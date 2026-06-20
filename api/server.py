"""
FastAPI Server
Main API application untuk GA Toys Chatbot
"""

import asyncio
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import traceback
from data.auto_refresh import start_auto_refresh_thread
from zoneinfo import ZoneInfo



from .models import (
    QueryRequest, QueryResponse, SourceInfo,
    MetricsResponse, HealthResponse, RefreshResponse
)
from . import (
    get_chatbot,
    request_semaphore,
    increment_active_requests,
    decrement_active_requests,
    MAX_CONCURRENT_REQUESTS,
    REDIS_AVAILABLE
)

# ============================================================
# LIFECYCLE MANAGEMENT
# ============================================================

# Global variable untuk auto-refresh manager
refresh_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management
    
    Startup:
        - Initialize chatbot singleton
        - Start auto-refresh thread
        - Warm up models
    
    Shutdown:
        - Stop auto-refresh thread
        - Save metrics
        - Cleanup resources
    """
    global refresh_manager
    
    # ============================================================
    # STARTUP
    # ============================================================
    print("="*70)
    print("  🚀 GA TOYS CHATBOT API - STARTUP")
    print("="*70)
    print(f"  Redis: {'✓ Available' if REDIS_AVAILABLE else '✗ Not Available'}")
    print(f"  Max Concurrent: {MAX_CONCURRENT_REQUESTS}")
    print("="*70)
    
    try:
        print("\n[STARTUP] Initializing chatbot...")
        chatbot = get_chatbot()  # Initialize singleton
        print("[SUCCESS] Chatbot ready to accept requests")
        
        # Set refresh lock FIRST before starting thread
        print("\n[STARTUP] Starting auto-refresh thread...")
        refresh_manager = start_auto_refresh_thread(
            chatbot,
            check_interval=300
        )
        
        # Set refresh lock to chatbot for thread-safe operations
        # chatbot.refresh_lock = refresh_manager.get_lock()
        print("[SUCCESS] Auto-refresh thread started with lock protection")
        print(f"[INFO] Auto-refresh interval: 300 seconds (5 minutes)")
        
    except Exception as e:
        print(f"[FATAL] Startup failed: {e}")
        raise
    
    yield  # Application runs here
    
    # ============================================================
    # SHUTDOWN
    # ============================================================
    print("\n[SHUTDOWN] Stopping auto-refresh thread...")
    if refresh_manager:
        try:
            refresh_manager.stop()
            print("[SUCCESS] Auto-refresh thread stopped")
        except Exception as e:
            print(f"[WARN] Failed to stop auto-refresh: {e}")
    
    print("\n[SHUTDOWN] Saving metrics...")
    try:
        chatbot = get_chatbot()
        if chatbot:
            chatbot.metrics.end_session()
        print("[SUCCESS] Metrics saved")
    except Exception as e:
        print(f"[WARN] Shutdown error: {e}")
    
    print("="*70)
    print("  👋 GA TOYS CHATBOT API - SHUTDOWN COMPLETE")
    print("="*70)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

# FILE: app/api/server.py

app = FastAPI(
    title="Smart RAG Chatbot API", 
    description="""
    Enterprise Grade Customer Service Chatbot API powered by RAG Technology.
    
    ## Features
    - 🤖 Pure RAG Architecture
    - 🔒 Thread-safe Operations
    - 🚦 Concurrency Control
    - 📊 Comprehensive Metrics
    - 🌐 Distributed Ready
    
    ## Endpoints
    - `POST /chat` - Main chat endpoint
    - `GET /metrics` - Get performance metrics
    - `POST /refresh-index` - Force database sync
    - `GET /health` - System health check
    """,
    version="1.0.0", # Atau 2.0.0 biar terlihat update
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================
# CORS MIDDLEWARE
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  
        # "http://localhost:3000",
        # "https://gatoys.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - Simple health check
    
    Returns basic service information
    """
    return {
        "service": "GA Toys Chatbot API",
        "status": "online",
        "version": "1.0.0",
        "timestamp": datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(),
        "docs": "/docs",
        "redis": "available" if REDIS_AVAILABLE else "unavailable"
    }


@app.post("/chat", response_model=QueryResponse, tags=["Chat"])
async def chat(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Main chat endpoint
    
    Process user question dengan RAG (Retrieval-Augmented Generation)
    
    **Flow:**
    1. Queue management (max 3 concurrent)
    2. Context validation
    3. RAG retrieval
    4. LLM generation
    5. Confidence calculation
    6. Metrics logging
    
    **Rate Limit:** Max 3 concurrent requests (others queued)
    
    **Response Time:** 1-3 seconds average
    """
    # Acquire semaphore (wait if queue full)
    async with request_semaphore:
        increment_active_requests()
        try:
            chatbot = get_chatbot()
            
            # Validasi chatbot ready
            if not chatbot or not chatbot.qa_chain:
                raise HTTPException(status_code=503, detail="Chatbot is initializing")

            # Jalankan di ThreadPool karena FAISS/Regex itu CPU bound
            # dan melepaskan GIL (FAISS), tapi Regex tidak.
            loop = asyncio.get_event_loop()

            # Ukur waktu respons aktual per-permintaan (untuk chat_logs & uji performa)
            import time
            _t0 = time.perf_counter()
            answer, confidence, sources, query_type = await loop.run_in_executor(
                None,
                chatbot.answer_question,
                request.question,
                request.session_id
            )
            response_time = round(time.perf_counter() - _t0, 3)
            
            # Format sources
            sources_list = []
            for i, doc in enumerate(sources[:5], 1):
                source_info = SourceInfo(
                    rank=i,
                    type=doc.metadata.get('type', 'unknown')
                )
                
                if doc.metadata.get('type') == 'product':
                    source_info.product_name = doc.metadata.get('name', 'N/A')
                    source_info.price = doc.metadata.get('price', 0)
                    source_info.image = doc.metadata.get('image')
                    source_info.product_id = doc.metadata.get('product_id')
                else:
                    source_info.title = doc.metadata.get('title', 'Store Info')
                
                sources_list.append(source_info)
            
            # Get query ID
            query_id = len(chatbot.metrics.qa_logs)

            # Simpan interaksi ke chat_logs (background task, tidak memblok respons)
            from utils.helpers import save_chat_log
            background_tasks.add_task(
                save_chat_log,
                request.user_id,
                request.session_id,
                request.question,
                answer,
                query_type,
                confidence,
                response_time,
            )

            return QueryResponse(
                answer=answer,
                query_type=query_type,
                response_time=response_time,
                confidence=confidence,
                sources=sources_list,
                query_id=query_id
            )
            
        except Exception as e:
            print(f"[ERROR] Chat endpoint error: {e}")
            import traceback
            print("[FULL TRACEBACK]")
            traceback.print_exc()
            print("[END TRACEBACK]")
            raise HTTPException(
                status_code=500, 
                detail=f"Internal server error: {str(e)}"
            )
        
        finally:
            # Release tracking (always executed)
            decrement_active_requests()


@app.get("/metrics", response_model=MetricsResponse, tags=["Monitoring"])
async def get_metrics():
    """
    Get current performance metrics
    
    Returns aggregated metrics untuk monitoring dan analisis:
    - Total queries processed
    - Average response time
    - Query type distribution
    - Number of sessions
    
    **Use Case:** Monitoring dashboard, analytics
    """
    try:
        print("[METRICS] Fetching chatbot instance...")
        chatbot = get_chatbot()
        print(f"[METRICS] Chatbot fetched: {chatbot is not None}")
        
        print("[METRICS] Accessing metrics...")
        total_queries = chatbot.metrics.metrics["total_queries"]
        avg_response_time = chatbot.metrics.metrics["avg_response_time"]
        query_types = chatbot.metrics.metrics["query_types"]
        sessions = len(chatbot.metrics.metrics["sessions"])
        
        print(f"[METRICS] Successfully fetched: queries={total_queries}, sessions={sessions}")
        
        return MetricsResponse(
            total_queries=total_queries,
            avg_response_time=avg_response_time,
            query_types=query_types,
            sessions=sessions
        )
        
    except Exception as e:
        print(f"[ERROR] Metrics endpoint error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )


@app.post("/refresh-index", response_model=RefreshResponse, tags=["Admin"])
async def refresh_index(background_tasks: BackgroundTasks):
    """
    Manually refresh FAISS vector index
    
    **Background Task:** Index refresh runs in background
    
    **Use Case:**
    - After adding new products to database
    - Manual index update
    - Scheduled maintenance
    
    **Warning:** Heavy operation (10-30 seconds)
    
    **Response:** Immediate (task runs in background)
    """
    try:
        chatbot = get_chatbot()
        
        # Define refresh task
        def do_refresh():
            """Background refresh task"""
            print("[REFRESH] Starting index refresh...")
            try:
                # Pakai satu sumber kebenaran yang sama dengan init & auto-refresh
                from utils.helpers import load_products_from_db, build_product_documents

                # Reload products
                chatbot.products_cache = load_products_from_db()

                # Rebuild documents
                docs = build_product_documents(chatbot.products_cache)
                
                # Rebuild index
                chatbot.index_builder.build_from_documents(docs)
                
                # Recreate QA chain
                chatbot.create_qa_chain()
                
                print("[REFRESH] Index refresh completed")
                
            except Exception as e:
                print(f"[ERROR] Refresh failed: {e}")
        
        # Add to background tasks
        background_tasks.add_task(do_refresh)
        
        return RefreshResponse(
            status="started",
            message="Index refresh started in background"
        )
        
    except Exception as e:
        print(f"[ERROR] Refresh endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start refresh: {str(e)}"
        )


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """
    Detailed health check
    
    Returns comprehensive system status:
    - Overall status (healthy/unhealthy)
    - Chatbot initialization status
    - LLM readiness
    - FAISS index status
    - Total queries processed
    
    **Use Case:**
    - Load balancer health checks
    - Kubernetes liveness/readiness probes
    - Monitoring systems (Prometheus, etc.)
    
    **Status Codes:**
    - 200: Healthy
    - 200 with status="unhealthy": Degraded (but responding)
    """
    try:
        chatbot = get_chatbot()
        
        # Safe attribute checking dengan getattr
        llm_ready = getattr(chatbot, 'llm', None) is not None
        
        # Check index builder (bisa bernama vectorstore, index_builder, atau vector_store)
        index_ready = False
        for attr_name in ['index_builder', 'vectorstore', 'vector_store', 'faiss_index']:
            if hasattr(chatbot, attr_name):
                attr = getattr(chatbot, attr_name)
                if attr is not None:
                    # Check if it has vectorstore attribute
                    if hasattr(attr, 'vectorstore'):
                        index_ready = attr.vectorstore is not None
                    else:
                        index_ready = True
                    break
        
        # Safe metrics access
        total_queries = 0
        if hasattr(chatbot, 'metrics') and chatbot.metrics:
            if hasattr(chatbot.metrics, 'metrics'):
                total_queries = chatbot.metrics.metrics.get("total_queries", 0)
        
        return HealthResponse(
            status="healthy",
            chatbot_initialized=chatbot is not None,
            llm_ready=llm_ready,
            index_ready=index_ready,
            total_queries=total_queries,
            timestamp=datetime.now(ZoneInfo("Asia/Jakarta")).isoformat()
        )
        
    except Exception as e:
        # Still return 200 but with unhealthy status
        return HealthResponse(
            status="unhealthy",
            error=str(e),
            timestamp=datetime.now(ZoneInfo("Asia/Jakarta")).isoformat()
        )


@app.get("/debug/chatbot-structure", tags=["Debug"])
async def debug_chatbot_structure():
    """Debug: Inspect chatbot structure"""
    try:
        chatbot = get_chatbot()
        
        info = {
            "chatbot_type": type(chatbot).__name__,
            "chatbot_attributes": dir(chatbot),
            "index_builder": {
                "exists": hasattr(chatbot, 'index_builder'),
                "is_none": getattr(chatbot, 'index_builder', 'not_found') is None,
                "type": type(getattr(chatbot, 'index_builder', None)).__name__ if hasattr(chatbot, 'index_builder') and chatbot.index_builder else "None",
                "attributes": dir(chatbot.index_builder) if hasattr(chatbot, 'index_builder') and chatbot.index_builder else []
            },
            "retriever_factory": {
                "exists": hasattr(chatbot, 'retriever_factory'),
                "is_none": getattr(chatbot, 'retriever_factory', 'not_found') is None,
                "type": type(getattr(chatbot, 'retriever_factory', None)).__name__ if hasattr(chatbot, 'retriever_factory') and chatbot.retriever_factory else "None"
            },
            "qa_chain": {
                "exists": hasattr(chatbot, 'qa_chain'),
                "is_none": getattr(chatbot, 'qa_chain', 'not_found') is None,
                "type": type(getattr(chatbot, 'qa_chain', None)).__name__ if hasattr(chatbot, 'qa_chain') and chatbot.qa_chain else "None"
            },
            "llm": {
                "exists": hasattr(chatbot, 'llm'),
                "is_none": getattr(chatbot, 'llm', 'not_found') is None,
                "type": type(getattr(chatbot, 'llm', None)).__name__ if hasattr(chatbot, 'llm') and chatbot.llm else "None"
            }
        }
        
        return info
        
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}
    
    
    
# ============================================================
# ERROR HANDLERS
# ============================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return {
        "error": "Not Found",
        "message": "The requested endpoint does not exist",
        "available_endpoints": [
            "GET /",
            "POST /chat",
            "GET /metrics",
            "POST /refresh-index",
            "GET /health",
            "GET /docs"
        ]
    }


# ============================================================
# RUN SERVER (if executed directly)
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║          GA TOYS CHATBOT API SERVER                       ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  FastAPI with Concurrency Support                        ║
    ║  Redis Distributed Locking                               ║
    ║  Thread-safe Operations                                  ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8001,
        workers=1, 
        reload=False,  
        log_level="info"
    )