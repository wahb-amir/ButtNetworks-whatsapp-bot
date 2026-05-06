from app.db.client import get_conn
from app.services.embeddings.local_embeddings import embed_text


def add_chunk(source: str, chunk_index: int, content: str, metadata: dict | None = None) -> None:
    metadata = metadata or {}
    embedding = embed_text(content)

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into knowledge_chunks (source, chunk_index, content, embedding, metadata)
            values (%s, %s, %s, %s, %s::jsonb)
            """,
            (source, chunk_index, content, embedding, __import__("json").dumps(metadata)),
        )
        conn.commit()


def search_chunks(query: str, top_k: int = 4) -> list[dict]:
    query_embedding = embed_text(query)

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select
              source,
              chunk_index,
              content,
              metadata,
              1 - (embedding <=> %s::vector) as similarity
            from knowledge_chunks
            order by embedding <=> %s::vector
            limit %s
            """,
            (query_embedding, query_embedding, top_k),
        )
        return cur.fetchall()