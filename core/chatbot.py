# ============================================================
# core/chatbot.py
# Main Chatbot Class (Terintegrasi Modular)
# ============================================================

import time
import traceback
import redis
from typing import Tuple, List
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import Document

# Local imports
from retrieval.vector_store import FAISSIndexBuilder
from utils.helpers import load_products_from_db, build_product_documents

from metrics import MetricsTracker
from retrieval.retriever import RetrieverFactory
from retrieval.qa_chain import QAChainBuilder
from query.classifier import classify_query
from query.ultra_validator import UltraValidator
from query.confidence import calculate_confidence
from query.exact_matcher import ExactMatcher
from .llm_manager import initialize_gemini

# Config & Constants
from .config import (
    GEMINI_MODEL,
    GEMINI_API_KEY,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    FAISS_INDEX_PATH,
    AUTO_REFRESH_ENABLED,
    REFRESH_INTERVAL_MINUTES,
    RETRIEVAL_TOP_K,
    METRICS_ENABLED,
    METRICS_FILE,
    SHOW_RETRIEVED_DOCS,
    SHOW_CONFIDENCE_SCORE,
    VERBOSE_MODE
)

class SessionMemory:
    """Manajemen Memori Chat Menggunakan Redis (atau Dictionary sebagai fallback)"""
    def __init__(self):
        self.use_redis = False
        self.redis_client = None
        self.fallback_dict = {}
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            if self.redis_client.ping():
                self.use_redis = True
                print("[MEMORY] Redis terhubung untuk Chat History")
        except Exception:
            print("[MEMORY] Redis tidak tersedia, menggunakan In-Memory Dict sebagai fallback")

    def get_history_string(self, session_id: str, limit: int = 4) -> str:
        """Mengambil 4 pasang chat terakhir untuk konteks"""
        if not session_id:
            return "Tidak ada riwayat sebelumnya."
        
        key = f"chat_mem:{session_id}"
        if self.use_redis:
            msgs = self.redis_client.lrange(key, -(limit*2), -1)
            return "\n".join(msgs) if msgs else "Tidak ada riwayat sebelumnya."
        else:
            msgs = self.fallback_dict.get(key, [])
            return "\n".join(msgs[-(limit*2):]) if msgs else "Tidak ada riwayat sebelumnya."

    def save_interaction(self, session_id: str, question: str, answer: str):
        """Menyimpan interaksi User dan AI ke dalam memori"""
        if not session_id:
            return
        
        key = f"chat_mem:{session_id}"
        q_str = f"Customer: {question}"
        a_str = f"CS GA Toys: {answer}"
        
        if self.use_redis:
            self.redis_client.rpush(key, q_str, a_str)
            self.redis_client.ltrim(key, -10, -1) # Simpan maksimal 10 baris terakhir agar tidak kepenuhan
            self.redis_client.expire(key, 86400)  # Kadaluarsa dalam 24 Jam
        else:
            if key not in self.fallback_dict:
                self.fallback_dict[key] =[]
            self.fallback_dict[key].extend([q_str, a_str])
            self.fallback_dict[key] = self.fallback_dict[key][-10:]
            
class ToysShopChatbot:
    """Main Customer Service Chatbot untuk GA Toys"""

    def __init__(self):
        print("[DEBUG] ToysShopChatbot.__init__ started...")
        self.llm = None
        self.retriever_factory = RetrieverFactory()
        self.qa_chain = QAChainBuilder()
        self.metrics = MetricsTracker(METRICS_ENABLED, METRICS_FILE)
        self.products_cache = []
        self.index_builder =  FAISSIndexBuilder()
        print("[DEBUG] Creating UltraValidator...")
        self.validator = UltraValidator(enable_semantic=False, strict_mode=False)
        print(f"[DEBUG] Validator created: type={type(self.validator)}, has_method={hasattr(self.validator, 'is_in_context')}")
        
        # Exact matcher untuk SKU/brand search (will be initialized after loading products)
        self.exact_matcher = None
        self.memory = SessionMemory()

                
    def create_qa_chain(self):
        """
        Buat ulang QA chain menggunakan retriever & LLM yang aktif.
        Biasanya dipanggil setelah FAISS index dibangun ulang.
        """
        try:
            print("[QA_CHAIN] Membangun QA chain baru...")

            # IMPORTANT: Get retriever dari index_builder yang sudah di-update
            # Pastikan index_builder.vectorstore sudah pointing ke data terbaru
            retriever = self.index_builder.get_retriever(k=5)

            if not retriever:
                print("[ERROR] Retriever gagal dibuat. Periksa FAISS index.")
                return

            # Buat LLM (kalau belum)
            if not self.llm:
                self.llm = initialize_gemini()

            # Bangun QA Chain dengan builder terpisah
            self.qa_chain = QAChainBuilder.create_chain(self.llm, retriever)

            if self.qa_chain:
                print("[SUCCESS] QA chain berhasil dibuat dan siap digunakan")
            else:
                print("[ERROR] QA chain gagal dibuat (hasil None)")

        except Exception as e:
            print(f"[ERROR] Gagal membuat QA chain: {e}")

    
    def initialize(self):
        """Initialize semua komponen chatbot"""
        print("=" * 70)
        print("  🎮 GA TOYS - CUSTOMER SERVICE CHATBOT (Pure RAG)")
        print("  📚 Skripsi: RAG + Embedding Implementation")
        print("  🤖 Powered by Google Gemini & Supabase")
        print("=" * 70)

        # 1. Init LLM
        print("\n[STEP 1/4] Initializing LLM (Google Gemini)...")
        try:
            self.llm = initialize_gemini()
            test = self.llm.invoke("test")
            print(f"[SUCCESS] Gemini LLM initialized: {GEMINI_MODEL}")
        except Exception as e:
            print(f"[FATAL] Gemini initialization failed: {e}")
            return False

        # 2. Load product data
        print("\n[STEP 2/4] Loading product data from Supabase...")
        self.products_cache = load_products_from_db()
        if not self.products_cache:
            print("[FATAL] No products loaded from database")
            return False
        
        # Initialize exact matcher dengan products cache
        print("\n[STEP 2.5/4] Initializing exact matcher for SKU/brand search...")
        self.exact_matcher = ExactMatcher(self.products_cache)
        print(f"[SUCCESS] Exact matcher ready with {len(self.products_cache)} products")

        # 3. Build/Load FAISS index via RetrieverFactory
        print("\n[STEP 3/4] Preparing FAISS vector index...")
        self.retriever_factory = RetrieverFactory()

        # Coba load, kalau belum ada, build baru
        docs = build_product_documents(self.products_cache)
        retriever = self.retriever_factory.load_or_build(docs)
        if not retriever:
            print("[FATAL] Failed to setup retriever")
            return False

        # 4. Create QA Chain
        print("\n[STEP 4/4] Creating RetrievalQA chain...")
        self.qa_chain = QAChainBuilder.create_chain(self.llm, retriever)
        if not self.qa_chain:
            print("[FATAL] Failed to create QA chain")
            return False

        print("\n" + "=" * 70)
        print("  ✅ CHATBOT READY!")
        print("=" * 70)
        return True

    def refresh_index_if_needed(self):
        """Auto-refresh FAISS index jika interval sudah lewat"""
        if not AUTO_REFRESH_ENABLED:
            return

        index_builder = self.retriever_factory.index_builder
        if index_builder.needs_refresh(REFRESH_INTERVAL_MINUTES):
            print("\n[AUTO-REFRESH] Rebuilding index...")

            self.products_cache = load_products_from_db()
            docs = build_product_documents(self.products_cache)
            retriever = self.retriever_factory.refresh(docs)

            # recreate QA chain
            self.qa_chain = QAChainBuilder.create_chain(self.llm, retriever)
            print("[AUTO-REFRESH] Index refreshed successfully")
            
    def update_components(self, new_qa_chain, new_index_builder, new_products):
        """
        Thread-safe Hot Swap: Mengganti komponen chatbot secara atomic.
        Tidak perlu lock saat query karena pointer assignment di Python atomic.
        """
        print("[HOT-SWAP] Updating chatbot components...")
        self.qa_chain = new_qa_chain
        self.index_builder = new_index_builder
        self.products_cache = new_products
        
        # Update exact matcher dengan data baru
        if self.exact_matcher:
            self.exact_matcher.update_products(new_products)
            
        print("[HOT-SWAP] Components updated successfully!")


    def answer_question(self, question: str, session_id: str = None):
        """Jawab pertanyaan user dengan validasi context + RAG + Memory"""
        start_time = time.time()
        current_qa_chain = self.qa_chain
        query_type = "general" 

        # Ambil riwayat chat berdasarkan session_id
        chat_history_str = self.memory.get_history_string(session_id)

        # Fungsi bantuan agar kita langsung menyimpan memori sebelum return
        def finalize_response(ans, conf, srcs, qtype):
            self.memory.save_interaction(session_id, question, ans)
            return ans, conf, srcs, qtype

        try:
            is_valid, reason, validation_confidence = self.validator.is_in_context(question)
            
            if not is_valid:
                rejection = self.validator.get_rejection_message(reason, question)
                response_time = time.time() - start_time
                self.metrics.log_query(question=question, answer=rejection, response_time=response_time, query_type="out_of_context", sources=[])
                return finalize_response(rejection, 0.0,[], "out_of_context")

            query_type = classify_query(question) 

            # EXACT MATCH PRE-FILTER
            exact_match = None
            if self.exact_matcher:
                exact_match = self.exact_matcher.match(question)
            
            # BIKIN CONTEXTUAL QUERY: Gabung history dan pertanyaan
            # Ini membuat AI (dan pencarian FAISS) mengerti konteks sebelumnya
            contextual_query = f"Riwayat Percakapan Terakhir:\n{chat_history_str}\n\nPertanyaan Baru: {question}"

            if exact_match:
                match_type, matched_products = exact_match
                if len(matched_products) == 0:
                    answer = "Maaf, produk atau SKU yang Anda cari tidak tersedia di katalog kami saat ini. 😊"
                    response_time = time.time() - start_time
                    self.metrics.log_query(question=question, answer=answer, response_time=response_time, query_type=query_type, sources=[])
                    return finalize_response(answer, 0.5,[], query_type)
                else:
                    from langchain.schema import Document
                    matched_docs =[]
                    for prod in matched_products[:10]:
                        price_idr = f"Rp {prod['price']:,}".replace(',', '.')
                        content = f"=== {prod['name']} ===\nSKU: {prod['sku']}\nHarga: {price_idr}\nKategori: {prod.get('category_name', 'N/A')}\nDESKRIPSI:\n{prod.get('description', 'Tidak ada')}"
                        matched_docs.append(Document(page_content=content, metadata={"type": "product", "name": prod['name'], "price": prod['price']}))
                    
                    # === INJEKSI CHAT HISTORY KE EXACT MATCH ===
                    # Cukup kirimkan 'query' saja!
                    result = current_qa_chain.invoke({
                        "query": contextual_query 
                    })                    
                    answer = result.get("result", "") if isinstance(result, dict) else str(result)
                    confidence = calculate_confidence(answer, matched_docs, question)
                    response_time = time.time() - start_time
                    self.metrics.log_query(question=question, answer=answer, response_time=response_time, query_type=query_type, sources=matched_docs)
                    return finalize_response(answer, confidence, matched_docs, query_type)
            
            # FALLBACK: Regular Vector Search
            try:
                # === INJEKSI CHAT HISTORY KE VECTOR SEARCH ===
                # Cukup kirimkan 'query' saja!
                result = self.qa_chain.invoke({
                    "query": contextual_query
                })

                answer = result.get("result", "") if isinstance(result, dict) else str(result)
                sources = result.get("source_documents",[])

                confidence = calculate_confidence(answer, sources, question)
                response_time = time.time() - start_time
                self.metrics.log_query(question=question, answer=answer, response_time=response_time, query_type=query_type, sources=sources)
                
                return finalize_response(answer, confidence, sources, query_type)

            except Exception as e:
                print(f"\n[FATAL ERROR SAAT INFERENSI LLM] Detail: {str(e)}")
                import traceback
                traceback.print_exc()

                error_msg = "Maaf, terjadi error internal sistem. Silakan coba lagi atau hubungi admin."
                return finalize_response(error_msg, 0.0,[], query_type)
        
        finally:
            pass
        

    def format_answer_display(self, question, answer, confidence, sources, query_type):
        """Cetak jawaban ke terminal (mode CLI)"""
        print("\n" + "=" * 70)
        print("💬 PERTANYAAN:")
        print(f"   {question}")
        print("\n" + "-" * 70)

        if query_type == "out_of_context":
            print("\n⚠️  PERTANYAAN DI LUAR KONTEKS")
            print(answer)
            print("=" * 70)
            return

        if SHOW_CONFIDENCE_SCORE:
            emoji = "🟢" if confidence >= 0.7 else "🟡" if confidence >= 0.5 else "🔴"
            print(f"\n{emoji} JAWABAN (Confidence: {confidence:.2f} | Type: {query_type}):")
        else:
            print("\n✅ JAWABAN:")

        print(answer)

        if SHOW_RETRIEVED_DOCS and sources:
            print("\n" + "-" * 70)
            print(f"📚 SUMBER INFORMASI ({len(sources)} dokumen):")
            for i, doc in enumerate(sources[:RETRIEVAL_TOP_K], 1):
                doc_type = doc.metadata.get('type', 'unknown')
                if doc_type == 'product':
                    name = doc.metadata.get('name', 'N/A')
                    price = doc.metadata.get('price', 0)
                    print(f"   {i}. [Produk] {name} - Rp {price:,}".replace(',', '.'))
                else:
                    title = doc.metadata.get('title', 'Store Info')
                    print(f"   {i}. [Info] {title}")

        print("=" * 70)

    def run_interactive(self):
        """Mode CLI untuk testing interaktif"""
        print("\n" + "=" * 70)
        print("  💬 CHAT MODE - CS Bot GA Toys")
        print("=" * 70)
        print("\n📝 Tips Pertanyaan:")
        print("  • 'Ada mainan Molly?'")
        print("  • 'Berapa harga Tokidoki Cactus Buddy?'")
        print("  • 'Rekomendasi mainan untuk umur 15 tahun?'")
        print("  • 'Bagaimana cara membeli?'")
        print("  • 'Apa itu blind box?'")
        print("\n⌨️  Ketik 'exit', 'quit', atau 'keluar' untuk berhenti")
        print("⌨️  Ketik 'metrics' untuk lihat statistik performa")
        print("⌨️  Ketik 'refresh' untuk rebuild index manual\n")

        while True:
            try:
                question = input("\n🧑 Anda: ").strip()
                if not question:
                    continue

                if question.lower() in ['exit', 'quit', 'keluar']:
                    print("\n👋 Terima kasih sudah menggunakan GA Toys Chatbot!")
                    break

                if question.lower() == 'metrics':
                    print(self.metrics.get_summary())
                    continue

                if question.lower() == 'refresh':
                    print("\n[MANUAL REFRESH] Rebuilding index...")
                    self.products_cache = load_products_from_db()
                    docs = build_product_documents(self.products_cache)
                    retriever = self.retriever_factory.refresh(docs)
                    self.qa_chain = QAChainBuilder.create_chain(self.llm, retriever)
                    print("[SUCCESS] Index refreshed manually")
                    continue

                answer, confidence, sources, qtype = self.answer_question(question)
                self.format_answer_display(question, answer, confidence, sources, qtype)

            except KeyboardInterrupt:
                print("\n\n👋 Chatbot dihentikan oleh user.")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                if VERBOSE_MODE:
                    traceback.print_exc()

        print("\n[SAVING] Menyimpan metrics...")
        self.metrics.end_session()
        print(f"[SUCCESS] Metrics disimpan ke {METRICS_FILE}")
        print("\n" + "=" * 70)
        print("  📊 SESSION SUMMARY")
        print("=" * 70)
        print(self.metrics.get_summary())


# Global instance untuk CLI mode (jangan dipakai di API!)
# API menggunakan singleton di api/__init__.py
if __name__ == "__main__":
    chatbot = ToysShopChatbot()
else:
    chatbot = None  # Prevent auto-instantiation saat di-import
