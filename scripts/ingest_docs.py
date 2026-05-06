from pathlib import Path

from app.repositories.knowledge_repository import add_chunk

RAW_DIR = Path("data/raw")
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += size - overlap
    return chunks


def main():
    for file_path in RAW_DIR.glob("*"):
        if file_path.suffix.lower() not in {".txt", ".md"}:
            continue

        content = file_path.read_text(encoding="utf-8", errors="ignore")
        chunks = chunk_text(content)

        for i, chunk in enumerate(chunks):
            add_chunk(
                source=file_path.name,
                chunk_index=i,
                content=chunk,
                metadata={"path": str(file_path)},
            )

        print(f"Ingested {file_path.name}: {len(chunks)} chunks")


if __name__ == "__main__":
    main()