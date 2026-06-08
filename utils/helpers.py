
# ============================================================
# PRODUCT DATA LOADER
# ============================================================

from typing import List, Dict
from supabase import create_client, Client
from langchain.docstore.document import Document
import re
import time
import json
import traceback
from datetime import datetime
from data.store_info import build_store_info_documents



# Config & Constants
from core.config import (
    GEMINI_MODEL,
    GEMINI_API_KEY,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    FAISS_INDEX_PATH,
    AUTO_REFRESH_ENABLED,
    REFRESH_INTERVAL_MINUTES,
    RETRIEVAL_TOP_K,
    METRICS_ENABLED,
    METRICS_FILE,
    SHOW_RETRIEVED_DOCS,
    SHOW_CONFIDENCE_SCORE,
    VERBOSE_MODE
)

# Pastikan kamu sudah punya ini di config.py
from core.config import SUPABASE_URL, SUPABASE_KEY
_supabase_instance = None

def get_supabase_client():
    """
    Singleton pattern untuk mendapatkan Supabase Client
    """
    global _supabase_instance
    
    if _supabase_instance is None:
        try:
            _supabase_instance = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"[FATAL] Failed to connect to Supabase: {e}")
            raise e
            
    return _supabase_instance


def save_chat_log(user_id, session_id, question, answer, query_type, confidence, response_time):
    """Simpan satu interaksi chat ke tabel chat_logs di Supabase (untuk data UAT & audit)."""
    try:
        supabase = get_supabase_client()
        supabase.table('chat_logs').insert({
            'user_id': str(user_id) if user_id not in (None, '') else None,
            'session_id': session_id,
            'question': question,
            'answer': answer,
            'query_type': query_type,
            'confidence': float(confidence) if confidence is not None else None,
            'response_time': float(response_time) if response_time is not None else None,
        }).execute()
    except Exception as e:
        print(f"[CHAT_LOG] Gagal menyimpan chat log: {e}")


def load_products_from_db() -> List[Dict]:
    """
    Load product data dari Supabase
    """
    print("\n[STEP] Loading product data from Supabase...")
    
    try:
        supabase = get_supabase_client()
        
        # Query products dengan skema baru
        response = supabase.table('products') \
            .select("""
                id,
                title,
                sku,
                price,
                stock,
                weight,
                is_active,
                desc,
                lore,
                probability,
                material,
                size,
                age_recommendation,
                series,
                origin,
                extra_info,
                categories!inner(name)
            """) \
            .eq('is_active', True) \
            .order('id') \
            .execute()
        
        if not response.data:
            print("[WARN] No products found in Supabase")
            return []
        
        products =[]
        for item in response.data:
            product = {
                'product_id': item['id'],
                'name': item['title'],
                'sku': item.get('sku', ''),
                'price': item['price'],
                'stock': item.get('stock', 0),
                'weight': item.get('weight', 0),
                'status': 'active' if item.get('is_active') else 'inactive',
                'category_name': (
                    item['categories'][0]['name'] if isinstance(item.get('categories'), list)
                    else item['categories']['name'] if item.get('categories')
                    else 'Uncategorized'
                ),
                'description': item.get('desc'),
                'lore': item.get('lore'),
                'probability': item.get('probability'),
                'material': item.get('material'),
                'size': item.get('size'),
                'age_recommendation': item.get('age_recommendation'),
                'series': item.get('series'),
                'origin': item.get('origin'),
                'extra_info': item.get('extra_info')
            }
            products.append(product)
        
        print(f"[SUCCESS] Loaded {len(products)} products from Supabase")
        return products
        
    except Exception as e:
        print(f"[ERROR] Failed to load products from Supabase: {e}")
        traceback.print_exc()
        return[]


# ============================================================
# DOCUMENT BUILDER
# ============================================================

def build_product_documents(products: List[Dict]) -> List[Document]:
    """
    Build rich documents dari product data
    Format natural untuk better embedding & retrieval
    """
    print("\n[STEP] Building product documents for RAG...")
    
    docs = []
    
    for product in products:
        # Format harga (bulatkan ke rupiah penuh, hindari .0 di belakang)
        price_idr = f"Rp {int(product['price']):,}".replace(',', '.')
        
        # Hitung info stok, peluang varian secret, dan lore
        stock = product.get('stock')
        if stock is None:
            stock_text = "Informasi stok tidak tersedia."
            stock_line = "- Stok: tidak diketahui"
        else:
            status = "Tersedia" if stock > 0 else "Stok habis"
            stock_text = f"Stok saat ini {stock} unit ({status})."
            stock_line = f"- Stok: {stock} unit ({status})"

        prob = product.get('probability')
        try:
            prob = float(prob) if prob is not None else None
        except (ValueError, TypeError):
            prob = None
        if prob and prob > 0:
            prob_text = (
                f"Peluang mendapatkan varian Secret (rahasia) sekitar {prob * 100:.2f}% "
                f"(kurang lebih 1 dari {round(1 / prob)} box)."
            )
        else:
            prob_text = "Informasi peluang varian Secret tidak tersedia."

        lore_text = product['lore'] if product.get('lore') else "Tidak ada informasi lore."

        # Build natural language document
        content_parts = [
            f"=== {product['name']} ===",
            f"Kategori: {product['category_name']}",
            f"SKU: {product['sku']}",
            f"Harga: {price_idr}",
            f"Status Stok: {stock_text}",
            "",
            "DESKRIPSI:",
            product['description'] if product['description'] else "Tidak ada deskripsi.",
            "",
            "LORE / CERITA KARAKTER:",
            lore_text,
            "",
            "PELUANG / PROBABILITAS VARIAN SECRET:",
            prob_text,
            "",
            "KETERSEDIAAN STOK:",
            stock_line,
            "",
            "DETAIL PRODUK:",
            f"- Material: {product['material'] or 'N/A'}",
            f"- Ukuran: {product['size'] or 'N/A'}",
            f"- Rekomendasi Umur: {product['age_recommendation'] or 'N/A'}",
            f"- Series: {product['series'] or 'N/A'}",
            f"- Asal: {product['origin'] or 'N/A'}",
            f"- Berat: {int(product['weight'])} gram",
            "",
        ]
        
        if product['extra_info']:
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
            f"A: {product['material'] or 'Material tidak dispesifikasikan'}",
            "",
            f"Q: Berapa ukuran {product['name']}?",
            f"A: {product['size'] or 'Ukuran tidak dispesifikasikan'}",
            "",
            f"Q: {product['name']} cocok untuk umur berapa?",
            f"A: Rekomendasi umur {product['age_recommendation'] or 'tidak dispesifikasikan'}",
            "",
            f"Q: Bagaimana cerita atau lore {product['name']}?",
            f"A: {lore_text}",
            "",
            f"Q: Berapa peluang mendapatkan varian secret/rahasia {product['name']}?",
            f"A: {prob_text}",
            "",
            f"Q: Apakah stok {product['name']} masih tersedia?",
            f"A: {stock_text}",
        ]
        
        # Combine all parts
        full_content = "\n".join(content_parts + faq_parts)
        
        # Metadata untuk filtering & ranking
        metadata = {
            "product_id": product['product_id'],
            "name": product['name'],
            "sku": product['sku'],
            "price": product['price'],
            "stock": stock if stock is not None else 0,
            "probability": prob,
            "category": product['category_name'],
            "series": product['series'] or "",
            "type": "product",
            "age_recommendation": product['age_recommendation'] or ""
        }
        
        docs.append(Document(
            page_content=full_content,
            metadata=metadata
        ))
    
    # Add general store info documents
    store_docs = build_store_info_documents()
    docs.extend(store_docs)
    
    print(f"[SUCCESS] Built {len(docs)} documents ({len(products)} products + {len(store_docs)} store info)")
    return docs


