from core.chatbot import ToysShopChatbot
import time
from core.config import METRICS_FILE


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def test_chatbot_scenarios():
    """
    Test chatbot dengan berbagai scenario
    Useful untuk evaluasi skripsi
    """
    print("\n" + "="*70)
    print("  🧪 TESTING CHATBOT SCENARIOS")
    print("="*70)
    
    chatbot = ToysShopChatbot()
    if not chatbot.initialize():
        print("[FATAL] Chatbot initialization failed")
        return
    
    # Test scenarios
    test_questions = [
        "Ada mainan Molly tidak?",
        "Berapa harga LABUBU Adventure?",
        "Rekomendasi mainan untuk anak umur 13 tahun?",
        "Bagaimana cara membeli?",
        "Apa itu blind box?",
        "Mainan apa yang paling mahal?",
        "Ada mainan dari series PUCKY?",
        "Bagaimana kebijakan return?",
        "Ukuran Tokidoki Cactus Buddy berapa?",
        "Material Skullpanda Night Fairy apa?"
    ]
    
    print(f"\nMenjalankan {len(test_questions)} test cases...\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[TEST {i}/{len(test_questions)}]")
        answer, confidence, sources, query_type = chatbot.answer_question(question)
        chatbot.format_answer_display(question, answer, confidence, sources, query_type)
        time.sleep(1)  # Delay between tests
    
    # Show final metrics
    print("\n" + "="*70)
    print("  📊 TEST RESULTS")
    print("="*70)
    print(chatbot.metrics.get_summary())
    
    # Save test results
    chatbot.metrics.save_metrics()
    print(f"\n[SUCCESS] Test results saved to {METRICS_FILE}")

