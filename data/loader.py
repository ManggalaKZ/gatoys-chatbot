# Di dalam file data/loader.py

from typing import List, Dict
from supabase import create_client, Client
import traceback

def load_products_from_supabase(supabase_url: str, supabase_key: str) -> List[Dict]:
    """
    Load product data dari Supabase dengan Skema Baru
    """
    print("\n[DATA] Loading products from Supabase...")
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Query tabel products (skema baru: digabung dan pakai is_active)
        response = supabase.table('products') \
            .select("""
                id,
                title,
                sku,
                price,
                weight,
                is_active,
                desc,
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
            return[]
        
        products =[]
        for item in response.data:
            # Mapping schema DB baru ke format dictionary yang dibutuhkan Chatbot
            product = {
                'product_id': item['id'],           # id -> product_id
                'name': item['title'],              # title -> name
                'sku': item.get('sku', ''),
                'price': item['price'],
                'weight': item.get('weight', 0),
                'status': 'active' if item.get('is_active') else 'inactive',
                'category_name': _extract_category(item),
                
                # Detail yang sekarang menyatu di tabel products
                'description': item.get('desc'),    # desc -> description
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

def _extract_category(item: Dict) -> str:
    categories = item.get('categories')
    if isinstance(categories, list):
        return categories[0]['name'] if categories else 'Uncategorized'
    elif categories:
        return categories.get('name', 'Uncategorized')
    return 'Uncategorized'