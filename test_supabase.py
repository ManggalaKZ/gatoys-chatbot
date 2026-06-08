"""
Quick test to check Supabase connection and data
"""

from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"SUPABASE_KEY: {SUPABASE_KEY[:20]}..." if SUPABASE_KEY else "None")
print()

try:
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Supabase client created")
    
    # Test 1: Check products table
    print("\n=== TEST 1: Checking products table ===")
    response = supabase.table('products').select('*').limit(5).execute()
    print(f"Total products (first 5): {len(response.data) if response.data else 0}")
    if response.data:
        print(f"Sample product: {response.data[0]}")
    
    # Test 2: Check categories table
    print("\n=== TEST 2: Checking categories table ===")
    response = supabase.table('categories').select('*').execute()
    print(f"Total categories: {len(response.data) if response.data else 0}")
    if response.data:
        print(f"Categories: {[cat['name'] for cat in response.data]}")
    
    # Test 3: Check product_details table
    print("\n=== TEST 3: Checking product_details table ===")
    response = supabase.table('product_details').select('*').limit(5).execute()
    print(f"Total product_details (first 5): {len(response.data) if response.data else 0}")
    
    # Test 4: Try the exact query used by the app (with joins)
    print("\n=== TEST 4: Testing JOIN query (like in app) ===")
    response = supabase.table('products') \
        .select("""
            product_id,
            name,
            sku,
            price,
            weight,
            status,
            categories!inner(name),
            product_details!inner(
                description,
                material,
                size,
                age_recommendation,
                series,
                origin,
                extra_info
            )
        """) \
        .eq('status', 'active') \
        .order('product_id') \
        .execute()
    
    print(f"Products with JOIN: {len(response.data) if response.data else 0}")
    if response.data:
        print(f"\nFirst product with all details:")
        print(f"  Name: {response.data[0].get('name')}")
        print(f"  SKU: {response.data[0].get('sku')}")
        print(f"  Category: {response.data[0].get('categories')}")
        print(f"  Details: {response.data[0].get('product_details')}")
    else:
        print("\n⚠️ No products returned with JOIN query!")
        print("This is the issue - the join is failing!")
        
        # Let's check without the joins
        print("\n=== TEST 5: Query without INNER joins ===")
        response = supabase.table('products') \
            .select("""
                product_id,
                name,
                sku,
                price,
                weight,
                status,
                categories(name),
                product_details(
                    description,
                    material,
                    size,
                    age_recommendation,
                    series,
                    origin,
                    extra_info
                )
            """) \
            .eq('status', 'active') \
            .order('product_id') \
            .execute()
        
        print(f"Products WITHOUT inner: {len(response.data) if response.data else 0}")
        if response.data:
            print(f"\nFirst product:")
            print(f"  Name: {response.data[0].get('name')}")
            print(f"  Category: {response.data[0].get('categories')}")
            print(f"  Details: {response.data[0].get('product_details')}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
