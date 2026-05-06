from pathlib import Path

# from app.db.supabase_client import supabase
# from app.services.embeddings.local_embeddings import embed_text
import os
print("Current working directory:", os.getcwd())

from app.db.supabase_client import supabase
from app.services.embeddings.local_embeddings import embed_text

FILE_PATH = "scripts/deep-research-report.md"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def chunk_text(text: str):
    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def ingest():
    file_text = Path(FILE_PATH).read_text(encoding="utf-8", errors="ignore")

    chunks = chunk_text(file_text)

    print(f"📦 Total chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks):
        embedding = embed_text(chunk)

        res = supabase.table("knowledge_chunks").insert({
            "source": "README.md",
            "content": chunk,
            "embedding": embedding,
            "metadata": {
                "chunk_index": i
            }
        }).execute()

        print(f"✅ Inserted chunk {i + 1}/{len(chunks)}")

    print("🚀 Ingestion complete!")


if __name__ == "__main__":
    ingest()