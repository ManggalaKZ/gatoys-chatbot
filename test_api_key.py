import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("Testing Gemini API Key from .env...")
print("=" * 60)
print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
print("=" * 60)

# Test dengan LangChain (sama seperti yang dipakai server)
try:
    print("\n[TEST] Creating ChatGoogleGenerativeAI...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.3
    )
    
    print("[TEST] Invoking with test message...")
    response = llm.invoke("Say hello in one word")
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS! API Key is VALID!")
    print("=" * 60)
    print(f"Response: {response.content}")
    print("\n✅ Your chatbot should work now!")
    
except Exception as e:
    print("\n" + "=" * 60)
    print("❌ FAILED! API Key has issues")
    print("=" * 60)
    print(f"Error: {str(e)[:200]}")
    print("\n📋 ACTION REQUIRED:")
    print("1. Go to: https://aistudio.google.com/apikey")
    print("2. Create a NEW API key")
    print("3. Update GEMINI_API_KEY in .env file")
    print("4. Run this test again")
