from __future__ import annotations

import argparse
import hashlib
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from app.db.supabase_client import supabase
from app.services.embeddings.local_embeddings import embed_text


DEFAULT_FILE_PATH = "scripts/deep-research-report.md"
DEFAULT_TABLE_NAME = "knowledge_chunks"
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150
DEFAULT_BATCH_SIZE = 20
DEFAULT_MIN_CHUNK_CHARS = 80
DEFAULT_EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))
DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def content_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def safe_section_path(section_stack: Sequence[str]) -> str:
    cleaned = [s.strip() for s in section_stack if s.strip()]
    return " / ".join(cleaned) if cleaned else "root"


def extract_blocks(text: str) -> List[Dict[str, str]]:
    """
    Turns a markdown document into blocks while preserving heading context.
    Each block is a paragraph/list block associated with the latest heading path.
    """
    blocks: List[Dict[str, str]] = []
    section_stack: List[str] = []
    paragraph_lines: List[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if not paragraph_lines:
            return

        block_text = "\n".join(paragraph_lines).strip()
        paragraph_lines = []

        if block_text:
            blocks.append(
                {
                    "text": block_text,
                    "section": safe_section_path(section_stack),
                }
            )

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        heading_match = HEADING_RE.match(line.strip())

        if heading_match:
            flush_paragraph()

            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            while len(section_stack) >= level:
                section_stack.pop()

            section_stack.append(heading_text)
            continue

        if not line.strip():
            flush_paragraph()
            continue

        paragraph_lines.append(line)

    flush_paragraph()
    return blocks


def split_long_block(text: str, max_chars: int) -> List[str]:
    """
    Split a long block into smaller parts without chopping blindly.
    Tries sentence boundaries first, then falls back to line boundaries,
    then hard slices if needed.
    """
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) == 1:
        sentences = [line.strip() for line in text.splitlines() if line.strip()]

    parts: List[str] = []
    current = ""

    for piece in sentences:
        piece = piece.strip()
        if not piece:
            continue

        candidate = f"{current} {piece}".strip() if current else piece

        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            parts.append(current.strip())
            current = ""

        if len(piece) <= max_chars:
            current = piece
        else:
            # Hard slice as last resort.
            for i in range(0, len(piece), max_chars):
                chunk = piece[i : i + max_chars].strip()
                if chunk:
                    parts.append(chunk)

    if current.strip():
        parts.append(current.strip())

    return parts


def build_units(blocks: List[Dict[str, str]], max_chars: int) -> List[Dict[str, str]]:
    units: List[Dict[str, str]] = []

    for block in blocks:
        text = block["text"].strip()
        section = block["section"].strip()

        if not text:
            continue

        if len(text) <= max_chars:
            units.append({"text": text, "section": section})
            continue

        for part in split_long_block(text, max_chars=max_chars):
            cleaned = part.strip()
            if cleaned:
                units.append({"text": cleaned, "section": section})

    return units


def take_overlap(units: List[Dict[str, str]], overlap_chars: int) -> List[Dict[str, str]]:
    """
    Keep a small tail of the previous chunk so the next chunk has context.
    Avoid overlap when there is only one unit; that prevents infinite repetition.
    """
    if len(units) <= 1 or overlap_chars <= 0:
        return []

    tail: List[Dict[str, str]] = []
    total = 0

    for unit in reversed(units):
        unit_len = len(unit["text"])
        if tail and total + unit_len > overlap_chars:
            break

        tail.append(unit)
        total += unit_len

        if total >= overlap_chars:
            break

    tail.reverse()
    if len(tail) >= len(units):
        return []
    return tail


def build_chunks(
    units: List[Dict[str, str]],
    max_chars: int,
    overlap_chars: int,
) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    current_units: List[Dict[str, str]] = []
    current_len = 0

    for unit in units:
        unit_text = unit["text"].strip()
        unit_len = len(unit_text)

        if not unit_text:
            continue

        separator_cost = 2 if current_units else 0
        would_overflow = current_units and (current_len + separator_cost + unit_len > max_chars)

        if would_overflow:
            chunk_text = "\n\n".join(u["text"] for u in current_units).strip()
            if chunk_text:
                chunks.append(
                    {
                        "text": chunk_text,
                        "section": current_units[0]["section"] if current_units else "root",
                    }
                )

            current_units = take_overlap(current_units, overlap_chars=overlap_chars)
            current_len = len("\n\n".join(u["text"] for u in current_units).strip()) if current_units else 0

        current_units.append(unit)
        current_len += unit_len + (2 if len(current_units) > 1 else 0)

    if current_units:
        chunk_text = "\n\n".join(u["text"] for u in current_units).strip()
        if chunk_text:
            chunks.append(
                {
                    "text": chunk_text,
                    "section": current_units[0]["section"] if current_units else "root",
                }
            )

    return chunks


def make_embedding(text: str) -> List[float]:
    embedding = embed_text(text)

    if hasattr(embedding, "tolist"):
        embedding = embedding.tolist()

    embedding = list(embedding)

    if len(embedding) != DEFAULT_EMBEDDING_DIM:
        raise ValueError(
            f"Embedding dimension mismatch: expected {DEFAULT_EMBEDDING_DIM}, got {len(embedding)}"
        )

    return embedding


def insert_batch(rows: List[Dict[str, Any]], retries: int = 3) -> None:
    if not rows:
        return

    for attempt in range(1, retries + 1):
        try:
            supabase.table(DEFAULT_TABLE_NAME).insert(rows).execute()
            return
        except Exception as exc:
            if attempt == retries:
                raise
            wait = 1.5 * attempt
            print(f"⚠️ Batch insert failed (attempt {attempt}/{retries}): {exc}")
            print(f"Retrying in {wait:.1f}s...")
            time.sleep(wait)


def ingest(
    file_path: str,
    source_name: str | None,
    max_chars: int,
    overlap_chars: int,
    batch_size: int,
    min_chunk_chars: int,
) -> None:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    raw_text = path.read_text(encoding="utf-8", errors="ignore")
    text = normalize_text(raw_text)

    blocks = extract_blocks(text)
    units = build_units(blocks, max_chars=max_chars)
    chunks = build_chunks(units, max_chars=max_chars, overlap_chars=overlap_chars)

    source = source_name or path.name

    print(f"📄 File: {path}")
    print(f"🧩 Blocks: {len(blocks)}")
    print(f"📦 Chunks before filtering: {len(chunks)}")

    seen_hashes: set[str] = set()
    rows: List[Dict[str, Any]] = []

    for idx, chunk in enumerate(chunks):
        chunk_text = chunk["text"].strip()
        if len(chunk_text) < min_chunk_chars:
            continue

        h = content_hash(chunk_text)
        if h in seen_hashes:
            continue
        seen_hashes.add(h)

        embedding = make_embedding(chunk_text)

        row = {
            "source": source,
            "content": chunk_text,
            "embedding": embedding,
            "metadata": {
                "chunk_index": len(rows),
                "source_file": str(path),
                "source_name": source,
                "section": chunk["section"],
                "char_length": len(chunk_text),
                "content_hash": h,
                "embedding_model": DEFAULT_EMBEDDING_MODEL,
                "embedding_dim": DEFAULT_EMBEDDING_DIM,
            },
        }
        rows.append(row)

    print(f"✅ Chunks after filtering/dedup: {len(rows)}")

    if not rows:
        print("Nothing to insert.")
        return

    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        insert_batch(batch)
        print(f"✅ Inserted {min(i + batch_size, len(rows))}/{len(rows)}")

    print("🚀 Ingestion complete!")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest markdown into Supabase pgvector.")
    parser.add_argument("--file", default=DEFAULT_FILE_PATH, help="Path to the markdown file.")
    parser.add_argument(
        "--source",
        default=None,
        help="Source name stored in the DB. Defaults to the file name.",
    )
    parser.add_argument("--max-chars", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--overlap-chars", type=int, default=DEFAULT_CHUNK_OVERLAP)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--min-chunk-chars", type=int, default=DEFAULT_MIN_CHUNK_CHARS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("Current working directory:", os.getcwd())
    print(f"Embedding model: {DEFAULT_EMBEDDING_MODEL}")
    print(f"Embedding dim: {DEFAULT_EMBEDDING_DIM}")

    ingest(
        file_path=args.file,
        source_name=args.source,
        max_chars=args.max_chars,
        overlap_chars=args.overlap_chars,
        batch_size=args.batch_size,
        min_chunk_chars=args.min_chunk_chars,
    )


if __name__ == "__main__":
    main()