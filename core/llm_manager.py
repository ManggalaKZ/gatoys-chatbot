"""
LLM Manager
Initialize dan manage Gemini LLM
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from .config import GEMINI_API_KEY, GEMINI_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS

def initialize_gemini():
    """
    Initialize Google Gemini LLM
    
    Returns:
        ChatGoogleGenerativeAI instance
    """
    print(f"[LLM] Initializing Google Gemini: {GEMINI_MODEL}")
    
    try:
        # Create LangChain wrapper directly (no google.genai needed)
        # Try multiple model formats for compatibility
        model_attempts = [
            GEMINI_MODEL,                                    # e.g., "gemini-1.5-flash-latest"
            f"models/{GEMINI_MODEL}",                        # e.g., "models/gemini-1.5-flash-latest"
            "gemini-1.5-flash",                              # Fallback 1
            "gemini-pro",                                    # Fallback 2
        ]
        
        last_error = None
        for model_name in model_attempts:
            try:
                print(f"[LLM] Trying model: {model_name}")
                
                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=GEMINI_API_KEY,
                    temperature=LLM_TEMPERATURE,
                    max_output_tokens=LLM_MAX_TOKENS,
                    convert_system_message_to_human=True
                )
                
                # Test LLM
                test_response = llm.invoke("test")
                
                print(f"[SUCCESS] Gemini LLM initialized: {model_name}")
                print(f"[CONFIG] Temperature: {LLM_TEMPERATURE}, Max Tokens: {LLM_MAX_TOKENS}")
                
                return llm
                
            except Exception as e:
                last_error = e
                print(f"[WARN] Model {model_name} failed: {str(e)[:100]}")
                continue
        
        # All attempts failed
        raise last_error
        
    except Exception as e:
        print(f"[FATAL] Gemini initialization failed: {e}")
        print("Pastikan GEMINI_API_KEY sudah benar di file .env")
        print("Atau buat API key baru di: https://aistudio.google.com/apikey")
        raise