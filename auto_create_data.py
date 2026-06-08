"""
generate_test_data.py - Bulk Data Generator untuk Testing

Generate ribuan data mainan realistis ke Supabase
Exact match dengan struktur tabel products & product_details

Requirements:
    pip install faker supabase python-dotenv

Usage:
    python generate_test_data.py --count 1000
    python generate_test_data.py --count 5000 --batch-size 100
    python generate_test_data.py --stats
    python generate_test_data.py --clear
"""

import random
import argparse
from datetime import datetime
from typing import List, Dict
from decimal import Decimal
from zoneinfo import ZoneInfo
from faker import Faker
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import time

# Load environment
load_dotenv()

# Supabase config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Faker
fake = Faker(['id_ID', 'en_US'])  # Indonesian & English

# ============================================================
# DATA TEMPLATES - REALISTIC TOY DATA
# ============================================================

# Brand/Series yang realistis untuk toko mainan koleksi (EXPANDED - 40+ brands)
BRANDS = [
    'Tokidoki', 'Molly', 'LABUBU', 'PUCKY', 'Dimoo', 
    'Skullpanda', 'Hirono', 'Sweet Bean', 'The Monsters',
    'Crybaby', 'Zimomo', 'Satyr Rory', 'Have a Seat',
    'Skull Panda', 'Pop Mart', 'Kennyswork', 'Instinctoy',
    'Fluffy House', 'Bean Sprout', 'Azura', 'Hacipupu',
    'Yuki', 'Penny', 'The Monsters', 'Baby Three', 'Kasing Lung',
    'Buzz', 'Panda Roll', 'Little Amber', 'Cosmo', 'Vivi Cat',
    'Cookie', 'Bunny', 'Seulgi', 'Fortune Cat', 'Miffy',
    'Snoopy', 'Hello Kitty', 'Kuromi', 'My Melody', 'Cinnamoroll',
    'Little Twin Stars', 'Pompompurin', 'Badtz-Maru', 'Keroppi'
]

# Series variations (EXPANDED - 50+ variations)
SERIES_TEMPLATES = [
    '{brand} Career Series',
    '{brand} Zodiac Series',
    '{brand} Adventure Series',
    '{brand} Sweet Dreams Series',
    '{brand} Gothic Series',
    '{brand} Marine Life Series',
    '{brand} Forest Friends Series',
    '{brand} Space Explorer Series',
    '{brand} Vintage Collection',
    '{brand} Holiday Special',
    '{brand} Sport Series',
    '{brand} Music Festival Series',
    '{brand} Cherry Blossom Series',
    '{brand} Night Fairy Series',
    '{brand} Royal Palace Series',
    '{brand} Summer Beach Series',
    '{brand} Winter Wonderland Series',
    '{brand} Autumn Harvest Series',
    '{brand} Spring Garden Series',
    '{brand} Urban Street Series',
    '{brand} Cyberpunk Series',
    '{brand} Retro Gaming Series',
    '{brand} Fairy Tale Series',
    '{brand} Mythology Series',
    '{brand} Dessert Paradise Series',
    '{brand} Coffee Time Series',
    '{brand} Tea Party Series',
    '{brand} Birthday Celebration Series',
    '{brand} Wedding Series',
    '{brand} Baby Shower Series',
    '{brand} School Days Series',
    '{brand} Office Life Series',
    '{brand} Chef Collection Series',
    '{brand} Doctor Series',
    '{brand} Artist Series',
    '{brand} Musician Series',
    '{brand} Athlete Series',
    '{brand} Superhero Series',
    '{brand} Princess Series',
    '{brand} Knight Series',
    '{brand} Pirate Series',
    '{brand} Astronaut Series',
    '{brand} Mermaid Series',
    '{brand} Dragon Series',
    '{brand} Unicorn Series',
    '{brand} Halloween Series',
    '{brand} Christmas Series',
    '{brand} Valentine Series',
    '{brand} Easter Series',
    '{brand} Chinese New Year Series',
]

# Materials
MATERIALS = [
    'PVC', 
    'ABS Plastic', 
    'Resin', 
    'Vinyl', 
    'PVC & ABS Mix', 
    'Soft Vinyl', 
    'Hard Plastic',
    'PVC + Resin',
    'Premium PVC'
]

# Sizes (format: PxLxT dalam cm)
SIZES = [
    '6 x 4 x 8 cm',
    '7 x 5 x 9 cm',
    '8 x 6 x 10 cm',
    '10 x 7 x 12 cm',
    '12 x 8 x 15 cm',
    '5 x 3 x 7 cm',
    '9 x 6 x 11 cm',
    '11 x 7 x 13 cm',
    '6 x 5 x 9 cm',
    '14 x 9 x 16 cm'
]

# Age recommendations
AGE_RECOMMENDATIONS = [
    '13 tahun ke atas',
    '15 tahun ke atas',
    '18 tahun ke atas',
    '14+ tahun',
    '16+ tahun',
    '13+',
    '15+',
    '18+',
    'Remaja dan dewasa'
]

# Origins
ORIGINS = [
    'China',
    'Imported from China',
    'China (Original Import)',
    'Mainland China',
    'PRC (People\'s Republic of China)'
]

# Categories - HARDCODED sesuai structure
CATEGORY_NAMES = [
    'Blind Box',
    'Limited Edition',
    'Standard Series',
    'Premium Collection',
    'Seasonal Special'
]

# Description templates (EXPANDED - 20+ variations untuk avoid duplicate)
DESCRIPTION_TEMPLATES = [
    "Koleksi {series} dari {brand}! Figurine blind box dengan detail tinggi dan kualitas import original. Cocok untuk kolektor dan pecinta mainan vinyl. Setiap box berisi 1 figurine random dari seri ini dengan desain eksklusif.",
    
    "{brand} {series} adalah salah satu seri paling populer tahun ini! Desain unik dengan finishing premium, perfect untuk display koleksi Anda. Material berkualitas tinggi dengan packaging original sealed dan sertifikat keaslian.",
    
    "Figurine collectible {brand} series {series}. Material berkualitas tinggi dengan packaging original. Limited stock, segera koleksi! Produk ini adalah blind box - karakter yang didapat acak namun tetap berkualitas premium dengan painting detail sempurna.",
    
    "Blind box {series} featuring karakter {brand} yang menggemaskan! Setiap box berisi 1 figurine random dari 8-12 varian berbeda. Packaging original import dengan seal utuh. Cocok sebagai hadiah atau untuk koleksi pribadi dengan value tinggi.",
    
    "{brand} kembali dengan {series}! Koleksi terbaru dengan tema yang fresh dan desain yang detail. Wajib punya untuk fans {brand}! Quality control ketat memastikan setiap piece dalam kondisi sempurna tanpa cacat produksi.",
    
    "Series eksklusif {series} dari {brand}. Produk original import dengan kualitas terjamin. Detail painting yang rapi dan material premium menjadikan ini investasi koleksi yang worthit. Dapat kartu koleksi dan packaging original dengan hologram.",
    
    "{brand} {series} - figurine vinyl berkualitas premium untuk kolektor sejati. Desain ikonik dengan karakteristik khas {brand}. Box sealed original, belum pernah dibuka. Stock terbatas, don't miss out! Pre-order sold out dalam hitungan jam.",
    
    "Dapatkan {series} koleksi terbaru dari {brand}! Figurine blind box dengan kemasan mewah dan detail ukiran yang presisi. Setiap piece diproduksi dengan standar quality control internasional. Perfect gift untuk special occasions.",
    
    "{brand} meluncurkan {series} dengan konsep yang revolutionary! Kombinasi warna vibrant dan desain yang eye-catching. Material PVC grade A dengan durability tinggi. Cocok untuk display di meja kerja atau rak koleksi.",
    
    "Special edition {series} dari brand ternama {brand}! Limited production hanya 5000 box worldwide. Setiap box dilengkapi dengan authenticity card dan special booklet. Nilai investasi tinggi untuk jangka panjang.",
    
    "Jangan lewatkan {brand} {series}! Kolaborasi eksklusif dengan desainer internasional. Finishing matte yang elegan dengan accent glossy di bagian tertentu. Packaging box dengan emboss gold foil yang mewah.",
    
    "{series} by {brand} hadir dengan 12 regular characters plus 1 hidden secret figure! Chase figure dengan rarity 1:144 memiliki market value 10x lipat. Perfect untuk serious collectors dan investment purpose.",
    
    "Blind box premium {brand} series {series}! Diproduksi dengan teknologi injection molding terkini untuk hasil sempurna. Setiap joint dapat digerakkan dengan smooth articulation. Display stand included di dalam box.",
    
    "Koleksi must-have: {brand} {series}! Design terinspirasi dari pop culture modern dengan twist yang unik. Setiap karakter memiliki backstory eksklusif di manual booklet. Community fanbase yang solid dan aktif.",
    
    "{brand} presents {series} - viral sensation di social media! Photogenic design yang instagram-worthy. Material premium dengan sentuhan akhir yang luxury. Packaging dapat dijadikan diorama display.",
    
    "Hot release: {series} dari {brand}! Pre-order sold out worldwide dalam 24 jam. Restock terbatas dengan quantity sangat limited. First come first served basis - jangan sampai kehabisan batch ini!",
    
    "Eksklusif Indonesia: {brand} {series}! Official distributor dengan garansi authenticity 100%. Harga special untuk early birds. Join komunitas kolektor Indonesia dan trading group eksklusif kami.",
    
    "{series} collection by {brand} - trending topic di forum kolektor! Appreciation value yang consistent setiap tahun. Packaging box dengan QR code untuk verify keaslian. After sales support untuk komplain produk cacat.",
    
    "Premium blind box {brand} featuring {series}! Collab dengan artist terkenal dari Jepang. Limited regional release hanya untuk Asia market. Certificate of authenticity dengan serial number unik per box.",
    
    "Newest arrival: {brand} {series}! Fresh from factory dengan production date terbaru. Zero defect guarantee dengan replacement policy. Free protective acrylic case untuk setiap pembelian 3 box atau lebih.",
]

# Extra info templates
EXTRA_INFO_TEMPLATES = [
    "Packaging original import. Box dalam kondisi sealed. Figurine sudah diproduksi dengan quality control ketat. Termasuk kartu koleksi original di dalam box.",
    
    "Termasuk kartu koleksi & manual dalam bahasa China/English. Box standar blind box original. Tidak termasuk accessories tambahan kecuali yang disebutkan dalam spesifikasi.",
    
    "Produk ini adalah blind box - karakter yang didapat acak. Setiap pembelian 1 full set (12 pcs) kemungkinan dapat semua varian lebih tinggi. Kami tidak melayani request karakter tertentu.",
    
    "Limited edition dengan produksi terbatas. Harga dapat berubah sewaktu-waktu mengikuti market value. First come first served! Box outer mungkin ada lecet tipis akibat pengiriman, namun figurine tetap sealed.",
    
    "Collectible item untuk usia remaja dan dewasa. Bukan mainan anak kecil. Ada part kecil yang bisa berbahaya jika tertelan. Display only, not for rough play.",
    
    "Blind box series ini memiliki 12 regular figures + 1 secret/hidden figure dengan probabilitas 1:144. Secret figure memiliki value lebih tinggi. Tidak ada refund/exchange untuk hasil blind box.",
    
    "Produk 100% original dan bergaransi. Jika menerima produk cacat/rusak (bukan karena hasil blind box tidak sesuai keinginan), dapat claim dalam 3 hari dengan video unboxing lengkap.",
]

# ============================================================
# GENERATOR FUNCTIONS
# ============================================================

def generate_product_name(brand: str, series: str, variant: int = None, index: int = 0) -> str:
    """
    Generate UNIQUE realistic product name with multiple variations
    Guarantee uniqueness dengan kombinasi brand, series, variant, dan format
    """
    # Multiple name formats untuk variety
    formats = [
        f"{brand} {series} - Figure #{variant}",
        f"{brand} {series} Blind Box #{variant}",
        f"{series} by {brand} Vol.{variant}",
        f"{brand} - {series} Edition {variant}",
        f"{brand} {series} Series {variant}",
        f"{series} {brand} Character {variant}",
        f"{brand} {series} Version {variant}",
        f"{brand} {series} No.{variant}",
        f"{series} - {brand} Figure {variant}",
        f"{brand} {series} Collection #{variant}",
        f"{series} {brand} Box {variant}",
        f"{brand} - {series} Set {variant}",
    ]
    
    if variant:
        # Use index to ensure different format for each product
        format_index = index % len(formats)
        return formats[format_index]
    else:
        # Non-variant products with unique suffix
        simple_formats = [
            f"{brand} {series}",
            f"{brand} {series} Blind Box",
            f"{series} by {brand}",
            f"{brand} - {series}",
            f"{brand} {series} Collection",
            f"{series} {brand} Edition",
        ]
        format_index = index % len(simple_formats)
        return simple_formats[format_index]

def generate_sku(index: int) -> str:
    """
    Generate GUARANTEED UNIQUE SKU
    Format: PREFIX-YEAR-SEQUENCE (contoh: TOY-25-00001)
    Index dimulai dari 1000 untuk avoid conflict dengan data existing
    """
    prefixes = ['TOY', 'FIG', 'BLB', 'COL', 'POP', 'VIN', 'CHR', 'BOX']
    # Rotate prefix berdasarkan index untuk variety
    prefix = prefixes[index % len(prefixes)]
    year = '25'  # 2025
    # Sequence number dijamin unik karena pakai index
    sequence = f"{index:05d}"
    return f"{prefix}-{year}-{sequence}"

def generate_price() -> Decimal:
    """
    Generate realistic price (in Rupiah)
    Returns Decimal for exact numeric(12,2) match
    """
    # Base prices for different tiers
    tiers = [
        (0.25, 85000),   # 25% - Budget friendly
        (0.35, 145000),  # 35% - Mid tier (most common)
        (0.25, 195000),  # 25% - Premium
        (0.10, 295000),  # 10% - Limited edition
        (0.05, 450000),  # 5% - Ultra premium
    ]
    
    rand = random.random()
    cumulative = 0
    for prob, base_price in tiers:
        cumulative += prob
        if rand <= cumulative:
            # Add some variation (±20%)
            variation = random.randint(-20000, 30000)
            final_price = max(75000, base_price + variation)
            # Round to nearest 5000
            final_price = round(final_price / 5000) * 5000
            return Decimal(str(final_price))
    
    return Decimal('145000.00')  # Fallback

def generate_weight() -> Decimal:
    """
    Generate weight in kg
    Returns Decimal for exact numeric(10,2) match
    """
    # Most figurines are 0.1 - 0.5 kg
    weight = round(random.uniform(0.12, 0.48), 2)
    return Decimal(str(weight))

def generate_product(index: int, category_id: int) -> Dict:
    """
    Generate single UNIQUE product data
    Exact match dengan tabel products
    Uses index untuk guarantee uniqueness
    """
    # Rotate through brands untuk variety
    brand = BRANDS[index % len(BRANDS)]
    
    # Rotate through series templates
    series_template = SERIES_TEMPLATES[index % len(SERIES_TEMPLATES)]
    series = series_template.format(brand=brand)
    
    # Generate variant dengan variasi
    # 60% chance punya variant number (1-12)
    variant = (index % 12) + 1 if random.random() > 0.4 else None
    
    # Generate unique name dengan index
    name = generate_product_name(brand, series, variant, index)
    
    # Truncate name if too long (max 150 chars)
    if len(name) > 150:
        name = name[:147] + "..."
    
    return {
        # product_id: auto-generated by DB
        'category_id': category_id,
        'name': name,
        'sku': generate_sku(index),
        'price': generate_price(),
        'weight': generate_weight(),
        'status': 'active',  # default active
        'created_at': datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(),
        'updated_at': datetime.now(ZoneInfo("Asia/Jakarta")).isoformat()
    }

def generate_product_detail(product_id: int, index: int) -> Dict:
    """
    Generate UNIQUE product detail
    Exact match dengan tabel product_details
    Uses index untuk avoid duplicate descriptions
    """
    # Rotate through brands and series untuk consistency
    brand = BRANDS[index % len(BRANDS)]
    series_template = SERIES_TEMPLATES[index % len(SERIES_TEMPLATES)]
    series = series_template.format(brand=brand)
    
    # Rotate through description templates untuk avoid duplication
    desc_template = DESCRIPTION_TEMPLATES[index % len(DESCRIPTION_TEMPLATES)]
    description = desc_template.format(
        brand=brand,
        series=series
    )
    
    # Rotate through materials, sizes, etc.
    material = MATERIALS[index % len(MATERIALS)]
    size = SIZES[index % len(SIZES)]
    age_rec = AGE_RECOMMENDATIONS[index % len(AGE_RECOMMENDATIONS)]
    origin = ORIGINS[index % len(ORIGINS)]
    extra_info = EXTRA_INFO_TEMPLATES[index % len(EXTRA_INFO_TEMPLATES)]
    
    return {
        # id: auto-generated by DB
        'product_id': product_id,
        'description': description,
        'material': material,
        'size': size,
        'age_recommendation': age_rec,
        'series': series,
        'origin': origin,
        'extra_info': extra_info
    }

# ============================================================
# CATEGORY MANAGEMENT
# ============================================================

def ensure_categories(supabase: Client) -> List[Dict]:
    """
    Ensure categories exist in database
    Returns list of category dicts with category_id
    """
    print("\n[STEP] Checking categories...")
    
    try:
        # Get existing categories
        response = supabase.table('categories').select('*').execute()
        
        if response.data and len(response.data) >= len(CATEGORY_NAMES):
            print(f"[INFO] Found {len(response.data)} existing categories")
            return response.data
        
        # Create missing categories
        print(f"[INFO] Creating {len(CATEGORY_NAMES)} categories...")
        
        # Clear existing first (optional)
        existing_names = [cat['name'] for cat in response.data] if response.data else []
        
        categories_to_create = []
        for cat_name in CATEGORY_NAMES:
            if cat_name not in existing_names:
                categories_to_create.append({'name': cat_name})
        
        if categories_to_create:
            response = supabase.table('categories').insert(categories_to_create).execute()
            print(f"[SUCCESS] Created {len(categories_to_create)} new categories")
        
        # Fetch all categories again
        response = supabase.table('categories').select('*').execute()
        return response.data
        
    except Exception as e:
        print(f"[ERROR] Category setup failed: {e}")
        raise

# ============================================================
# BULK INSERT FUNCTIONS
# ============================================================

def bulk_insert_products(supabase: Client, count: int, batch_size: int = 100):
    """
    Bulk insert products with batch processing
    
    Args:
        supabase: Supabase client
        count: Total products to generate
        batch_size: Insert batch size (default 100)
    """
    
    print(f"\n{'='*70}")
    print(f"  🎮 BULK DATA GENERATOR - GA TOYS")
    print(f"{'='*70}")
    print(f"Target: {count:,} products")
    print(f"Batch size: {batch_size}")
    print(f"Database: {SUPABASE_URL.split('.')[0].replace('https://', '')}")
    print(f"{'='*70}\n")
    
    # Ensure categories exist
    categories = ensure_categories(supabase)
    category_ids = [cat['category_id'] for cat in categories]
    
    if not category_ids:
        print("[ERROR] No categories found! Cannot continue.")
        return
    
    print(f"[INFO] Using {len(category_ids)} categories: {[c['name'] for c in categories]}")
    
    # Generate and insert products in batches
    print(f"\n[STEP] Generating {count:,} products in batches of {batch_size}...\n")
    
    total_inserted = 0
    total_failed = 0
    start_time = time.time()
    
    for batch_num in range(0, count, batch_size):
        batch_start = batch_num
        batch_end = min(batch_start + batch_size, count)
        batch_count = batch_end - batch_start
        batch_index = (batch_start // batch_size) + 1
        
        print(f"[BATCH {batch_index}] Generating {batch_count} products...")
        
        # Generate products batch with uniqueness guarantee
        products_batch = []
        for i in range(batch_start, batch_end):
            # Rotate through categories untuk even distribution
            category_id = category_ids[i % len(category_ids)]
            # Use (i + 1000) as unique index untuk avoid conflicts
            product = generate_product(i + 1000, category_id)
            products_batch.append(product)
        
        # Insert products
        try:
            print(f"[BATCH {batch_index}] Inserting products into database...")
            response = supabase.table('products').insert(products_batch).execute()
            inserted_products = response.data
            
            if not inserted_products:
                print(f"[ERROR] Batch {batch_index} returned no data!")
                total_failed += batch_count
                continue
            
            # Generate and insert product details with same index untuk consistency
            print(f"[BATCH {batch_index}] Inserting product details...")
            details_batch = []
            for idx, product in enumerate(inserted_products):
                # Use same index as product generation untuk match brand/series
                original_index = batch_start + idx
                detail = generate_product_detail(product['product_id'], original_index + 1000)
                details_batch.append(detail)
            
            supabase.table('product_details').insert(details_batch).execute()
            
            # Update counters
            inserted_count = len(inserted_products)
            total_inserted += inserted_count
            
            # Calculate progress
            progress = (total_inserted / count) * 100
            elapsed = time.time() - start_time
            rate = total_inserted / elapsed if elapsed > 0 else 0
            eta = (count - total_inserted) / rate if rate > 0 else 0
            
            print(f"[BATCH {batch_index}] ✓ Success: {inserted_count} products")
            print(f"[PROGRESS] {total_inserted}/{count} ({progress:.1f}%) | "
                  f"Rate: {rate:.1f} products/s | ETA: {eta:.0f}s")
            print()
            
        except Exception as e:
            print(f"[ERROR] Batch {batch_index} failed: {e}")
            total_failed += batch_count
            continue
    
    # Final summary
    elapsed_total = time.time() - start_time
    success_rate = (total_inserted / count) * 100 if count > 0 else 0
    
    print(f"\n{'='*70}")
    print(f"  ✅ GENERATION COMPLETE!")
    print(f"{'='*70}")
    print(f"Total products inserted: {total_inserted:,} / {count:,}")
    print(f"Failed: {total_failed:,}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Total time: {elapsed_total:.1f}s")
    print(f"Average rate: {total_inserted/elapsed_total:.1f} products/second")
    print(f"{'='*70}\n")

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clear_test_data(supabase: Client):
    """Clear all test data (DANGEROUS!)"""
    
    print("\n⚠️  WARNING: This will DELETE ALL products and product_details!")
    print("⚠️  This action CANNOT be undone!")
    confirm = input("\nType 'DELETE ALL' to confirm (case sensitive): ")
    
    if confirm != "DELETE ALL":
        print("❌ Operation cancelled")
        return
    
    print("\n[DELETING] Removing all data...")
    
    try:
        # Delete product_details first (foreign key constraint)
        print("[1/2] Deleting product_details...")
        response = supabase.table('product_details').delete().neq('id', 0).execute()
        print(f"  ✓ Deleted product_details (affected: {len(response.data) if response.data else 'all'})")
        
        # Delete products
        print("[2/2] Deleting products...")
        response = supabase.table('products').delete().neq('product_id', 0).execute()
        print(f"  ✓ Deleted products (affected: {len(response.data) if response.data else 'all'})")
        
        print("\n✅ All test data deleted successfully!")
        
    except Exception as e:
        print(f"\n❌ Deletion failed: {e}")
        print("Note: Supabase might not return deleted count in response")

def show_stats(supabase: Client):
    """Show current database statistics"""
    
    print(f"\n{'='*70}")
    print(f"  📊 DATABASE STATISTICS")
    print(f"{'='*70}")
    
    try:
        # Count products
        products_response = supabase.table('products') \
            .select('product_id', count='exact') \
            .execute()
        total_products = products_response.count
        print(f"Total Products: {total_products:,}")
        
        # Count by category
        categories = supabase.table('categories').select('*').execute()
        print(f"\nBreakdown by Category:")
        for cat in categories.data:
            cat_products = supabase.table('products') \
                .select('product_id', count='exact') \
                .eq('category_id', cat['category_id']) \
                .execute()
            print(f"  • {cat['name']:<25}: {cat_products.count:>6,} products")
        
        # Count details
        details_response = supabase.table('product_details') \
            .select('id', count='exact') \
            .execute()
        total_details = details_response.count
        print(f"\nTotal Product Details: {total_details:,}")
        
        # Data integrity check
        if total_products == total_details:
            print(f"✓ Data integrity: OK (1:1 product-detail ratio)")
        else:
            print(f"⚠️  Data integrity: Mismatch (products: {total_products}, details: {total_details})")
        
        # Price statistics
        price_stats = supabase.table('products') \
            .select('price') \
            .execute()
        
        if price_stats.data:
            prices = [float(p['price']) for p in price_stats.data]
            print(f"\nPrice Statistics:")
            print(f"  • Min Price: Rp {min(prices):,.0f}")
            print(f"  • Max Price: Rp {max(prices):,.0f}")
            print(f"  • Avg Price: Rp {sum(prices)/len(prices):,.0f}")
        
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"❌ Error fetching statistics: {e}")

# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Generate realistic test data for GA Toys chatbot database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --count 1000                  # Generate 1000 products
  %(prog)s --count 5000 --batch-size 200 # Generate 5000 with batch size 200
  %(prog)s --stats                       # Show database statistics
  %(prog)s --clear                       # Delete all data (dangerous!)
        """
    )
    
    parser.add_argument(
        '--count', 
        type=int, 
        default=1000,
        help='Number of products to generate (default: 1000)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for insertion (default: 100, max: 500)'
    )
    
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear all existing data (DANGEROUS!)'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show database statistics'
    )
    
    args = parser.parse_args()
    
    # Validate batch size
    if args.batch_size > 500:
        print("⚠️  Warning: Batch size > 500 may cause issues. Setting to 500.")
        args.batch_size = 500
    
    # Initialize Supabase
    print("\n[INIT] Connecting to Supabase...")
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Test connection
        supabase.table('categories').select('category_id', count='exact').limit(1).execute()
        print("✓ Connected to Supabase successfully")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        print("\nPlease check:")
        print("1. .env file exists with SUPABASE_URL and SUPABASE_KEY")
        print("2. Credentials are correct")
        print("3. Internet connection is stable")
        return
    
    # Execute command
    if args.clear:
        clear_test_data(supabase)
        show_stats(supabase)
    elif args.stats:
        show_stats(supabase)
    else:
        # Generate data
        bulk_insert_products(supabase, args.count, args.batch_size)
        show_stats(supabase)
        
        print("\n💡 Next steps:")
        print("1. Refresh FAISS index: curl -X POST http://localhost:8000/refresh-index")
        print("2. Test queries in Postman")
        print("3. Check metrics: curl http://localhost:8000/metrics")

if __name__ == "__main__":
    main()

# ============================================================
# DATA TEMPLATES
# ============================================================

# Brand/Series yang realistis
BRANDS = [
    'Tokidoki', 'Molly', 'LABUBU', 'PUCKY', 'Dimoo', 
    'Skullpanda', 'Hirono', 'Sweet Bean', 'The Monsters',
    'Crybaby', 'Zimomo', 'Satyr Rory', 'Have a Seat'
]

# Series variations
SERIES_TEMPLATES = [
    '{brand} Career Series',
    '{brand} Zodiac Series',
    '{brand} Adventure Series',
    '{brand} Sweet Series',
    '{brand} Gothic Series',
    '{brand} Marine Series',
    '{brand} Forest Series',
    '{brand} Space Series',
    '{brand} Vintage Series',
    '{brand} Holiday Series',
    '{brand} Sport Series',
    '{brand} Music Series',
]

# Materials
MATERIALS = [
    'PVC', 'ABS Plastic', 'Resin', 'Vinyl', 
    'PVC & ABS Mix', 'Soft Vinyl', 'Hard Plastic'
]

# Sizes (cm)
SIZES = [
    '6 x 4 x 8', '7 x 5 x 9', '8 x 6 x 10',
    '10 x 7 x 12', '12 x 8 x 15', '5 x 3 x 7',
    '9 x 6 x 11', '11 x 7 x 13', '6 x 5 x 9'
]

# Age recommendations
AGE_RECOMMENDATIONS = [
    '13 tahun ke atas', '15 tahun ke atas', '18 tahun ke atas',
    '14+ tahun', '16+ tahun', '13+', '15+', '18+'
]

# Origins
ORIGINS = ['China', 'Imported from China', 'China (Original Import)']

# Categories (pastikan sesuai dengan categories table Anda)
CATEGORIES = [
    'Blind Box',
    'Limited Edition',
    'Standard Series',
    'Premium Collection',
    'Seasonal Special'
]

# Description templates
DESCRIPTION_TEMPLATES = [
    "Koleksi {series} dari {brand}! Figurine blind box dengan detail tinggi dan kualitas import original. Cocok untuk kolektor dan pecinta mainan vinyl.",
    "{brand} {series} adalah salah satu seri paling populer tahun ini! Desain unik dengan finishing premium, perfect untuk display koleksi Anda.",
    "Figurine collectible {brand} series {series}. Material berkualitas tinggi dengan packaging original. Limited stock, segera koleksi!",
    "Blind box {series} featuring karakter {brand} yang menggemaskan! Setiap box berisi 1 figurine random dari 8-12 varian berbeda.",
    "{brand} kembali dengan {series}! Koleksi terbaru dengan tema yang fresh dan desain yang detail. Wajib punya untuk fans {brand}!",
]

# Extra info templates
EXTRA_INFO_TEMPLATES = [
    "Packaging original import. Box dalam kondisi sealed. Figurine sudah diproduksi dengan quality control ketat.",
    "Termasuk kartu koleksi & manual. Box standar blind box original. Tidak termasuk accessories tambahan.",
    "Produk ini adalah blind box - karakter yang didapat acak. Setiap pembelian 1 full set (12 pcs) kemungkinan dapat semua varian lebih tinggi.",
    "Limited edition dengan produksi terbatas. Harga dapat berubah sewaktu-waktu. First come first served!",
    "Collectible item untuk usia remaja dan dewasa. Bukan mainan anak kecil. Ada part kecil yang bisa berbahaya jika tertelan.",
]

# ============================================================
# GENERATOR FUNCTIONS
# ============================================================

def generate_product_name(brand: str, series: str, variant: int = None) -> str:
    """Generate realistic product name"""
    if variant:
        return f"{brand} {series} - Figure #{variant}"
    else:
        return f"{brand} {series}"

def generate_sku(index: int) -> str:
    """Generate unique SKU"""
    prefix = random.choice(['TOY', 'FIG', 'BLB', 'COL'])
    return f"{prefix}-{index:06d}"

def generate_price() -> int:
    """Generate realistic price (in Rupiah)"""
    # Base prices for different tiers
    tiers = [
        (0.3, 95000),   # 30% chance - Entry level
        (0.4, 145000),  # 40% chance - Mid tier
        (0.2, 195000),  # 20% chance - Premium
        (0.1, 295000),  # 10% chance - Limited edition
    ]
    
    rand = random.random()
    cumulative = 0
    for prob, price in tiers:
        cumulative += prob
        if rand <= cumulative:
            # Add some variation
            variation = random.randint(-10000, 20000)
            return max(75000, price + variation)
    
    return 145000  # Fallback

def generate_weight() -> float:
    """Generate weight in kg"""
    return round(random.uniform(0.15, 0.5), 2)

def generate_product(index: int, category_id: int) -> Dict:
    """Generate single product data"""
    
    brand = random.choice(BRANDS)
    series_template = random.choice(SERIES_TEMPLATES)
    series = series_template.format(brand=brand)
    
    variant = random.randint(1, 12) if random.random() > 0.3 else None
    name = generate_product_name(brand, series, variant)
    
    return {
        'name': name,
        'sku': generate_sku(index),
        'price': generate_price(),
        'weight': generate_weight(),
        'category_id': category_id,
        'status': 'active'
    }

def generate_product_detail(product_id: int) -> Dict:
    """Generate product detail"""
    
    brand = random.choice(BRANDS)
    series = random.choice(SERIES_TEMPLATES).format(brand=brand)
    
    description = random.choice(DESCRIPTION_TEMPLATES).format(
        brand=brand,
        series=series
    )
    
    return {
        'product_id': product_id,
        'description': description,
        'material': random.choice(MATERIALS),
        'size': random.choice(SIZES),
        'age_recommendation': random.choice(AGE_RECOMMENDATIONS),
        'series': series,
        'origin': random.choice(ORIGINS),
        'extra_info': random.choice(EXTRA_INFO_TEMPLATES)
    }

# ============================================================
# BULK INSERT FUNCTIONS
# ============================================================

def get_or_create_categories(supabase: Client) -> List[Dict]:
    """Get existing categories or create them"""
    print("\n[STEP] Checking categories...")
    
    # Get existing categories
    response = supabase.table('categories').select('*').execute()
    
    if response.data and len(response.data) > 0:
        print(f"[INFO] Found {len(response.data)} existing categories")
        return response.data
    
    # Create categories if not exist
    print("[INFO] Creating categories...")
    categories_data = [{'name': cat} for cat in CATEGORIES]
    
    response = supabase.table('categories').insert(categories_data).execute()
    
    print(f"[SUCCESS] Created {len(response.data)} categories")
    return response.data

def bulk_insert_products(supabase: Client, count: int, batch_size: int = 100):
    """
    Bulk insert products with batch processing
    
    Args:
        supabase: Supabase client
        count: Total products to generate
        batch_size: Insert batch size (default 100)
    """
    
    print(f"\n{'='*70}")
    print(f"  BULK DATA GENERATOR - GA TOYS")
    print(f"{'='*70}")
    print(f"Target: {count:,} products")
    print(f"Batch size: {batch_size}")
    print(f"{'='*70}\n")
    
    # Get categories
    categories = get_or_create_categories(supabase)
    category_ids = [cat['category_id'] for cat in categories]
    
    if not category_ids:
        print("[ERROR] No categories found!")
        return
    
    # Generate and insert products in batches
    print(f"\n[STEP] Generating {count:,} products...")
    
    total_inserted = 0
    start_index = 1000  # Start from SKU 1000
    
    for batch_start in range(0, count, batch_size):
        batch_end = min(batch_start + batch_size, count)
        batch_count = batch_end - batch_start
        
        print(f"\n[BATCH {batch_start//batch_size + 1}] Generating {batch_count} products...")
        
        # Generate products batch
        products_batch = []
        for i in range(batch_start, batch_end):
            category_id = random.choice(category_ids)
            product = generate_product(start_index + i, category_id)
            products_batch.append(product)
        
        # Insert products
        print(f"[BATCH {batch_start//batch_size + 1}] Inserting products...")
        try:
            response = supabase.table('products').insert(products_batch).execute()
            inserted_products = response.data
            
            # Generate and insert product details
            print(f"[BATCH {batch_start//batch_size + 1}] Inserting product details...")
            details_batch = []
            for product in inserted_products:
                detail = generate_product_detail(product['product_id'])
                details_batch.append(detail)
            
            supabase.table('product_details').insert(details_batch).execute()
            
            total_inserted += len(inserted_products)
            print(f"[BATCH {batch_start//batch_size + 1}] ✓ Inserted {len(inserted_products)} products")
            print(f"[PROGRESS] Total: {total_inserted}/{count} ({total_inserted/count*100:.1f}%)")
            
        except Exception as e:
            print(f"[ERROR] Batch {batch_start//batch_size + 1} failed: {e}")
            continue
    
    print(f"\n{'='*70}")
    print(f"  ✅ COMPLETED!")
    print(f"{'='*70}")
    print(f"Total products inserted: {total_inserted:,}")
    print(f"Success rate: {total_inserted/count*100:.1f}%")
    print(f"{'='*70}\n")

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clear_test_data(supabase: Client):
    """Clear all test data (DANGEROUS!)"""
    
    confirm = input("⚠️  WARNING: This will DELETE ALL products! Type 'DELETE' to confirm: ")
    
    if confirm != "DELETE":
        print("❌ Cancelled")
        return
    
    print("\n[DELETING] Removing all products...")
    
    try:
        # Delete product_details first (foreign key)
        supabase.table('product_details').delete().neq('product_id', 0).execute()
        print("✓ Deleted product_details")
        
        # Delete products
        supabase.table('products').delete().neq('product_id', 0).execute()
        print("✓ Deleted products")
        
        print("\n✅ All test data deleted!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_stats(supabase: Client):
    """Show current database statistics"""
    
    print(f"\n{'='*70}")
    print(f"  DATABASE STATISTICS")
    print(f"{'='*70}")
    
    # Count products
    products = supabase.table('products').select('product_id', count='exact').execute()
    print(f"Total Products: {products.count:,}")
    
    # Count by category
    categories = supabase.table('categories').select('*').execute()
    for cat in categories.data:
        cat_products = supabase.table('products') \
            .select('product_id', count='exact') \
            .eq('category_id', cat['category_id']) \
            .execute()
        print(f"  - {cat['name']}: {cat_products.count:,}")
    
    # Count details
    details = supabase.table('product_details').select('product_id', count='exact').execute()
    print(f"\nTotal Product Details: {details.count:,}")
    
    print(f"{'='*70}\n")

# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='Generate test data for GA Toys chatbot')
    
    parser.add_argument(
        '--count', 
        type=int, 
        default=1000,
        help='Number of products to generate (default: 1000)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for insertion (default: 100)'
    )
    
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear all existing data (DANGEROUS!)'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show database statistics'
    )
    
    args = parser.parse_args()
    
    # Initialize Supabase
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✓ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return
    
    # Execute command
    if args.clear:
        clear_test_data(supabase)
    elif args.stats:
        show_stats(supabase)
    else:
        bulk_insert_products(supabase, args.count, args.batch_size)
        show_stats(supabase)

if __name__ == "__main__":
    main()