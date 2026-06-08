"""
Context Validator
Validate if questions are within chatbot scope
"""

import re
from typing import Tuple

class ContextValidator:
    """Validate query context"""
    
    # Define in-context keywords
    IN_CONTEXT_KEYWORDS = {
        # Product related
        'saran', 'sarankan',
        'produk', 'mainan', 'figurine', 'blind box', 'harga', 'price', 
        'jual', 'beli', 'stock', 'tersedia', 'ada',
        'rekomendasi', 'lucu', 'gemes', 'unik',
        'cocok', 'bagus', 'recommend', 'koleksi', 'collectible',
        'limited edition', 'edisi terbatas', 'original', 'import',
        
        # Brands/Series
        'tokidoki', 'molly', 'dimoo', 'skullpanda', 'pucky', 'hirono',
        'labubu', 'bunny', 'sweet bean',
        
        # Store operations
        'toko', 'shop', 'ga toys', 'pembayaran', 'pengiriman', 'ongkir',
        'return', 'garansi', 'bayar', 'kirim', 'pesan', 'order',
        
        # Product attributes
        'ukuran', 'size', 'material', 'bahan', 'umur', 'rekomendasi',
        'kategori', 'series', 'asal', 'origin', 'berat', 'weight',
        
        # Customer service
        'cara', 'bagaimana', 'kapan', 'dimana', 'berapa lama',
        'kebijakan', 'syarat', 'ketentuan',
        'informasi', 'info', 'detail', 'deskripsi', 'faq'
    }
    
    # Out-of-context patterns
    OUT_OF_CONTEXT_PATTERNS = [
        # Math/calculation
        r'\d+\s*[\+\-\*\/xX×]\s*\d+',  # 5+5, 5x5, 10-3, etc.
        r'berapa\s+\d+\s*[\+\-\*\/xX×]',
        r'hitung',
        r'hasil\s+(dari\s+)?\d+',
        r'\d+\s+[\+\-\*xX×]\s+\d+',  # "5 x 5"
        r'setelah\s+\d+\s+angka',  # "setelah 5 angka berapa"
        
        # Weather
        r'cuaca',
        r'hujan',
        r'panas\s+(hari\s+ini|sekarang|di)',
        r'dingin\s+(hari\s+ini|sekarang|di)',
        r'temperatur',
        r'suhu\s+(hari\s+ini|sekarang|di)',
        
        # News/current events
        r'berita',
        r'news',
        r'terkini',
        
        # General knowledge
        r'siapa\s+presiden',
        r'ibukota',
        r'capital',
        r'negara\s+',
        r'sejarah(?!\s+(toko|ga\s+toys))',  # "sejarah" OK if about store
        
        # Time/date (non-shopping related)
        r'jam\s+berapa',
        r'tanggal\s+berapa',
        r'hari\s+ini\s+(tanggal|hari)',
        
        # Technology/programming
        r'cara\s+coding',
        r'program\s+(python|java|javascript)',
        r'html',
        r'css',
        
        # Inappropriate
        r'politik',
        r'agama',
    ]
    
    @classmethod
    def is_in_context(cls, question: str) -> Tuple[bool, str]:
        """
        Check if question is in context
        
        Args:
            question: User's question
            
        Returns:
            Tuple of (is_valid, reason)
        """
        q_lower = question.lower()
        
        # Check out-of-context patterns (REJECT first)
        for pattern in cls.OUT_OF_CONTEXT_PATTERNS:
            if re.search(pattern, q_lower):
                return False, "out_of_context_pattern"
        
        # Check length
        if len(question.strip()) < 3:
            return False, "too_short"
        
        # Check keywords
        has_keyword = any(kw in q_lower for kw in cls.IN_CONTEXT_KEYWORDS)
        if has_keyword:
            return True, "has_context_keyword"
        
        # Question words without context
        question_words = ['apa', 'siapa', 'dimana', 'kapan']
        if any(w in q_lower for w in question_words) and not has_keyword:
            return False, "general_question"
        
        return True, "default_allow"
    
    @classmethod
    def get_rejection_message(cls, reason: str, question: str = "") -> str:
        """
        Get rejection message based on reason
        
        Args:
            reason: Rejection reason
            question: Original question (optional, for context)
            
        Returns:
            Rejection message string
        """
        
        if reason == "out_of_context_pattern":
            return """Maaf, pertanyaan Anda di luar konteks layanan kami. 

Saya adalah customer service assistant untuk GA Toys, toko mainan koleksi figurine import. 

Saya dapat membantu Anda dengan:
✓ Informasi produk mainan (harga, ukuran, material, dll)
✓ Rekomendasi mainan sesuai usia/preferensi
✓ Cara pembelian dan pembayaran
✓ Kebijakan pengiriman, return, dan garansi
✓ Informasi tentang blind box

Silakan tanyakan sesuatu tentang produk atau layanan kami! 😊"""

        elif reason == "general_question":
            return """Maaf, saya hanya bisa menjawab pertanyaan seputar produk dan layanan GA Toys.

Contoh pertanyaan yang bisa saya bantu:
• "Ada mainan Molly?"
• "Berapa harga Tokidoki Cactus Buddy?"
• "Rekomendasi mainan untuk usia 13 tahun?"
• "Bagaimana cara membeli?"
• "Apa itu blind box?"

Silakan tanyakan tentang mainan koleksi kami! 🎮"""

        elif reason == "too_short":
            return """Maaf, pertanyaan Anda terlalu pendek.

Saya adalah CS assistant GA Toys yang khusus membantu informasi seputar:
✓ Produk mainan koleksi
✓ Harga dan spesifikasi
✓ Cara pembelian
✓ Pengiriman & return

Bisa Anda perjelas pertanyaannya? 😊"""
        
        else:
            # Default message
            return """Maaf, saya tidak mengerti pertanyaan Anda.

Saya adalah CS assistant GA Toys yang khusus membantu informasi seputar:
✓ Produk mainan koleksi figurine
✓ Harga dan spesifikasi produk
✓ Cara pembelian dan pembayaran
✓ Pengiriman dan kebijakan return

Silakan tanyakan sesuatu tentang produk kami! 😊"""