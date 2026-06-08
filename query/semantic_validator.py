"""
Semantic Validator
Validasi pertanyaan menggunakan embedding similarity
Lebih akurat dari keyword matching
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from functools import lru_cache
from typing import Tuple
from core.singleton import get_embedding_model


class SemanticValidator:
    """
    Validasi semantic dengan embedding
    Menggunakan cosine similarity untuk cek relevansi pertanyaan
    """
    
    # Business scope description (semakin detail, semakin akurat)
    BUSINESS_SCOPE = """
    GA Toys adalah toko online spesialis mainan koleksi figurine import.
    Kami menjual blind box series, collectible toys, dan figurine karakter populer
    seperti Tokidoki, Molly, LABUBU, PUCKY, Dimoo, Skullpanda, Hirono, Sweet Bean.
    
    Produk kami meliputi:
    - Blind box series dengan karakter acak
    - Limited edition collectibles
    - Figurine PVC import original dari China
    - Mainan koleksi untuk remaja dan dewasa (13+)
    
    Layanan dan informasi yang kami berikan:
    - Informasi produk mainan: harga, ukuran, material, series
    - Rekomendasi mainan sesuai usia dan preferensi
    - Cara pembelian dan metode pembayaran
    - Informasi pengiriman dan estimasi waktu
    - Kebijakan return dan garansi produk
    - Penjelasan tentang blind box system
    - FAQ tentang produk dan toko
    - Promo dan diskon yang sedang berlangsung
    
    Kami TIDAK melayani pertanyaan tentang:
    - Cuaca, berita, politik, agama
    - Matematika, perhitungan, rumus
    - Teknologi, programming, coding
    - Keuangan, saham, cryptocurrency
    - Topik di luar produk dan layanan toko mainan
    """
    
    # Contoh out-of-scope untuk kontras
    OUT_OF_SCOPE_EXAMPLES = """
    Contoh pertanyaan yang TIDAK kami layani:
    - Cuaca hari ini bagaimana?
    - Berapa 5 + 5?
    - Cara coding Python?
    - Harga bitcoin sekarang?
    - Berita politik terkini?
    - Resep masakan?
    - Cara install software?
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize semantic validator
        
        Args:
            model_name: Nama model embedding (default: multilingual MiniLM)
        """
        self.embedding_wrapper = get_embedding_model()
        self.model = self.embedding_wrapper.client # Access underlying sentence-transformer
    
    @property
    def scope_embedding(self):
        """Lazy load scope embedding"""
        if self._scope_embedding is None:
            print("[SEMANTIC VALIDATOR] Computing business scope embedding...")
            self._scope_embedding = self.model.encode([self.BUSINESS_SCOPE])[0]
        return self._scope_embedding
    
    @property
    def out_of_scope_embedding(self):
        """Lazy load out-of-scope embedding"""
        if self._out_of_scope_embedding is None:
            self._out_of_scope_embedding = self.model.encode([self.OUT_OF_SCOPE_EXAMPLES])[0]
        return self._out_of_scope_embedding
    
    def calculate_similarity(self, question: str) -> Tuple[float, float]:
        """
        Calculate similarity scores
        
        Args:
            question: User question
            
        Returns:
            (in_scope_similarity, out_of_scope_similarity)
        """
        # Embed question
        question_embedding = self.model.encode([question])[0]
        
        # Calculate cosine similarity dengan in-scope
        in_scope_sim = cosine_similarity(
            [question_embedding],
            [self.scope_embedding]
        )[0][0]
        
        # Calculate cosine similarity dengan out-of-scope
        out_of_scope_sim = cosine_similarity(
            [question_embedding],
            [self.out_of_scope_embedding]
        )[0][0]
        
        return float(in_scope_sim), float(out_of_scope_sim)
    
    def is_semantically_related(
        self, 
        question: str, 
        in_scope_threshold: float = 0.35,
        out_of_scope_threshold: float = 0.25
    ) -> Tuple[bool, float, str]:
        """
        Cek apakah question semantically related dengan business scope
        
        Args:
            question: User question
            in_scope_threshold: Minimum similarity untuk dianggap in-scope (0.0-1.0)
            out_of_scope_threshold: Maximum similarity dengan out-of-scope examples
            
        Returns:
            (is_related, confidence, reason)
            
        Strategy:
            - Jika similarity dengan in_scope TINGGI → IN-SCOPE
            - Jika similarity dengan out_of_scope TINGGI → OUT-OF-SCOPE
            - Jika keduanya rendah → DEFAULT ALLOW (safer)
        """
        in_sim, out_sim = self.calculate_similarity(question)
        
        # Decision logic dengan prioritas yang lebih ketat
        
        # Priority 1: Jelas out-of-scope (similarity tinggi dengan out-of-scope)
        if out_sim > out_of_scope_threshold:
            return False, float(out_sim), f"high_similarity_to_out_of_scope ({out_sim:.3f})"
        
        # Priority 2: Jelas in-scope (similarity tinggi dengan in-scope)
        if in_sim >= in_scope_threshold:
            return True, float(in_sim), f"semantically_related ({in_sim:.3f})"
        
        # Priority 3: Delta check - bandingkan mana lebih tinggi
        delta = in_sim - out_sim
        if delta > 0.15:  # In-scope jauh lebih tinggi
            return True, float(in_sim), f"delta_favor_in_scope (delta:{delta:.3f})"
        elif delta < -0.10:  # Out-scope lebih tinggi
            return False, float(out_sim), f"delta_favor_out_scope (delta:{delta:.3f})"
        
        # Priority 4: Ambiguous cases - default REJECT (lebih aman)
        # Untuk customer service, lebih baik reject daripada jawab salah
        return False, 0.3, f"ambiguous_reject (in:{in_sim:.3f}, out:{out_sim:.3f}, delta:{delta:.3f})"
    
    def validate_with_details(self, question: str, verbose: bool = False) -> dict:
        """
        Validasi dengan detail lengkap (untuk debugging/analysis)
        
        Args:
            question: User question
            verbose: Print detail ke console
            
        Returns:
            Dict dengan detail validasi
        """
        is_related, confidence, reason = self.is_semantically_related(question)
        in_sim, out_sim = self.calculate_similarity(question)
        
        result = {
            "question": question,
            "is_valid": is_related,
            "confidence": confidence,
            "reason": reason,
            "in_scope_similarity": in_sim,
            "out_of_scope_similarity": out_sim,
            "delta": in_sim - out_sim  # Positive = lebih in-scope
        }
        
        if verbose:
            print("\n" + "=" * 60)
            print("SEMANTIC VALIDATION DETAILS")
            print("=" * 60)
            print(f"Question: {question}")
            print(f"In-Scope Similarity: {in_sim:.4f}")
            print(f"Out-Scope Similarity: {out_sim:.4f}")
            print(f"Delta (In - Out): {result['delta']:.4f}")
            print(f"Decision: {'✅ IN-SCOPE' if is_related else '❌ OUT-OF-SCOPE'}")
            print(f"Confidence: {confidence:.4f}")
            print(f"Reason: {reason}")
            print("=" * 60)
        
        return result


# ============================================================
# TESTING & VALIDATION
# ============================================================

def test_semantic_validator():
    """Test semantic validator dengan berbagai contoh"""
    
    validator = SemanticValidator()
    
    test_cases = [
        # IN-SCOPE cases
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
        
        # OUT-OF-SCOPE cases
        ("Cuaca hari ini bagaimana?", False),
        ("Berapa 5 + 5?", False),
        ("Cara coding Python?", False),
        ("Harga bitcoin sekarang?", False),
        ("Berita politik terkini?", False),
        ("Resep ayam goreng?", False),
        ("Siapa presiden Indonesia?", False),
        ("Cara install Windows?", False),
        
        # EDGE cases (yang mungkin salah di sistem lama)
        ("Tokidoki adalah nama band rock?", False),  # Konteks musik, bukan produk
        ("Harga emas hari ini naik?", False),  # 'harga' tapi konteks finance
        ("Ada cara membuat kue coklat?", False),  # 'ada' + 'cara' tapi cooking
    ]
    
    print("\n" + "=" * 70)
    print("TESTING SEMANTIC VALIDATOR")
    print("=" * 70)
    
    correct = 0
    total = len(test_cases)
    
    for question, expected in test_cases:
        result = validator.validate_with_details(question, verbose=False)
        is_correct = result["is_valid"] == expected
        correct += is_correct
        
        status = "✅" if is_correct else "❌"
        print(f"{status} {question}")
        print(f"   Expected: {expected} | Got: {result['is_valid']} | Conf: {result['confidence']:.3f}")
        print(f"   In-Sim: {result['in_scope_similarity']:.3f} | Out-Sim: {result['out_of_scope_similarity']:.3f}")
        print()
    
    accuracy = (correct / total) * 100
    print("=" * 70)
    print(f"ACCURACY: {correct}/{total} ({accuracy:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    # Run test
    test_semantic_validator()
