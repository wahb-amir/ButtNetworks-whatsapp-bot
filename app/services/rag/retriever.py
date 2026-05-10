from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from app.db.supabase_client import supabase
from app.services.embeddings.local_embeddings import embed_text


EMBEDDING_DIM = 384
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@dataclass
class RetrievedChunk:
    id: str
    source: str | None
    content: str
    metadata: Dict[str, Any] | None
    similarity: float


def _normalize_query(query: str) -> str:
    query = query.strip()
    if not query:
        raise ValueError("Query cannot be empty")
    return f"{QUERY_PREFIX}{query}"

def retrieve_chunks(
    query: str,
    top_k: int = 5,
    min_similarity: float = 0.65,
) -> List[RetrievedChunk]:
    """
    Embed the user query and retrieve the most relevant chunks from Supabase.
    """
    normalized_query = _normalize_query(query)
    query_embedding = embed_text(normalized_query)

    if hasattr(query_embedding, "tolist"):
        query_embedding = query_embedding.tolist()

    query_embedding = list(query_embedding)

    if len(query_embedding) != EMBEDDING_DIM:
        raise ValueError(
            f"Embedding dimension mismatch: expected {EMBEDDING_DIM}, got {len(query_embedding)}"
        )

    response = supabase.rpc(
        "match_knowledge_chunks",
        {
            "query_embedding": query_embedding,
            "match_count": top_k,
            "min_similarity": min_similarity,
        },
    ).execute()

    rows = response.data or []

    results: List[RetrievedChunk] = []
    for row in rows:
        results.append(
            RetrievedChunk(
                id=row["id"],
                source=row.get("source"),
                content=row["content"],
                metadata=row.get("metadata"),
                similarity=float(row["similarity"]),
            )
        )

    return results


def print_retrieval(query: str, top_k: int = 5, min_similarity: float = 0.65) -> None:
    """
    Small helper for debugging in terminal.
    """
    results = retrieve_chunks(
    query=query,
    top_k=top_k,
    min_similarity=min_similarity,
)

    print(f"\nQUERY: {query}\n")
    if not results:
        print("No chunks found.")
        return

    for i, item in enumerate(results, start=1):
        chunk_index = None
        if item.metadata and "chunk_index" in item.metadata:
            chunk_index = item.metadata["chunk_index"]

        print(f"RESULT {i}")
        print(f"  id: {item.id}")
        print(f"  source: {item.source}")
        print(f"  chunk_index: {chunk_index}")
        print(f"  similarity: {item.similarity:.4f}")
        print(f"  preview: {item.content[:300]}")
        print("-" * 80)


if __name__ == "__main__":
    print_retrieval("AI recycling app with leaderboard", match_count=5, min_similarity=0.65)