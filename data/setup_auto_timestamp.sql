-- ============================================================
-- Supabase Auto-Update Timestamp Setup
-- ============================================================
-- Script ini setup auto-update column `updated_at` di table products
-- setiap kali ada UPDATE operation

-- Step 1: Add column updated_at (jika belum ada)
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Step 2: Update existing rows dengan timestamp sekarang
UPDATE products 
SET updated_at = NOW() 
WHERE updated_at IS NULL;

-- Step 3: Buat function untuk auto-update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 4: Drop trigger lama (jika ada)
DROP TRIGGER IF EXISTS update_products_updated_at ON products;

-- Step 5: Buat trigger baru
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Verification: Check jika column sudah ada
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'products' AND column_name = 'updated_at';

-- Test: Update satu product dan cek timestamp
-- UPDATE products SET name = name WHERE product_id = 1;
-- SELECT product_id, name, updated_at FROM products WHERE product_id = 1;
