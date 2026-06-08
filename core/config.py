"""
Configuration & Constants
Centralized configuration management
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================
# API KEYS
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ============================================================
# MODEL SETTINGS
# ============================================================

# Gemini LLM
GEMINI_MODEL = "gemini-2.5-flash"  # Latest stable version
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 1024

# Embedding Model
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_MODEL_TYPE = "sentence-transformers"  # or "bge"

# BGE-M3 Settings (if using BGE)
BGE_MAX_LENGTH = 8192
BGE_USE_FP16 = True

# ============================================================
# RETRIEVAL SETTINGS
# ============================================================

RETRIEVAL_TOP_K = 4
MAX_CONTEXT_LENGTH = 2000

# ============================================================
# INDEX SETTINGS
# ============================================================

FAISS_INDEX_PATH = "faiss_index"
FAISS_SAVE_ENABLED = True

AUTO_REFRESH_ENABLED = True
REFRESH_INTERVAL_MINUTES = 60

# ============================================================
# DISPLAY OPTIONS
# ============================================================

SHOW_RETRIEVED_DOCS = True
SHOW_CONFIDENCE_SCORE = True
VERBOSE_MODE = False

# ============================================================
# METRICS
# ============================================================

METRICS_ENABLED = True
METRICS_FILE = "chatbot_metrics.json"
QA_LOG_FILE = "result_response_data.json"

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# ============================================================
# VALIDATION
# ============================================================

def validate_config():
    """Validate required configuration"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found!")
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase credentials not found!")
    
    print("[CONFIG] ✓ Configuration validated")