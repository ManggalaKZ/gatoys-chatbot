"""
Query Classifier
Classify user queries into types
"""

# from .validator import ContextValidator
from .ultra_validator import UltraValidator

# Singleton validator instance for classifier
_validator_instance = None

def _get_validator():
    """Get or create singleton validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = UltraValidator(enable_semantic=False, strict_mode=True)
    return _validator_instance

def classify_query(question: str) -> str:
    """
    Classify user query into types untuk metrics
    """
    q = question.lower()

    # Check if out of context first
    validator = _get_validator()
    is_valid, reason, _ = validator.is_in_context(question)
    if not is_valid:
        return 'out_of_context'

    # Product inquiry (harga, ukuran, detail)
    if any(word in q for word in ['harga', 'price', 'berapa', 'ukuran', 'size', 'material', 'berat', 'weight']):
        return 'product_inquiry'

    # Product search / availability
    if any(word in q for word in ['ada', 'punya', 'tersedia', 'stock', 'stok', 'jual', 'ready']):
        return 'product_search'

    # Recommendation / preference-based
    if any(word in q for word in ['rekomendasi', 'rekomendasikan', 'saran', 'sarankan', 'lucu', 'gemes', 'cocok', 'bagus', 'recommend', 'unik']):
        return 'recommendation'

    # Store policy / transaction
    if any(word in q for word in ['beli', 'bayar', 'kirim', 'return', 'garansi', 'refund', 'cara', 'ongkir', 'pembayaran', 'pengiriman']):
        return 'store_policy'

    # Blind box
    if 'blind box' in q or 'random' in q:
        return 'blind_box_info'

    # Brand-specific queries
    if any(word in q for word in ['tokidoki', 'molly', 'dimoo', 'skullpanda', 'pucky', 'hirono', 'labubu', 'bunny', 'sweet bean']):
        return 'product_search'

    # General inside business scope
    return 'general'