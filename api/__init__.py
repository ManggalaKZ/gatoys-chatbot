"""
API Module
FastAPI utilities, concurrency control, dan distributed locking
"""

import threading
from typing import Optional
from datetime import datetime
from asyncio import Semaphore

from core.chatbot import ToysShopChatbot
from metrics.tracker import MetricsTracker
from zoneinfo import ZoneInfo


# ============================================================
# CONFIGURATION
# ============================================================

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Try import redis, set flag if not available
try:
    import redis as redis_module
    REDIS_INSTALLED = True
except ImportError:
    print("[WARN] Redis module not installed - running without Redis")
    redis_module = None
    REDIS_INSTALLED = False

# Concurrency settings
MAX_CONCURRENT_REQUESTS = 3

# ============================================================
# GLOBAL STATE
# ============================================================

# Singleton chatbot instance
chatbot_instance: Optional[ToysShopChatbot] = None
chatbot_lock = threading.Lock()

# Redis client
if REDIS_INSTALLED:
    try:
        redis_client = redis_module.Redis(
            host=REDIS_HOST, 
            port=REDIS_PORT, 
            db=REDIS_DB, 
            decode_responses=True,
            socket_connect_timeout=5
        )
        # Test connection
        redis_client.ping()
        REDIS_AVAILABLE = True
        print("[INFO] Redis connected successfully")
    except Exception as e:
        print(f"[WARN] Redis not available: {e}")
        print("[WARN] Running without distributed locking")
        redis_client = None
        REDIS_AVAILABLE = False
else:
    print("[WARN] Redis module not installed - running without distributed locking")
    redis_client = None
    REDIS_AVAILABLE = False

# Concurrency control
request_semaphore = Semaphore(MAX_CONCURRENT_REQUESTS)
active_requests = 0
request_lock = threading.Lock()

# ============================================================
# CHATBOT SINGLETON
# ============================================================

def get_chatbot() -> ToysShopChatbot:
    """
    Get or create chatbot singleton instance (thread-safe)
    
    Uses double-check locking pattern untuk efficiency
    
    Returns:
        ToysShopChatbot instance
        
    Raises:
        RuntimeError: If chatbot initialization fails
    """
    global chatbot_instance
    
    if chatbot_instance is None:
        with chatbot_lock:
            # Double-check locking
            if chatbot_instance is None:
                print("[INIT] Initializing chatbot singleton...")
                chatbot_instance = ToysShopChatbot()
                if not chatbot_instance.initialize():
                    raise RuntimeError("Failed to initialize chatbot")
                print("[SUCCESS] Chatbot singleton ready")
    
    return chatbot_instance


# ============================================================
# REDIS DISTRIBUTED LOCK
# ============================================================

class RedisLock:
    """
    Distributed lock menggunakan Redis
    
    Untuk prevent race conditions di multi-server environment
    """
    
    def __init__(self, key: str, timeout: int = 10):
        """
        Initialize Redis lock
        
        Args:
            key: Lock key identifier
            timeout: Lock timeout in seconds
        """
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.token = None
        self.enabled = REDIS_AVAILABLE
    
    def acquire(self) -> bool:
        """
        Acquire lock
        
        Returns:
            True if lock acquired, False otherwise
        """
        if not self.enabled:
            return True  # Always succeed if Redis not available
        
        self.token = datetime.now(ZoneInfo("Asia/Jakarta")).isoformat()
        return redis_client.set(self.key, self.token, nx=True, ex=self.timeout)
    
    def release(self):
        """Release lock (only if we own it)"""
        if not self.enabled or not self.token:
            return
        
        # Lua script untuk atomic check-and-delete
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        redis_client.eval(lua_script, 1, self.key, self.token)


# ============================================================
# THREAD-SAFE METRICS
# ============================================================

class ThreadSafeMetrics:
    """
    Thread-safe wrapper untuk MetricsTracker
    
    Menggunakan Redis lock untuk distributed environment
    """
    
    def __init__(self, tracker: MetricsTracker):
        """
        Initialize thread-safe metrics
        
        Args:
            tracker: MetricsTracker instance to wrap
        """
        self.tracker = tracker
        self.lock = threading.Lock()
    
    def log_query(self, **kwargs):
        """
        Thread-safe log query
        
        Args:
            **kwargs: Arguments to pass to tracker.log_query()
        """
        lock = RedisLock("metrics_write")
        
        try:
            if lock.acquire():
                with self.lock:
                    self.tracker.log_query(**kwargs)
        finally:
            lock.release()
    
    def get_summary(self) -> str:
        """
        Thread-safe get summary
        
        Returns:
            Metrics summary string
        """
        with self.lock:
            return self.tracker.get_summary()


# ============================================================
# REQUEST TRACKING
# ============================================================

def increment_active_requests() -> int:
    """
    Increment active request counter (thread-safe)
    
    Returns:
        Current number of active requests
    """
    global active_requests
    with request_lock:
        active_requests += 1
        return active_requests


def decrement_active_requests() -> int:
    """
    Decrement active request counter (thread-safe)
    
    Returns:
        Current number of active requests
    """
    global active_requests
    with request_lock:
        active_requests -= 1
        return active_requests


def get_active_requests() -> int:
    """
    Get current active request count (thread-safe)
    
    Returns:
        Number of active requests
    """
    global active_requests
    with request_lock:
        return active_requests


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    'get_chatbot',
    'RedisLock',
    'ThreadSafeMetrics',
    'request_semaphore',
    'increment_active_requests',
    'decrement_active_requests',
    'get_active_requests',
    'MAX_CONCURRENT_REQUESTS',
    'REDIS_AVAILABLE'
]