"""
Document Builder for RAG
Transform products into LangChain documents with rich content
"""

from typing import List, Dict
from langchain.docstore.document import Document

def build_product_documents(products: List[Dict]) -> List[Document]:
    """
    Build rich documents dari product data
    Format natural language untuk better embedding & retrieval
    
    Args:
        products: List of product dictionaries
        
    Returns:
        List of LangChain Document objects
    """
    print(f"\n[BUILDER] Building documents from {len(products)} products...")
    
    docs = []
    
    for product in products:
        # Format harga
        price_idr = f"Rp {product['price']:,}".replace(',', '.')
        
        # Build natural language content
        content = _build_product_content(product, price_idr)
        
        # Metadata untuk filtering & ranking
        metadata = {
            "product_id": product['product_id'],
            "name": product['name'],
            "sku": product['sku'],
            "price": product['price'],
            "category": product['category_name'],
            "series": product.get('series', ''),
            "type": "product",
            "age_recommendation": product.get('age_recommendation', '')
        }
        
        docs.append(Document(
            page_content=content,
            metadata=metadata
        ))
    
    print(f"[SUCCESS] Built {len(docs)} product documents")
    return docs

def _build_product_content(product: Dict, price_idr: str) -> str:
    """
    Build natural language content dengan FAQ-style
    
    Args:
        product: Product dictionary
        price_idr: Formatted price string
        
    Returns:
        Natural language content string
    """
    # Main content parts
    content_parts = [
        f"=== {product['name']} ===",
        f"Kategori: {product['category_name']}",
        f"SKU: {product['sku']}",
        f"Harga: {price_idr}",
         "",
        "DESKRIPSI:",
        product.get('desc') if product.get('desc') else 'Tidak ada deskripsi.',
        "",
        "LORE / CERITA KARAKTER:",                                     
        product.get('lore') if product.get('lore') else 'Tidak ada lore.', 
        "",
        "EXTRA_INFO / CERITA KARAKTER:",                                    
        product.get('extra_info') if product.get('extra_info') else 'Tidak ada informasi tambahan.', 
        "",
        "DETAIL PRODUK:",
        f"- Material: {product.get('material') or 'N/A'}",
        f"- Ukuran: {product.get('size') or 'N/A'}",
        f"- Rekomendasi Umur: {product.get('age_recommendation') or 'N/A'}",
        f"- Series: {product.get('series') or 'N/A'}",
        f"- Asal: {product.get('origin') or 'N/A'}",
        f"- Berat: {product['weight']} gram",
        "",
    ]
    
    # Extra info jika ada
    if product.get('extra_info'):
        content_parts.extend([
            "INFORMASI TAMBAHAN:",
            product['extra_info'],
            ""
        ])
    
    # FAQ-style questions untuk better retrieval
    faq_parts = [
        "PERTANYAAN UMUM:",
        f"Q: Berapa harga {product['name']}?",
        f"A: {price_idr}",
        "",
        f"Q: {product['name']} terbuat dari apa?",
        f"A: {product.get('material') or 'Material tidak dispesifikasikan'}",
        "",
        f"Q: Berapa ukuran {product['name']}?",
        f"A: {product.get('size') or 'Ukuran tidak dispesifikasikan'}",
        "",
        f"Q: {product['name']} cocok untuk umur berapa?",
        f"A: Rekomendasi umur {product.get('age_recommendation') or 'tidak dispesifikasikan'}",
    ]
    
    # Combine all parts
    return "\n".join(content_parts + faq_parts)