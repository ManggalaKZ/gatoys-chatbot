# ============================================================
# retrieval/qa_chain.py
# RetrievalQA Chain Builder
# ============================================================

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from core.config import (
    RETRIEVAL_TOP_K
)


class QAChainBuilder:
    """
    Builder untuk membuat RetrievalQA chain
    agar tidak tercampur di dalam class Chatbot.
    """

    @staticmethod
    def create_chain(llm, retriever):
        """
        Buat RetrievalQA dengan custom prompt.
        """
        if not retriever:
            print("[ERROR] Retriever tidak tersedia, QA Chain gagal dibuat.")
            return None

        cs_prompt = PromptTemplate(
            template="""
Kamu adalah customer service assistant untuk GA Toys, toko online mainan koleksi figurine import.

Tugasmu:
- Jawab pertanyaan customer dengan ramah dan informatif
- Berikan informasi produk yang akurat berdasarkan Context
- Gunakan Riwayat Percakapan untuk memahami konteks jika pertanyaan merujuk pada hal sebelumnya (misal: "kalau yang merah?", "harganya berapa?", dll).
- Selalu professional dan helpful

Context (informasi produk & toko):
{context}

Pertanyaan Customer: {question}

Jawaban (Bahasa Indonesia, ramah, dan lengkap):
""",
            input_variables=["context", "question"] 
        )

        try:
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": cs_prompt}
            )
            print("[SUCCESS] QA Chain berhasil dibuat")
            return qa_chain

        except Exception as e:
            print(f"[ERROR] Gagal membuat QA Chain: {e}")
            return None
