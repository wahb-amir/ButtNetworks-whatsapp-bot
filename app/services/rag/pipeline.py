from __future__ import annotations

from typing import List

from app.services.rag.retriever import RetrievedChunk, retrieve_chunks


def format_context(chunks: List[RetrievedChunk]) -> str:
    if not chunks:
        return ""

    parts = []
    for i, chunk in enumerate(chunks, start=1):
        section = ""
        if chunk.metadata and chunk.metadata.get("section"):
            section = f" | Section: {chunk.metadata['section']}"

        parts.append(
            f"[Chunk {i}{section} | Source: {chunk.source} | Score: {chunk.similarity:.4f}]\n"
            f"{chunk.content}"
        )

    return "\n\n---\n\n".join(parts)


def retrieve_for_query(query: str, top_k: int = 5, min_similarity: float = 0.65):
    chunks = retrieve_chunks(
    query=query,
    top_k=top_k,
    min_similarity=min_similarity,
)

    return {
        "query": query,
        "chunks": chunks,
        "context": format_context(chunks),
    }