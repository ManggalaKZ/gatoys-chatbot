# ============================================================
# retrieval/retriever.py
# Retriever Factory
# ============================================================

from typing import Optional
from langchain_core.vectorstores import VectorStoreRetriever

from retrieval.vector_store import FAISSIndexBuilder
from core.config import (
    EMBEDDING_MODEL,
    FAISS_INDEX_PATH,
    RETRIEVAL_TOP_K
)


class RetrieverFactory:
    """
    Factory untuk membuat retriever dari FAISSIndexBuilder.
    Dipisah agar modular dan mudah di-maintain.
    """

    def __init__(self):
        self.index_builder = FAISSIndexBuilder(
            embedding_model_name=EMBEDDING_MODEL,
            index_path=FAISS_INDEX_PATH
        )

    def load_or_build(self, docs=None) -> Optional[VectorStoreRetriever]:
        """
        Muat index kalau sudah ada, jika belum maka build dari docs (wajib dikirim).
        """
        if self.index_builder.load_index():
            print("[INFO] Retriever menggunakan FAISS index yang sudah ada")
        else:
            if not docs:
                print("[FATAL] Tidak ada dokumen untuk membangun index!")
                return None
            print("[INFO] Index tidak ditemukan, membangun FAISS index baru...")
            if not self.index_builder.build_from_documents(docs):
                print("[ERROR] Gagal membangun index baru")
                return None

        return self.index_builder.get_retriever(k=RETRIEVAL_TOP_K)

    def get_retriever(self, k: int = RETRIEVAL_TOP_K):
        """Ambil retriever langsung jika index sudah siap."""
        return self.index_builder.get_retriever(k=k)

    def refresh(self, docs):
        """
        Rebuild index secara manual (misal saat auto-refresh).
        """
        print("[AUTO-REFRESH] Membangun ulang FAISS index...")
        self.index_builder.build_from_documents(docs)
        print("[AUTO-REFRESH] Index berhasil diperbarui")
        return self.get_retriever()
