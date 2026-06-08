import os
import random
import time
from datetime import datetime
from typing import List, Dict
from decimal import Decimal
from zoneinfo import ZoneInfo # Python 3.9+
from faker import Faker
from supabase import create_client, Client
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Pastikan file .env sudah diisi SUPABASE_URL dan SUPABASE_KEY")
    exit()

# Init Supabase & Faker
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
fake = Faker(['id_ID', 'en_US'])

# ============================================================
# KONFIGURASI TARGET
# ============================================================
TARGET_CATEGORIES = ['Action Figures', 'Blind Box', 'Accessories']
TOTAL_PRODUCTS = 20  # Sesuai request

# Data Statis untuk Variasi
BRANDS = ['Pop Mart', 'Bandai', 'Good Smile', 'Kotobukiya', 'Hot Toys']
SERIES_LIST = ['The Monsters', 'Skullpanda', 'Dimoo', 'Gundam Witch', 'One Piece']
MATERIALS = ['PVC', 'ABS', 'Vinyl', 'Resin']

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def simple_slugify(text):
    """Membuat slug ala Laravel (lowercase & dash)"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

def get_or_create_categories():
    """Memastikan Kategori Utama ada dan mengambil ID-nya"""
    print("[1/3] Mempersiapkan Kategori...")
    
    cat_map = {} # Simpan nama: id
    
    # 1. Cek yang sudah ada
    existing = supabase.table('categories').select('*').execute()
    for row in existing.data:
        cat_map[row['name']] = row['id']
        
    # 2. Buat yang belum ada
    for target in TARGET_CATEGORIES:
        if target not in cat_map:
            print(f"   -> Membuat kategori baru: {target}")
            
            # Insert menggunakan skema terbaru: name, description, dan path
            res = supabase.table('categories').insert({
                'name': target,
                'description': f"Deskripsi default untuk {target}", # Deskripsi default
                'path': 'test' # Path diisi 'test' semua
            }).execute()
            
            # Ambil ID dari hasil insert
            if res.data:
                cat_map[target] = res.data[0]['id']
            
    print(f"   ✓ Kategori siap: {cat_map}")
    return cat_map

def generate_single_product(index, cat_name, cat_id):
    """Generate 1 baris data produk LENGKAP (Merged Schema)"""
    
    brand = random.choice(BRANDS)
    series = random.choice(SERIES_LIST)
    
    # Nama Produk
    if cat_name == 'Blind Box':
        name = f"{brand} {series} Series - Blind Box"
        price = random.choice([159000, 189000, 219000])
        probability = round(random.uniform(0.5, 5.0), 2) # Ada probability
        lore = fake.paragraph(nb_sentences=5) # Lore panjang
    elif cat_name == 'Action Figures':
        name = f"{brand} {series} Action Figure Vol.{index}"
        price = random.choice([450000, 850000, 1200000])
        probability = None
        lore = fake.paragraph(nb_sentences=3)
    else: # Accessories
        name = f"{series} Display Case / Stand Base"
        price = random.choice([50000, 75000, 120000])
        probability = None
        lore = "Aksesoris pelengkap koleksi."

    # Tambah random number biar nama & slug unik
    name = f"{name} #{index}"
    slug = simple_slugify(name)
    
    # URL Gambar Dummy (Placeholder)
    image_url = f"https://placehold.co/600x600/png?text={name.replace(' ', '+')}"

    return {
        # --- Kolom Laravel Standard ---
        'name': name,
        'slug': slug,
        'image': image_url, # Masukkan path/url gambar dummy
        'price': price,
        'quantity': random.randint(5, 50),
        'is_active': True,
        'category_id': cat_id,
        
        # --- Kolom Chatbot / Blind Box (Merged) ---
        'sku': f"SKU-{cat_name[0:2].upper()}-{index:04d}",
        'series': series if cat_name != 'Accessories' else None,
        'weight': round(random.uniform(0.1, 0.8), 2),
        'description': fake.text(max_nb_chars=150),
        'lore': lore,
        'material': random.choice(MATERIALS),
        'size': f"{random.randint(5, 20)} cm",
        'age_recommendation': "15+",
        'origin': "China",
        'extra_info': "Box sealed, original product.",
        'probability': probability,
        
        # Timestamp
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }

# ============================================================
# MAIN EXECUTION
# ============================================================
def main():
    print(f"--- GENERATOR DATA DUMMY GA-TOYS ({TOTAL_PRODUCTS} Items) ---")
    
    # 1. Siapkan Kategori
    categories = get_or_create_categories()
    
    # 2. Generate Data Produk
    print(f"[2/3] Generating {TOTAL_PRODUCTS} produk...")
    products_batch = []
    
    for i in range(1, TOTAL_PRODUCTS + 1):
        # Distribusi Kategori: Blind Box (50%), Figure (30%), Accs (20%)
        rand = random.random()
        if rand < 0.5:
            target_cat = 'Blind Box'
        elif rand < 0.8:
            target_cat = 'Action Figures'
        else:
            target_cat = 'Accessories'
            
        product_data = generate_single_product(i, target_cat, categories[target_cat])
        products_batch.append(product_data)
    
    # 3. Insert ke Supabase
    print(f"[3/3] Uploading ke Supabase...")
    try:
        # Insert ke tabel 'products'
        res = supabase.table('products').insert(products_batch).execute()
        print(f"✅ SUKSES! {len(res.data)} data berhasil ditambahkan.")
        print("   Silakan cek Dashboard Admin Laravel Anda.")
        
    except Exception as e:
        print(f"❌ GAGAL: {e}")

if __name__ == "__main__":
    main()