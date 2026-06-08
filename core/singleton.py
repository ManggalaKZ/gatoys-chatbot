from langchain_community.embeddings import SentenceTransformerEmbeddings
from core.config import EMBEDDING_MODEL

_embedding_instance = None

def get_embedding_model():
    global _embedding_instance
    if _embedding_instance is None:
        print(f"[INIT] Loading Shared Embedding Model: {EMBEDDING_MODEL}")
        _embedding_instance = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
    return _embedding_instance