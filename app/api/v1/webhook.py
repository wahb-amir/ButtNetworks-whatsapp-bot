from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.repositories.chat_repository import (
    get_or_create_conversation,
    get_recent_messages,
    save_message,
)
from app.services.whatsapp.meta_client import send_whatsapp_text
from app.services.rag.pipeline import answer_with_rag
from app.services.whatsapp.parser import extract_inbound_messages

router = APIRouter()


@router.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        return PlainTextResponse(challenge or "", status_code=200)

    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/webhook")
async def whatsapp_webhook(payload: dict):
    inbound_messages = extract_inbound_messages(payload)

    for msg in inbound_messages:
        user_id = msg["from"]
        text = msg["text"].strip()

        if not text:
            continue

        conversation = get_or_create_conversation(user_id)
        save_message(
            conversation_id=str(conversation["id"]),
            role="user",
            content=text,
            wa_message_id=msg["wa_message_id"],
            metadata={"timestamp": msg.get("timestamp")},
        )

        history = get_recent_messages(str(conversation["id"]), limit=8)
        reply, _chunks = answer_with_rag(text, chat_history=history)

        save_message(
            conversation_id=str(conversation["id"]),
            role="assistant",
            content=reply,
        )

        await send_whatsapp_text(to=user_id, body=reply)

    return {"status": "ok"}