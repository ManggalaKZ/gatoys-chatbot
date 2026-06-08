"""
Enhanced Validator V2
Hybrid approach: Keyword + Semantic + Regex
Menggabungkan kelebihan sistem lama dan baru
"""

from typing import Tuple
import re

# Handle both relative and absolute imports
try:
    from .validator import ContextValidator
    from .semantic_validator import SemanticValidator
except ImportError:
    from validator import ContextValidator
    from semantic_validator import SemanticValidator

class EnhancedValidator:
    """
    Multi-layer validator yang menggabungkan:
    1. Regex pattern (quick reject)
    2. Keyword matching (fast accept)
    3. Semantic similarity (accurate validation)
    """
    
    def __init__(self, enable_semantic: bool = True):
        """
        Args:
            enable_semantic: Enable semantic layer (lebih akurat tapi lebih lambat)
        """
        self.enable_semantic = enable_semantic
        
        if self.enable_semantic:
            print("[ENHANCED VALIDATOR] Initializing with semantic layer...")
            self.semantic_validator = SemanticValidator()
        else:
            print("[ENHANCED VALIDATOR] Using keyword-only mode...")
    
    def is_in_context(self, question: str) -> Tuple[bool, str, float]:
        """
        Multi-layer validation
        
        Returns:
            (is_valid, reason, confidence)
        """
        
        # ========== LAYER 1: QUICK REJECT ==========
        # Gunakan regex dari sistem lama (cepat, akurat untuk pattern jelas)
        is_valid_old, reason_old = ContextValidator.is_in_context(question)
        
        if not is_valid_old and reason_old == "out_of_context_pattern":
            # Regex pattern match - langsung reject (confidence tinggi)
            return False, "regex_pattern_reject", 0.95
        
        if reason_old == "too_short":
            return False, "too_short", 1.0
        
        # ========== LAYER 2: KEYWORD QUICK ACCEPT ==========
        # Jika ada keyword jelas, langsung accept (fast path)
        if reason_old == "has_context_keyword":
            # Ada keyword yang jelas terkait business
            return True, "keyword_match", 0.85
        
        # ========== LAYER 3: SEMANTIC VALIDATION ==========
        # Untuk ambiguous cases, gunakan semantic
        if self.enable_semantic:
            is_related, confidence, semantic_reason = self.semantic_validator.is_semantically_related(question)
            
            # Semantic validator lebih teliti
            return is_related, f"semantic_{semantic_reason}", confidence
        
        # ========== FALLBACK: DEFAULT ==========
        # Jika semantic disabled dan tidak ada match jelas
        # Default allow untuk safety (customer service oriented)
        if reason_old == "default_allow":
            return True, "default_allow", 0.6
        else:
            return False, "general_question", 0.4
    
    def get_rejection_message(self, reason: str, question: str = "") -> str:
        """
        Get appropriate rejection message
        
        Args:
            reason: Rejection reason dari is_in_context
            question: Original question
            
        Returns:
            Rejection message string
        """
        # Gunakan message dari sistem lama (sudah bagus)
        return ContextValidator.get_rejection_message(reason, question)


# ============================================================
# TESTING
# ============================================================

def test_enhanced_validator():
    """Test enhanced validator"""
    
    validator = EnhancedValidator(enable_semantic=True)
    
    test_cases = [
        # IN-SCOPE cases (harus lolos)
        ("Ada mainan Molly?", True),
        ("Berapa harga LABUBU?", True),
        ("Rekomendasi mainan untuk umur 15 tahun", True),
        ("Bagaimana cara membeli?", True),
        ("Apa itu blind box?", True),
        ("Tokidoki masih ready?", True),
        ("Pengiriman berapa lama?", True),
        ("Bisa return kalau tidak suka?", True),
        ("Mainan apa yang cocok buat kolektor pemula?", True),
        ("Sweet Bean series ada?", True),
        ("Skullpanda harganya berapa?", True),
        ("Pucky masih ada stock?", True),
        
        # OUT-OF-SCOPE cases (harus ditolak)
        ("Cuaca hari ini bagaimana?", False),
        ("Berapa 5 + 5?", False),
        ("Cara coding Python?", False),
        ("Harga bitcoin sekarang?", False),
        ("Berita politik terkini?", False),
        ("Resep ayam goreng?", False),
        ("Siapa presiden Indonesia?", False),
        ("Cara install Windows?", False),
        
        # EDGE cases (tricky - yang sering salah)
        ("Tokidoki adalah nama band rock?", False),  # Konteks musik
        ("Harga emas hari ini naik?", False),  # 'harga' tapi finance
        ("Ada cara membuat kue coklat?", False),  # 'ada' + 'cara' tapi cooking
        ("5 kali 5 berapa hasilnya?", False),  # Math dengan kata
    ]
    
    print("\n" + "=" * 70)
    print("TESTING ENHANCED VALIDATOR (HYBRID)")
    print("=" * 70)
    
    correct = 0
    total = len(test_cases)
    false_positives = []
    false_negatives = []
    
    for question, expected in test_cases:
        is_valid, reason, confidence = validator.is_in_context(question)
        is_correct = is_valid == expected
        correct += is_correct
        
        if not is_correct:
            if is_valid and not expected:
                false_positives.append((question, reason, confidence))
            else:
                false_negatives.append((question, reason, confidence))
        
        status = "✅" if is_correct else "❌"
        print(f"{status} Q: {question}")
        print(f"   Expected: {expected} | Got: {is_valid} | Conf: {confidence:.3f}")
        print(f"   Reason: {reason}")
        print()
    
    accuracy = (correct / total) * 100
    
    print("=" * 70)
    print(f"ACCURACY: {correct}/{total} ({accuracy:.1f}%)")
    print("=" * 70)
    
    if false_positives:
        print("\n⚠️ FALSE POSITIVES (Seharusnya reject tapi lolos):")
        for q, r, c in false_positives:
            print(f"   - {q}")
            print(f"     Reason: {r} | Conf: {c:.3f}")
    
    if false_negatives:
        print("\n⚠️ FALSE NEGATIVES (Seharusnya lolos tapi ditolak):")
        for q, r, c in false_negatives:
            print(f"   - {q}")
            print(f"     Reason: {r} | Conf: {c:.3f}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    test_enhanced_validator()
