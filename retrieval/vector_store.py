# ============================================================
# retrieval/vector_store.py
# FAISS Index Builder & Persistence
# ============================================================

import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import List
from zoneinfo import ZoneInfo

from langchain_community.vectorstores.faiss import FAISS
from langchain_core.documents import Document
from core.singleton import get_embedding_model


# Import konfigurasi & embeddings
from core.config import (
    EMBEDDING_MODEL_TYPE,
    EMBEDDING_MODEL,
    FAISS_INDEX_PATH,
    FAISS_SAVE_ENABLED,
    BGE_USE_FP16
)



class FAISSIndexBuilder:
    """Manage FAISS index building & persistence"""

    def __init__(self, embedding_model_name: str = EMBEDDING_MODEL, index_path: str = FAISS_INDEX_PATH):
        self.embedding_model_name = embedding_model_name
        self.index_path = index_path
        self.embeddings = None
        self.vectorstore = None
        self.last_build_time = None

        self._init_embeddings()

    def _init_embeddings(self):
        """Initialize embeddings based on model type"""
        try:
            self.embeddings = get_embedding_model()
        except Exception as e:
            print(f"[ERROR] Failed to initialize embeddings: {e}")
            raise

    def build_from_documents(self, docs: List[Document]) -> bool:
        """Build FAISS index from documents"""
        try:
            print(f"\n[STEP] Building FAISS index from {len(docs)} documents...")
            print(f"[MODEL] Using: {self.embedding_model_name}")

            start_time = time.time()

            print(f"[PROGRESS] Encoding {len(docs)} documents...")
            self.vectorstore = FAISS.from_documents(docs, self.embeddings)
            self.last_build_time = datetime.now(ZoneInfo("Asia/Jakarta"))

            elapsed = time.time() - start_time
            print(f"[SUCCESS] FAISS index built in {elapsed:.2f}s")
            print(f"[INFO] Index size: {len(docs)} documents")

            if FAISS_SAVE_ENABLED:
                self.save_index()

            return True

        except Exception as e:
            print(f"[ERROR] Failed to build FAISS index: {e}")
            traceback.print_exc()
            return False

    def save_index(self):
        """Save FAISS index to disk"""
        try:
            if self.vectorstore:
                self.vectorstore.save_local(self.index_path)
                print(f"[SUCCESS] FAISS index saved to {self.index_path}")
        except Exception as e:
            print(f"[WARN] Could not save FAISS index: {e}")

    def load_index(self) -> bool:
        """Load FAISS index from disk"""
        try:
            if Path(self.index_path).exists():
                print(f"\n[STEP] Loading existing FAISS index from {self.index_path}...")

                self.vectorstore = FAISS.load_local(
                    self.index_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                self.last_build_time = datetime.now(ZoneInfo("Asia/Jakarta"))

                print("[SUCCESS] FAISS index loaded from disk")
                return True

        except Exception as e:
            print(f"[WARN] Could not load existing index: {e}")
            traceback.print_exc()

        return False

    def get_retriever(self, k: int = 4):
        """Get retriever from vectorstore"""
        if self.vectorstore:
            return self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": k}
            )
        return None

    def needs_refresh(self, interval_minutes: int) -> bool:
        """Check if index needs refresh"""
        if not self.last_build_time:
            return True
        dateNow = datetime.now(ZoneInfo("Asia/Jakarta"))
        elapsed = (dateNow - self.last_build_time).total_seconds() / 60
        return elapsed >= interval_minutes
