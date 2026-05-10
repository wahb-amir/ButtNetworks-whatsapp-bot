from __future__ import annotations

from typing import Any

from app.db.supabase_client import supabase
from app.services.embeddings.local_embeddings import embed_text


def add_chunk(
    source: str,
    chunk_index: int,
    content: str,
    metadata: dict | None = None,
) -> None:
    metadata = metadata or {}
    metadata["chunk_index"] = chunk_index

    embedding = embed_text(content)
    if hasattr(embedding, "tolist"):
        embedding = embedding.tolist()

    supabase.table("knowledge_chunks").insert(
        {
            "source": source,
            "content": content,
            "embedding": embedding,
            "metadata": metadata,
        }
    ).execute()


def search_chunks(query: str, top_k: int = 4, min_similarity: float = 0.65) -> list[dict[str, Any]]:
    query_embedding = embed_text(query)
    if hasattr(query_embedding, "tolist"):
        query_embedding = query_embedding.tolist()

    response = supabase.rpc(
        "match_knowledge_chunks",
        {
            "query_embedding": query_embedding,
            "match_count": top_k,
            "min_similarity": min_similarity,
        },
    ).execute()

    return response.data or []