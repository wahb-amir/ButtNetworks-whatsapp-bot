from functools import lru_cache

from fastembed import TextEmbedding


@lru_cache(maxsize=1)
def get_embedding_model():
    return TextEmbedding(model_name="BAAI/bge-small-en-v1.5")


def embed_text(text: str) -> list[float]:
    model = get_embedding_model()

    embeddings = list(model.embed([text]))

    return embeddings[0].tolist()