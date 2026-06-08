"""
Auto Refresh FAISS Index ketika Supabase Database berubah

Cara kerja:
1. Polling: Cek timestamp `updated_at` di Supabase setiap N detik
2. Jika ada perubahan → rebuild FAISS index otomatis
3. Thread background yang tidak mengganggu request chat

Usage:
    from data.auto_refresh import start_auto_refresh_thread
    
    # Di chatbot.py atau server.py startup
    start_auto_refresh_thread(chatbot, check_interval=60)  # Check setiap 60 detik
"""

import threading
import time
from datetime import datetime
from typing import Optional, Callable
from supabase import create_client, Client
from utils.helpers import get_supabase_client  # <--- Import Singleton



class AutoRefreshManager:
    """Manage auto-refresh FAISS index dari Supabase changes"""
    
    def __init__(self, 
                 chatbot_instance,
                 supabase_url: str,
                 supabase_key: str,
                 check_interval: int = 60,  # seconds
                 on_refresh_callback: Optional[Callable] = None):
        """
        Args:
            chatbot_instance: Instance dari ToysShopChatbot
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            check_interval: Interval checking dalam seconds (default 60s = 1 menit)
            on_refresh_callback: Optional callback function yang dipanggil setelah refresh
        """
        self.chatbot = chatbot_instance
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.check_interval = check_interval
        self.on_refresh_callback = on_refresh_callback
        
        self.supabase: Optional[Client] = None
        self.last_modified_at: Optional[datetime] = None
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        
        # Thread lock untuk prevent race condition
        self.refresh_lock = threading.Lock()
        
        print(f"[AUTO-REFRESH] Initialized with {check_interval}s interval")
    
    def _init_supabase(self):
        """Initialize Supabase client using Singleton"""
        try:
            # Ganti create_client manual dengan singleton
            self.supabase = get_supabase_client()
            print("[AUTO-REFRESH] Supabase client initialized (Shared)")
        except Exception as e:
            print(f"[AUTO-REFRESH ERROR] Failed to init Supabase: {e}")
    
    def _get_latest_modified_time(self) -> Optional[datetime]:
        """
        Get timestamp terakhir dari table products
        Asumsi: table products punya column `updated_at` atau `created_at`
        """
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Query untuk ambil modified time terbaru
                # Sesuaikan nama column dengan schema Supabase kamu
                response = self.supabase.table('products') \
                    .select('updated_at') \
                    .order('updated_at', desc=True) \
                    .limit(1) \
                    .execute()
                
                if response.data and len(response.data) > 0:
                    timestamp_str = response.data[0]['updated_at']
                    # Parse ISO format datetime
                    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                
                return None
            
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"[AUTO-REFRESH WARN] Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    print(f"[AUTO-REFRESH ERROR] Failed to get latest modified time after {max_retries} attempts: {e}")
                    return None
    
    def _rebuild_index(self):
        """Rebuild index di background lalu swap"""
        # Tidak perlu lock global yang memblokir chat
        try:
            print("\n[AUTO-REFRESH] 🔄 Building new index in background...")
            
            # 1. Load data baru
            from utils.helpers import load_products_from_db, build_product_documents
            from retrieval.vector_store import FAISSIndexBuilder
            from retrieval.qa_chain import QAChainBuilder
            
            new_products = load_products_from_db()
            if not new_products: return

            new_docs = build_product_documents(new_products)
            
            # 2. Build Index Baru (Terpisah dari yang live)
            # Penting: Init builder baru, jangan pakai self.chatbot.index_builder
            new_index_builder = FAISSIndexBuilder() 
            success = new_index_builder.build_from_documents(new_docs)
            
            if not success: return
            
            # 3. Build Chain Baru
            new_retriever = new_index_builder.get_retriever(k=5)
            # Asumsi LLM thread-safe/stateless, bisa reuse self.chatbot.llm
            new_qa_chain = QAChainBuilder.create_chain(self.chatbot.llm, new_retriever)
            
            # 4. HOT SWAP
            # Panggil method update di chatbot untuk mengganti referensi
            self.chatbot.update_components(new_qa_chain, new_index_builder, new_products)
            
            # Call callback
            if self.on_refresh_callback:
                self.on_refresh_callback(len(new_products))
                
        except Exception as e:
            print(f"[AUTO-REFRESH ERROR] {e}")
            import traceback
            traceback.print_exc()
    
    def _check_loop(self):
        """Main loop untuk checking changes"""
        print("[AUTO-REFRESH] Background thread started")
        
        # Init Supabase
        self._init_supabase()
        
        # Get initial timestamp
        self.last_modified_at = self._get_latest_modified_time()
        print(f"[AUTO-REFRESH] Initial timestamp: {self.last_modified_at}")
        
        poll_count = 0
        
        while self.is_running:
            try:
                # Sleep dulu
                time.sleep(self.check_interval)
                
                poll_count += 1
                
                # Check timestamp terbaru
                print(f"[AUTO-REFRESH POLL #{poll_count}] Checking for changes...")
                current_modified_at = self._get_latest_modified_time()
                
                if current_modified_at is None:
                    print(f"[AUTO-REFRESH POLL #{poll_count}] Failed to fetch timestamp (network issue?)")
                    continue
                
                print(f"[AUTO-REFRESH POLL #{poll_count}] Last: {self.last_modified_at} | Current: {current_modified_at}")
                
                # Compare dengan last timestamp
                if self.last_modified_at is None or current_modified_at > self.last_modified_at:
                    print(f"[AUTO-REFRESH] 🔔 Change detected: {self.last_modified_at} → {current_modified_at}")
                    
                    # Rebuild index
                    self._rebuild_index()
                    
                    # Update last timestamp
                    self.last_modified_at = current_modified_at
                
                else:
                    # No changes
                    print(f"[AUTO-REFRESH POLL #{poll_count}] ✓ No changes detected")
            
            except Exception as e:
                print(f"[AUTO-REFRESH ERROR] Error in check loop: {e}")
                import traceback
                traceback.print_exc()
        
        print("[AUTO-REFRESH] Background thread stopped")
    
    def start(self):
        """Start auto-refresh thread"""
        if self.is_running:
            print("[AUTO-REFRESH WARN] Already running")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._check_loop, daemon=True)
        self.thread.start()
        print("[AUTO-REFRESH] Started in background thread")
    
    def stop(self):
        """Stop auto-refresh thread"""
        if not self.is_running:
            return
        
        print("[AUTO-REFRESH] Stopping...")
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[AUTO-REFRESH] Stopped")
    
    def get_lock(self):
        """Get refresh lock untuk digunakan di chatbot (prevent race condition)"""
        return self.refresh_lock


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def start_auto_refresh_thread(chatbot_instance, 
                              supabase_url: str = None,
                              supabase_key: str = None,
                              check_interval: int = 60) -> AutoRefreshManager:
    """
    Helper function untuk start auto-refresh dengan mudah
    
    Args:
        chatbot_instance: Instance dari ToysShopChatbot
        supabase_url: Supabase URL (default dari env)
        supabase_key: Supabase key (default dari env)
        check_interval: Interval check dalam seconds (default 60s)
    
    Returns:
        AutoRefreshManager instance
    
    Example:
        # Di server.py startup
        from data.auto_refresh import start_auto_refresh_thread
        
        refresh_manager = start_auto_refresh_thread(
            chatbot,
            check_interval=120  # Check setiap 2 menit
        )
    """
    # Get from env if not provided
    if not supabase_url or not supabase_key:
        import os
        supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase URL and Key must be provided or set in environment")
    
    # Create and start manager
    manager = AutoRefreshManager(
        chatbot_instance,
        supabase_url,
        supabase_key,
        check_interval=check_interval
    )
    manager.start()
    
    return manager
