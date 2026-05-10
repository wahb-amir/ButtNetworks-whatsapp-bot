from __future__ import annotations

from app.db.supabase_client import supabase


def get_or_create_conversation(whatsapp_user_id: str) -> dict:
    existing = (
        supabase.table("conversations")
        .select("id, whatsapp_user_id, created_at, updated_at")
        .eq("whatsapp_user_id", whatsapp_user_id)
        .limit(1)
        .execute()
    )

    rows = existing.data or []
    if rows:
        return rows[0]

    created = (
        supabase.table("conversations")
        .insert({"whatsapp_user_id": whatsapp_user_id})
        .execute()
    )

    return (created.data or [])[0]


def save_message(
    conversation_id: str,
    role: str,
    content: str,
    wa_message_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    supabase.table("chat_messages").insert(
        {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "wa_message_id": wa_message_id,
            "metadata": metadata or {},
        }
    ).execute()


def get_recent_messages(conversation_id: str, limit: int = 8) -> list[dict]:
    response = (
        supabase.table("chat_messages")
        .select("role, content, created_at")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    rows = response.data or []
    return list(reversed(rows))