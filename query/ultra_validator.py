"""
Ultra Validator V3 - Advanced ML-Based Context Validation
Target Accuracy: 90-97%

Fitur:
1. Multi-embedding approach (2 models)
2. Context-aware keyword matching
3. Explicit blacklist
4. Domain-specific phrase detection
5. Question intent classification
6. Confidence-based decision making
"""

from typing import Tuple, List, Dict
import re
from functools import lru_cache

# Handle both relative and absolute imports
try:
    from .validator import ContextValidator
    from .semantic_validator import SemanticValidator
except ImportError:
    from validator import ContextValidator
    from semantic_validator import SemanticValidator


class UltraValidator:
    """
    Ultra validator dengan multiple layers untuk akurasi maksimal
    Target: 90-97% accuracy
    """
    
    # Explicit blacklist - out-of-context keywords yang pasti reject
    BLACKLIST_KEYWORDS = {
        # Finance
        'bitcoin', 'btc', 'ethereum', 'kripto', 'cryptocurrency', 'saham', 
        'forex', 'trading', 'reksadana', 'obligasi', 'valas', 'bursa',
        
        # Technology/Programming (Hapus 'website' dan 'aplikasi' karena wajar ditanyakan pembeli)
        'coding', 'programming', 'python', 'javascript', 'java', 'html', 
        'css', 'php', 'sql', 'database', 'server', 'hosting', 'linux', 'ubuntu',
        
        # Food/Cooking (Hapus 'kue', 'roti' karena banyak mainan bertema dessert)
        'resep', 'memasak', 'tumis', 'rebus', 'panggang',
        
        # Politics/News
        'presiden', 'menteri', 'politik', 'pemilu', 'pilkada', 
        'pemerintah', 'dpr', 'partai',
        
        # Education (non-product)
        'rumus', 'matematika', 'fisika', 'kimia', 'biologi',
        'pelajaran', 'ujian', 'tutorial',
    }
    
    # Domain-specific phrases yang HARUS ada untuk context produk
    PRODUCT_CONTEXT_PHRASES = {
        'mainan', 'figurine', 'figure', 'blind box', 'collectible', 
        'koleksi', 'boneka', 'action figure', 'toy', 'toys',
        'ga toys', 'gatoys', 'toko', 'produk', 'barang',
        'box', 'seri', 'series', 'edisi', 'edition', 'karakter', 'ori', 'asli'
    }
    
    # Brand/Series names (strong indicator of in-context)
    BRAND_NAMES = {
        'tokidoki', 'molly', 'labubu', 'pucky', 'dimoo', 'skullpanda',
        'hirono', 'sweet bean', 'bunny', 'crybaby', 'azura', 
        'hacipupu', 'skull panda', 'kasing lung',
    }
    
    # Shopping/Store keywords
    SHOPPING_KEYWORDS = {
        'beli', 'bayar', 'pesan', 'order', 'kirim', 'ongkir',
        'pengiriman', 'pembayaran', 'harga', 'diskon', 'promo',
        'stock', 'stok', 'ready', 'tersedia', 'ada', 'punya',
        'jual', 'dijual', 'harganya', 'belinya', 'nyari', 'cari', 
        'mau', 'pengen', 'min', 'kak', 'minat', 'katalog',
        
        # Bahasa Inggris
        'buy', 'purchase', 'pay', 'payment', 'ship', 'shipping',
        'delivery', 'cost', 'price', 'pricing', 'discount', 'sale',
        'available', 'sell', 'sold', 'shipping cost', 'fee'
    }
    
    # Store-specific keywords (always in-context)
    STORE_OPERATION_KEYWORDS = {
        'cara membeli', 'cara beli', 'cara pesan', 'cara order',
        'pengiriman', 'return', 'garansi', 'kebijakan',
        'bagaimana membeli', 'bagaimana beli', 'gimana beli',
        'berapa lama kirim', 'berapa lama pengiriman',
        'bisa tukar', 'tukar gak', 'bisa cod', 'cod untuk',
        'foto real', 'real pict', 'pict sebelum', 'checkout',
        'dapet duplikat', 'dapat duplikat', 'hari', 'jam berapa', 'tanggal berapa', 'jam'
        
        # TAMBAHAN BAHASA INGGRIS
        'how to buy', 'how to order', 'how to purchase',
        'shipping time', 'how long', 'return policy', 'warranty',
        'can i exchange', 'exchange policy', 'real photo', 'real picture',
        'before checkout', 'duplicate', 'get double'
    }
    
    CS_PATTERNS = [
        r'\bapa\s+(yang\s+)?(bisa|dapat)\s+(kamu|anda|kalian)\s+bantu',
        r'\bbantu\s+apa\b',
        r'\bbisa\s+bantu\s+apa',
        r'\binfo\s+(apa|tentang|seputar)',
        r'\bapa\s+saja\s+(yang\s+)?(bisa|dapat)',
        r'\blayanan\s+(apa|kamu)',
        r'\bkamu\s+(bisa|dapat)',
        r'\bkamu\s+(siapa|untuk\s+apa)',
        r'\bini\s+toko\s+apa',
            
        # TAMBAHAN POLA BAHASA INGGRIS
        r'\b(can|could)\s+(you|u)\s+help',      # Can you help
        r'\bwhat\s+can\s+(you|u)\s+do',         # What can you do
        r'\bhow\s+(can|do)\s+i\s+(buy|order)',  # How can I buy
        r'\bdo\s+(you|u)\s+have',               # Do you have
        r'\bshipping\s+(to|fee|cost)',          # Shipping to/fee
        r'\bhow\s+much\s+(is|does)',            # How much is
        r'\bprice\s+(of|for)',                  # Price of
        r'\btell\s+me\s+about'                  # Tell me about
    ]

    STORE_PATTERNS = [
        r'bisa\s+(tukar|cod|kasih)',
        r'bisa\s+kasih\s+foto',
        r'(dapet|dapat)\s+duplikat',
        r'foto\s+real',
        r'real\s+pict',
        r'sebelum\s+checkout',
    ]
    
    def __init__(self, enable_semantic: bool = True, strict_mode: bool = False):
        """
        Args:
            enable_semantic: Enable semantic validation layer
            strict_mode: Jika True, lebih ketat dalam accept (reduce false positive)
        """
        self.enable_semantic = enable_semantic
        self.strict_mode = strict_mode
        
        if self.enable_semantic:
            print("[ULTRA VALIDATOR] Initializing with semantic layer...")
            self.semantic_validator = SemanticValidator()
        else:
            print("[ULTRA VALIDATOR] Using rule-based only mode...")
    
    def _has_blacklist_keyword(self, question: str) -> Tuple[bool, str]:
        """Check if question contains blacklisted keywords"""
        q_lower = question.lower()
        
        for keyword in self.BLACKLIST_KEYWORDS:
            if re.search(r'\b' + re.escape(keyword) + r'\b', q_lower):
                return True, keyword
        
        return False, ""
    
    def _has_product_context(self, question: str) -> bool:
        """Check if question has product-related context"""
        q_lower = question.lower()
        
        # Check brand names
        for brand in self.BRAND_NAMES:
            if brand in q_lower:
                return True
        
        # Check product context phrases
        for phrase in self.PRODUCT_CONTEXT_PHRASES:
            if phrase in q_lower:
                return True
        
        return False
    
    def _has_store_operation_context(self, question: str) -> bool:
        """Check if question is about store operations"""
        q_lower = question.lower()
        
        # Check exact phrases
        for phrase in self.STORE_OPERATION_KEYWORDS:
            if phrase in q_lower:
                return True
        
        # Check common store operation patterns
 
        for pattern in self.STORE_PATTERNS:
            if re.search(pattern, q_lower):
                return True
        
        return False
    
    def _is_ambiguous_keyword_question(self, question: str) -> Tuple[bool, str]:
        """
        Diperbarui: Lebih luwes. Hanya menolak jika benar-benar tidak ada konteks
        dan pertanyaannya sangat aneh.
        """
        q_lower = question.lower()
        
        # Jika panjang karakter sangat pendek (contoh: "ada?", "harga?"),
        # biarkan lolos karena ini biasanya pertanyaan lanjutan (follow up) dalam chat.
        if len(question.split()) <= 3:
            return False, "" 
            
        # Check store operation keywords first (always in-context)
        if self._has_store_operation_context(question):
            return False, ""  
        
        ambiguous = ['harga', 'berapa', 'ada', 'punya']
        
        for keyword in ambiguous:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, q_lower):
                has_product = self._has_product_context(question)
                has_shopping = any(kw in q_lower for kw in self.SHOPPING_KEYWORDS)
                
                # Jika tidak ada konteks TAPI ada kata ganti (ini, itu, nya) -> Loloskan
                has_pronoun = any(w in q_lower for w in['ini', 'itu', 'nya', 'yg', 'yang'])
                
                if not (has_product or has_shopping or has_pronoun):
                    # Hanya kembalikan ambigu jika kalimatnya panjang tapi tidak jelas konteksnya
                    if len(question.split()) > 5:
                        return True, f"ambiguous_keyword:{keyword}_without_context"
        
        return False, ""
    
    def _check_question_intent(self, question: str) -> Tuple[str, float]:
        """
        Classify question intent
        Returns: (intent, confidence)
        """
        q_lower = question.lower()
        
        # Math/Calculation
        if re.search(r'\d+\s*[\+\-\*\/xX×]\s*\d+', q_lower):
            return 'math', 1.0
        if any(w in q_lower for w in ['hitung', 'hasil', 'berapa hasil']):
            return 'math', 0.9
        
        # Weather
        if any(w in q_lower for w in ['cuaca']):
            return 'weather', 0.95
        
        if any(re.search(pattern, q_lower) for pattern in self.CS_PATTERNS):
            return 'customer_service_help', 0.9
        
        # Shopping (in-context)
        if any(w in q_lower for w in self.SHOPPING_KEYWORDS):
            if self._has_product_context(question):
                return 'shopping', 0.9
            else:
                return 'shopping_unclear', 0.5
        
        # Product inquiry (in-context)
        if self._has_product_context(question):
            return 'product_inquiry', 0.85
        
        # General question
        return 'general', 0.3
    
    def is_in_context(self, question: str) -> Tuple[bool, str, float]:
        """
        Ultra validation dengan multiple checks
        
        Returns:
            (is_valid, reason, confidence)
        """
        
        # ========== LAYER 0: PRE-CHECK ==========
        if len(question.strip()) < 3:
            return False, "too_short", 1.0
        
        # ========== LAYER 1: EXPLICIT BLACKLIST ==========
        has_blacklist, keyword = self._has_blacklist_keyword(question)
        if has_blacklist:
            return False, f"blacklist_keyword:{keyword}", 0.98
        
        # ========== LAYER 2: REGEX PATTERN REJECT ==========
        is_valid_old, reason_old = ContextValidator.is_in_context(question)
        if not is_valid_old and reason_old == "out_of_context_pattern":
            return False, "regex_pattern_reject", 0.95
        
        # ========== LAYER 3: INTENT CLASSIFICATION ==========
        intent, intent_conf = self._check_question_intent(question)
        
        # Reject intents yang jelas out-of-context
        if intent in ['math', 'weather'] and intent_conf > 0.8:
            return False, f"intent_reject:{intent}", intent_conf
        
        # Accept intents yang jelas in-context
        if intent in ['shopping', 'product_inquiry', 'customer_service_help'] and intent_conf > 0.8:
            return True, f"intent_accept:{intent}", intent_conf
        
        # ========== LAYER 3.5: STORE OPERATION CHECK ==========
        # Check jika pertanyaan tentang operasional toko (selalu in-context)
        if self._has_store_operation_context(question):
            return True, "store_operation_inquiry", 0.92
        
        # ========== LAYER 4: AMBIGUOUS KEYWORD CHECK ==========
        is_ambiguous, amb_reason = self._is_ambiguous_keyword_question(question)
        if is_ambiguous:
            # Ambiguous keyword tanpa context produk → reject
            if self.strict_mode:
                return False, amb_reason, 0.85
            # Non-strict: lanjut ke semantic check
        
        # ========== LAYER 5: BRAND/PRODUCT NAME CHECK ==========
        # Jika ada brand name, high chance in-context
        for brand in self.BRAND_NAMES:
            if brand in question.lower():
                # HAPUS aturan yang memblokir pertanyaan "apa itu tokidoki", "dari mana asal labubu", dll.
                # Karena sebagai CS Mainan, kita HARUS BISA menjelaskan apa itu produk kita kepada awam.
                
                wrong_context_words =[
                    'band', 'musik', 'lagu', 'penyanyi', 'restoran',
                    'atlet', 'aktor', 'politikus'
                ]
                if any(word in question.lower() for word in wrong_context_words):
                    return False, f"brand_in_wrong_context:{brand}", 0.90
                
                # Context OK - biarkan pertanyaan tentang brand/karakter masuk
                return True, f"brand_name_match:{brand}", 0.88

        
        # ========== LAYER 6: SEMANTIC VALIDATION ==========
        if self.enable_semantic:
            is_related, confidence, semantic_reason = self.semantic_validator.is_semantically_related(question)
            
            # Semantic validator result
            if is_related and confidence > 0.5:
                return True, f"semantic_accept:{semantic_reason}", confidence
            elif not is_related and confidence > 0.5:
                return False, f"semantic_reject:{semantic_reason}", confidence
            # Else: ambiguous, lanjut ke layer berikutnya
        
        # ========== LAYER 7: KEYWORD FALLBACK ==========
        # Last resort: check IN_CONTEXT_KEYWORDS
        if reason_old == "has_context_keyword":
            # Ada keyword, tapi confidence rendah karena sudah lolos banyak check
            return True, "keyword_fallback", 0.65
        
        # ========== DEFAULT: REJECT (Strict Mode) ==========
        # Untuk customer service, lebih baik reject daripada jawab salah
        if self.strict_mode:
            return False, "strict_mode_default_reject", 0.60
        else:
            # Non-strict: allow untuk safety
            return True, "default_allow", 0.50
    
    @classmethod
    def get_rejection_message(cls, reason: str, question: str = "") -> str:
        """Get appropriate rejection message"""
        return ContextValidator.get_rejection_message(reason, question)
    
    def validate_with_details(self, question: str, verbose: bool = False) -> Dict:
        """
        Validate dengan detail lengkap untuk debugging
        
        Returns:
            Dict dengan semua detail validation
        """
        is_valid, reason, confidence = self.is_in_context(question)
        
        # Collect additional info
        has_blacklist, blacklist_kw = self._has_blacklist_keyword(question)
        has_product_ctx = self._has_product_context(question)
        is_ambiguous, amb_reason = self._is_ambiguous_keyword_question(question)
        intent, intent_conf = self._check_question_intent(question)
        
        result = {
            "question": question,
            "is_valid": is_valid,
            "reason": reason,
            "confidence": confidence,
            "details": {
                "has_blacklist": has_blacklist,
                "blacklist_keyword": blacklist_kw,
                "has_product_context": has_product_ctx,
                "is_ambiguous": is_ambiguous,
                "ambiguous_reason": amb_reason,
                "intent": intent,
                "intent_confidence": intent_conf,
            }
        }
        
        if verbose:
            print("\n" + "=" * 70)
            print("ULTRA VALIDATION DETAILS")
            print("=" * 70)
            print(f"Question: {question}")
            print(f"Decision: {'✅ IN-CONTEXT' if is_valid else '❌ OUT-OF-CONTEXT'}")
            print(f"Confidence: {confidence:.3f}")
            print(f"Reason: {reason}")
            print("\nDetails:")
            print(f"  - Has Blacklist: {has_blacklist} ({blacklist_kw})")
            print(f"  - Has Product Context: {has_product_ctx}")
            print(f"  - Is Ambiguous: {is_ambiguous}")
            print(f"  - Intent: {intent} (conf: {intent_conf:.3f})")
            print("=" * 70)
        
        return result

# ============================================================
# TESTING
# ============================================================

def test_ultra_validator():
    """Test ultra validator dengan test cases comprehensive"""
    
    # Test dengan strict mode
    validator = UltraValidator(enable_semantic=True, strict_mode=True)
    
    test_cases = [
    # ===== IN-CONTEXT CASES =====
    ("Ada koleksi terbaru dari Skullpanda?", True),
    ("Dimoo edisi Halloween ready gak?", True),
    ("Kalo beli satu box isinya random semua kan?", True),
    ("Bisa COD untuk pengiriman di Jakarta?", True),
    ("Seri Hirono yang paling laris yang mana?", True),
    ("Aku cari blind box bertema kucing, ada rekomendasi?", True),
    ("Berapa kisaran harga satuan Molly Sweet Home?", True),
    ("Ada promo kalau beli 3 box sekaligus?", True),
    ("Kalo dapet duplikat bisa tukar gak?", True),
    ("Tokidoki Unicorno masih restock minggu ini?", True),
    ("Mainan ini cocok untuk hadiah ulang tahun anak SMP?", True),
    ("Apa bedanya figure rare dan secret?", True),
    ("Kalian kirim ke luar Jawa juga kan?", True),
    ("Bisa kasih foto real pict sebelum checkout?", True),
    # ("bisa kasih foto barangnya buat molly?", True),
    ("Aku mau hadiahkan ke kolektor pemula, seri apa yang bagus?", True),
    
        # ===== OUT-OF-CONTEXT CASES =====
    ("Cara bikin website e-commerce gimana?", False),
    ("Hari ini ada pertandingan bola apa?", False),
    ("Berapa jarak bumi ke matahari?", False),
    ("Kamu bisa bantu kerjain tugas kimia?", False),
    ("Berita kriminal terbaru dong?", False),
    ("Resep membuat mie ayam pedas?", False),
    ("Berapa umur presiden saat ini?", False),
    ("Cara perhitungan PPN perusahaan?", False),
    ("Kenapa langit berwarna biru?", False),
    ("Film horor terbaik tahun ini apa?", False),
    ("Investasi reksa dana bagus yang mana?", False),
    ("Spesifikasi iPhone terbaru apa saja?", False),
    
        # ===== EDGE CASES (TRICKY!) =====
    ("Tokidoki itu dari anime apa ya?", False),
    ("Harga tiket konser Molly berapa?", False),
    ("Dimoo itu karakter game ya?", False),
    ("Aku mau belajar desain mainan 3D, ada tutorial?", False),
    ("Sweet Bean itu maskot restoran ya?", False),
    ("Skullpanda pemain band metal dari Jepang ya?", False),
    ("Aku mau cari beasiswa kuliah desain karakter", False),


    ]
    
    print("\n" + "=" * 70)
    print("TESTING ULTRA VALIDATOR (STRICT MODE)")
    print("Target Accuracy: 90-97%")
    print("=" * 70)
    
    correct = 0
    total = len(test_cases)
    false_positives = []
    false_negatives = []
    
    for question, expected in test_cases:
        result = validator.validate_with_details(question, verbose=False)
        is_valid = result["is_valid"]
        reason = result["reason"]
        confidence = result["confidence"]
        
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
    print(f"🎯 ACCURACY: {correct}/{total} ({accuracy:.1f}%)")
    print("=" * 70)
    
    if false_positives:
        print(f"\n⚠️ FALSE POSITIVES: {len(false_positives)} (Seharusnya reject tapi lolos)")
        for q, r, c in false_positives:
            print(f"   - {q}")
            print(f"     Reason: {r} | Conf: {c:.3f}")
    
    if false_negatives:
        print(f"\n⚠️ FALSE NEGATIVES: {len(false_negatives)} (Seharusnya lolos tapi ditolak)")
        for q, r, c in false_negatives:
            print(f"   - {q}")
            print(f"     Reason: {r} | Conf: {c:.3f}")
    
    print("\n" + "=" * 70)
    
    # Performance summary
    fp_rate = (len(false_positives) / total) * 100
    fn_rate = (len(false_negatives) / total) * 100
    
    print("📊 PERFORMANCE METRICS:")
    print(f"   Accuracy:        {accuracy:.1f}%")
    print(f"   False Positive:  {fp_rate:.1f}% ({len(false_positives)} cases)")
    print(f"   False Negative:  {fn_rate:.1f}% ({len(false_negatives)} cases)")
    print("=" * 70)
    
    # Rating
    if accuracy >= 95:
        rating = "🏆 EXCELLENT"
    elif accuracy >= 90:
        rating = "🥇 VERY GOOD"
    elif accuracy >= 85:
        rating = "🥈 GOOD"
    elif accuracy >= 80:
        rating = "🥉 FAIR"
    else:
        rating = "⚠️ NEEDS IMPROVEMENT"
    
    print(f"\n{rating}")
    print("=" * 70)


if __name__ == "__main__":
    test_ultra_validator()
