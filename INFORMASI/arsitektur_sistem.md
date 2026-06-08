# 🏗️ Arsitektur Sistem - GA Toys Chatbot

**Project:** Customer Service Chatbot dengan RAG (Pure Architecture)  
**Tech Stack:** FastAPI + LangChain + FAISS + Google Gemini + Supabase  
**Last Updated:** 9 November 2025

---

## 📐 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                            │
│                    (FastAPI Endpoint)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CONCURRENCY CONTROL                          │
│  • Semaphore (Max 3 concurrent)                                │
│  • Request tracking                                             │
│  • Queue management                                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CHATBOT MAIN PROCESSING                        │
│                   (ToysShopChatbot)                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
            ┌────────────┴───────────┐
            │                        │
            ▼                        ▼
   ┌────────────────┐      ┌────────────────┐
   │ REFRESH LOCK   │      │  VALIDATION    │
   │  Acquire?      │      │ (UltraValidator)│
   │  (Non-block)   │      │  8 Layers      │
   └───────┬────────┘      └────────┬────────┘
           │                        │
           │                        ▼
           │              ┌─────────────────┐
           │              │  Valid Context? │
           │              └────┬───────┬────┘
           │                   │       │
           │                 YES      NO
           │                   │       │
           │                   │       └─────► Rejection Message
           │                   │
           │                   ▼
           │          ┌──────────────────────┐
           │          │   EXACT MATCHER      │
           │          │  • SKU regex         │
           │          │  • Brand filter      │
           │          │  • Fuzzy match       │
           │          └──────┬───────────────┘
           │                 │
           │          ┌──────┴────────┐
           │          │               │
           │       MATCH?            NO
           │          │               │
           │         YES              │
           │          │               │
           │          ▼               ▼
           │  ┌──────────────┐  ┌──────────────┐
           │  │ Static       │  │ Vector       │
           │  │ Retriever    │  │ Search       │
           │  │ (Exact docs) │  │ (FAISS)      │
           │  └──────┬───────┘  └──────┬───────┘
           │         │                 │
           │         └────────┬────────┘
           │                  │
           │                  ▼
           │         ┌──────────────────┐
           │         │  Retrieved Docs  │
           │         │  (Top 5)         │
           │         └────────┬─────────┘
           │                  │
           │                  ▼
           │         ┌──────────────────┐
           │         │   LLM GENERATE   │
           │         │  (Gemini Flash)  │
           │         └────────┬─────────┘
           │                  │
           │                  ▼
           │         ┌──────────────────┐
           │         │  Answer + Meta   │
           │         │  • Confidence    │
           │         │  • Sources       │
           │         │  • Query type    │
           │         └────────┬─────────┘
           │                  │
           ▼                  ▼
   ┌────────────────┐  ┌──────────────────┐
   │ LOCK RELEASE   │  │  METRICS LOG     │
   │ (Finally)      │  │  • Response time │
   └────────────────┘  │  • Query type    │
                       │  • Success rate  │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  RESPONSE JSON   │
                       └──────────────────┘
```

---

## 🔄 Auto-Refresh Background Thread

```
SERVER STARTUP
      │
      ▼
┌──────────────────────────────────────┐
│  Start Background Thread (Daemon)    │
│  • Check interval: 300s              │
│  • Thread-safe lock                  │
└───────────────┬──────────────────────┘
                │
                │ (Every 5 minutes)
                ▼
        ┌───────────────┐
        │  POLL SUPABASE│
        │  MAX(updated_at)│
        └──────┬────────┘
               │
               ▼
        ┌──────────────┐
        │  Changed?    │
        └──┬────────┬──┘
           │        │
          YES       NO
           │        │
           │        └──► Continue polling
           │
           ▼
   ┌──────────────────┐
   │  ACQUIRE LOCK    │
   │  (Blocking)      │
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────┐
   │  REBUILD INDEX   │
   │  • Load products │
   │  • Build docs    │
   │  • FAISS rebuild │
   │  • Save to disk  │
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────┐
   │  RELOAD INDEX    │
   │  (Force reload)  │
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────┐
   │  RECREATE CHAIN  │
   │  • New retriever │
   │  • Same LLM      │
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────┐
   │  RELEASE LOCK    │
   └──────┬───────────┘
          │
          └─────► Continue polling
```

**Timing:**
- Poll interval: 300s (5 minutes)
- Rebuild time: 4-5s
- Downtime: 1.3% (4s / 300s)
- Impact: Minimal (non-blocking for users)

---

## 🎯 Validation Flow (UltraValidator)

```
USER QUESTION
      │
      ▼
┌─────────────────────────────────────┐
│ LAYER 1: Greeting Detection        │
│ Patterns: halo, hai, permisi, dll  │
└──────┬─────────────────────┬────────┘
       │                     │
     MATCH                NO MATCH
       │                     │
       ▼                     ▼
    ACCEPT          ┌──────────────────┐
                    │ LAYER 2: Intent  │
                    │ Classification   │
                    └──────┬────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
               PRODUCT       STORE_INFO
                    │             │
                    ▼             ▼
           ┌─────────────┐  ┌──────────────┐
           │ LAYER 3:    │  │ LAYER 4:     │
           │ Brand Check │  │ Store Check  │
           └──────┬──────┘  └──────┬───────┘
                  │                │
               FOUND            FOUND
                  │                │
                  └────────┬───────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ LAYER 5: Product│
                  │ Keywords Check  │
                  └──────┬──────────┘
                         │
                      FOUND
                         │
                         ▼
                  ┌─────────────────┐
                  │ LAYER 6: Proper │
                  │ Name Detection  │
                  └──────┬──────────┘
                         │
                      FOUND
                         │
                         ▼
                  ┌─────────────────┐
                  │ LAYER 7: Series │
                  │ Keywords Check  │
                  └──────┬──────────┘
                         │
                      FOUND
                         │
                         ▼
                  ┌─────────────────┐
                  │ LAYER 8: Minimal│
                  │ Length Check    │
                  └──────┬──────────┘
                         │
                    ┌────┴────┐
                    │         │
                  PASS       FAIL
                    │         │
                    ▼         ▼
                 ACCEPT    REJECT
```

**Rejection Reasons:**
- `too_short`: < 3 kata
- `no_keywords`: Tidak ada keyword relevan
- `off_topic`: Bukan tentang produk/toko
- `ambiguous`: Terlalu umum/ambigu

---

## 🔍 Hybrid Search Strategy

```
USER QUERY: "adakah sku BLB-001044?"
      │
      ▼
┌──────────────────────────┐
│  EXACT MATCHER           │
│  • SKU regex detect      │
└──────┬───────────────────┘
       │
    DETECTED: "BLB-001044"
       │
       ▼
┌──────────────────────────┐
│  DIRECT QUERY            │
│  products_cache.filter() │
│  WHERE sku = "BLB-001044"│
└──────┬───────────────────┘
       │
    ┌──┴───┐
    │      │
  FOUND   NOT FOUND
    │      │
    ▼      ▼
  RETURN  RETURN []
  [Product]
    │
    ▼
┌──────────────────────────┐
│  Convert to Documents    │
│  • Price format          │
│  • Description           │
│  • Metadata              │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  StaticRetriever         │
│  • Returns matched docs  │
│  • No vector search      │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  LLM Generate Answer     │
│  • 100% accurate sources │
│  • Zero hallucination    │
└──────────────────────────┘
```

**vs Traditional Vector Search:**
```
USER QUERY: "adakah sku BLB-001044?"
      │
      ▼
┌──────────────────────────┐
│  Embed Query             │
│  SentenceTransformer     │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  FAISS Similarity Search │
│  • Semantic similarity   │
│  • NOT exact match       │
└──────┬───────────────────┘
       │
       ▼
   RANDOM DOCS ❌
   (Hirono, Crybaby, etc)
       │
       ▼
   LLM Hallucinates ❌
```

---

## 💾 Data Flow

```
SUPABASE DATABASE
      │
      │ (Auto-trigger on UPDATE)
      ▼
┌──────────────────────────┐
│  updated_at = NOW()      │
│  (SQL Trigger)           │
└──────┬───────────────────┘
       │
       │ (5-min polling)
       ▼
┌──────────────────────────┐
│  Auto-Refresh Detect     │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  Load Products           │
│  • SQL JOIN              │
│  • products + details    │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  Build Documents         │
│  • Natural language      │
│  • FAQ-style format      │
│  • Rich metadata         │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  Embed Documents         │
│  • SentenceTransformer   │
│  • 384-dim vectors       │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  FAISS Index             │
│  • IndexFlatL2           │
│  • Save to disk          │
│  • index.faiss + pkl     │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  products_cache          │
│  • In-memory list        │
│  • For exact matching    │
└──────────────────────────┘
       │
       ▼
   READY FOR SEARCH ✅
```

---

## 🧠 LLM Prompt Engineering

**System Prompt:**
```
Kamu adalah customer service GA Toys, toko blind box & collectible figurines.

RULES:
1. Jawab dalam Bahasa Indonesia
2. Ramah, profesional, gunakan emoji
3. Jika tidak yakin, katakan "maaf tidak ada info"
4. Berikan informasi lengkap dari context
5. Format harga: Rp X.XXX.XXX
6. Sarankan produk serupa jika tersedia

TEMPLATE:
Halo! Terima kasih sudah menghubungi GA Toys.

[Jawaban berdasarkan context]

Apakah ada yang bisa saya bantu lagi? 😊
```

**Few-Shot Examples:**
```
Q: Berapa harga Molly Career Series?
A: Halo! Terima kasih sudah menghubungi GA Toys.

Molly Career Series dijual dengan harga Rp 145.000.

Produk ini merupakan blind box original dengan:
- Material: PVC
- Ukuran: 8 x 6 x 10 cm
- Rekomendasi umur: 15 tahun ke atas

Apakah Anda tertarik untuk membelinya? 😊
```

---

## 📊 Metrics & Monitoring

**Tracked Metrics:**
```python
{
  "total_queries": int,
  "avg_response_time": float,
  "query_types": {
    "product_inquiry": int,
    "product_search": int,
    "general": int,
    "out_of_context": int
  },
  "sessions": [
    {
      "session_id": str,
      "start_time": datetime,
      "end_time": datetime,
      "queries": int
    }
  ],
  "qa_logs": [
    {
      "question": str,
      "answer": str,
      "query_type": str,
      "response_time": float,
      "timestamp": datetime,
      "sources": [...]
    }
  ]
}
```

**Persistence:**
- Format: JSON
- Auto-save: Every query
- Location: `chatbot_metrics.json`
- Backup: `result_response_data.json`

---

## 🔐 Security & Environment

**Environment Variables (.env):**
```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbG...

# Google Gemini
GEMINI_API_KEY=AIzaSy...

# Optional: Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

**Security Measures:**
- ✅ Environment variables (no hardcoded secrets)
- ✅ Rate limiting (max 3 concurrent)
- ✅ Input validation (UltraValidator)
- ✅ SQL injection prevention (Supabase ORM)
- ✅ CORS configuration
- ✅ Error handling (no stack traces to user)

---

## 🚀 Deployment Architecture

**Production Setup:**
```
┌──────────────────────────────────────┐
│         Load Balancer (Nginx)        │
└────────────┬────────────┬────────────┘
             │            │
             ▼            ▼
     ┌──────────┐   ┌──────────┐
     │ Server 1 │   │ Server 2 │
     │ (FastAPI)│   │ (FastAPI)│
     └────┬─────┘   └────┬─────┘
          │              │
          └──────┬───────┘
                 │
                 ▼
        ┌────────────────┐
        │  Supabase      │
        │  (PostgreSQL)  │
        └────────────────┘
```

**Scaling Considerations:**
- Horizontal: Add more FastAPI instances
- Vertical: Increase FAISS index size
- Database: Supabase auto-scaling
- Cache: Add Redis for query cache

---

## 📝 Code Quality

**Type Hints:**
```python
def answer_question(self, question: str) -> Tuple[str, float, List[Document], str]:
    """
    Args:
        question: User question string
        
    Returns:
        Tuple of (answer, confidence, sources, query_type)
    """
```

**Error Handling:**
```python
try:
    result = self.qa_chain.invoke({"query": question})
except Exception as e:
    print(f"[ERROR] Failed: {e}")
    return error_msg, 0.0, [], query_type
finally:
    if lock_acquired:
        self.refresh_lock.release()
```

**Logging:**
```python
print(f"[EXACT_MATCHER] SKU detected: {sku}")
print(f"[AUTO-REFRESH] Poll #{count}")
print(f"[FUZZY_MATCH] '{word}' → '{brand}' (similarity: {score:.2f})")
```

---

## 🧪 Testing Strategy

**Unit Tests:**
- Validator logic
- Exact matcher patterns
- Fuzzy matching threshold

**Integration Tests:**
- End-to-end RAG pipeline
- Auto-refresh mechanism
- Concurrency handling

**Load Tests:**
- Concurrent requests (test_concurrent.py)
- Max throughput
- Response time under load

---

## 📚 References & Dependencies

**Core Libraries:**
- LangChain 0.3.x
- FAISS-CPU 1.9.x
- Sentence-Transformers 3.x
- FastAPI 0.115.x
- Supabase-py 2.x
- Google-GenerativeAI 0.8.x

**Python Version:** 3.10+

---

**Last Updated:** 9 November 2025  
**Document Version:** 1.0  
**Maintainer:** [Your Name]
