from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.repositories.knowledge_repository import search_chunks
from app.services.llm.groq_client import get_llm


def build_context(query: str) -> str:
    chunks = search_chunks(query, top_k=settings.rag_top_k)
    if not chunks:
        return ""

    lines = []
    for i, chunk in enumerate(chunks, start=1):
        lines.append(f"[{i}] {chunk['content']}")
    return "\n\n".join(lines)


def answer_with_rag(user_text: str, chat_history: list[dict] | None = None) -> tuple[str, list[dict]]:
    context = build_context(user_text)
    llm = get_llm()

    system_prompt = f"""
You are a helpful WhatsApp assistant.

Use the retrieved context when it is relevant.
If the context does not contain the answer, say you do not know.

Retrieved context:
{context if context else "No relevant knowledge found."}
""".strip()

    messages = [SystemMessage(content=system_prompt)]

    if chat_history:
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                # keep short history only
                messages.append(SystemMessage(content=f"Previous assistant reply: {msg['content']}"))

    messages.append(HumanMessage(content=user_text))
    response = llm.invoke(messages)

    return response.content, search_chunks(user_text, top_k=settings.rag_top_k)