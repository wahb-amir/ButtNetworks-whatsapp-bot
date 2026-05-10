from fastapi import APIRouter, Form, Response
from twilio.twiml.messaging_response import MessagingResponse

# 1. Import your centralized settings
from app.core.config import settings

# Importing your existing logic
from app.repositories.chat_repository import (
    get_or_create_conversation,
    get_recent_messages,
    save_message,
)
from app.services.rag.pipeline import answer_with_rag

router = APIRouter()

@router.post("/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...), 
    Body: str = Form(...), 
    MessageSid: str = Form(...)
):
    """
    Handles incoming WhatsApp messages from Twilio using .env settings.
    """
    # Clean up the sender ID (Twilio sends 'whatsapp:+123456789')
    user_id = From.replace("whatsapp:", "")
    text = Body.strip()

    try:
        # 2. Manage Conversation State
        conversation = get_or_create_conversation(user_id)
        conversation_id = str(conversation["id"])

        # 3. Save User Message to DB
        save_message(
            conversation_id=conversation_id,
            role="user",
            content=text,
            wa_message_id=MessageSid,
        )

        # 4. Load Short-Term Memory (History)
        history = get_recent_messages(conversation_id, limit=8)

        # 5. Run RAG Pipeline
        # The pipeline already has access to settings.groq_api_key internally
        reply, chunks = answer_with_rag(
            query=text,
            chat_history=history,
        )

        # 6. Save Assistant Response to DB
        save_message(
            conversation_id=conversation_id,
            role="assistant",
            content=reply,
        )

        # 7. Generate TwiML Response
        # We use the configured twilio_whatsapp_number if needed, 
        # though Twilio usually handles the "From" automatically in the sandbox.
        twilio_resp = MessagingResponse()
        twilio_resp.message(reply)
        
        return Response(
            content=str(twilio_resp), 
            media_type="application/xml"
        )

    except Exception as e:
        # Log error using app_env from settings
        if settings.app_env == "dev":
            print(f"❌ [WEBHOOK ERROR] {e}")
            
        # Fallback TwiML error message
        error_resp = MessagingResponse()
        error_resp.message("I'm having trouble processing that right now. Please try again later.")
        return Response(
            content=str(error_resp), 
            media_type="application/xml"
        )