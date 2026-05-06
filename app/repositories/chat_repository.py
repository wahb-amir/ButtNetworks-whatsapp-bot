from app.db.client import get_conn


def get_or_create_conversation(whatsapp_user_id: str) -> dict:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into conversations (whatsapp_user_id)
            values (%s)
            on conflict (whatsapp_user_id)
            do update set updated_at = now()
            returning id, whatsapp_user_id, created_at, updated_at
            """,
            (whatsapp_user_id,),
        )
        return cur.fetchone()


def save_message(
    conversation_id: str,
    role: str,
    content: str,
    wa_message_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    metadata = metadata or {}
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into chat_messages (conversation_id, role, content, wa_message_id, metadata)
            values (%s, %s, %s, %s, %s::jsonb)
            """,
            (conversation_id, role, content, wa_message_id, __import__("json").dumps(metadata)),
        )
        conn.commit()


def get_recent_messages(conversation_id: str, limit: int = 8) -> list[dict]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select role, content, created_at
            from chat_messages
            where conversation_id = %s
            order by created_at desc
            limit %s
            """,
            (conversation_id, limit),
        )
        rows = cur.fetchall()
        return list(reversed(rows))