-- ============================================================
-- SUPABASE DATABASE SETUP SCRIPT
-- ============================================================
-- This script creates all necessary tables for the chatbot system
-- Run this in your Supabase SQL Editor

-- ============================================================
-- 1. CATEGORIES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default categories
INSERT INTO public.categories (name, description) VALUES
('Action Figures', 'Action figures and collectibles'),
('BlindBox', 'Gundam model kits and accessories'),
('Accessories', 'Toy accessories and parts')
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- 2. PRODUCTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) UNIQUE NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    weight DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'out_of_stock')),
    category_id INTEGER REFERENCES public.categories(category_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_products_status ON public.products(status);
CREATE INDEX IF NOT EXISTS idx_products_category ON public.products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_sku ON public.products(sku);

-- ============================================================
-- 3. PRODUCT_DETAILS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.product_details (
    detail_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES public.products(product_id) ON DELETE CASCADE,
    description TEXT,
    material VARCHAR(255),
    size VARCHAR(100),
    age_recommendation VARCHAR(50),
    series VARCHAR(100),
    origin VARCHAR(100),
    extra_info TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(product_id)
);

-- Create index
CREATE INDEX IF NOT EXISTS idx_product_details_product ON public.product_details(product_id);

-- ============================================================
-- 4. STORE_INFORMATION TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.store_information (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'general' CHECK (type IN ('general', 'policy', 'faq', 'contact', 'hours')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default store information
INSERT INTO public.store_information (title, content, type) VALUES
('Store Name', 'GA Toys - Your Trusted Toy Store', 'general'),
('Store Description', 'GA Toys is a specialized store offering action figures, Gundam models, anime figurines, and collectibles. We provide authentic products with competitive prices.', 'general'),
('Store Location', 'Jakarta, Indonesia', 'contact'),
('Contact WhatsApp', '081234567890', 'contact'),
('Contact Email', 'support@gatoys.com', 'contact'),
('Store Hours', 'Monday - Friday: 9:00 AM - 6:00 PM, Saturday: 10:00 AM - 4:00 PM, Sunday: Closed', 'hours'),
('Shipping Policy', 'We offer shipping throughout Indonesia via JNE, J&T, and SiCepat. Shipping costs are calculated based on weight and destination. Orders are processed within 1-2 business days.', 'policy'),
('Return Policy', 'Products can be returned within 7 days if there is a manufacturing defect or damage during shipping. Returns must include original packaging. Custom orders cannot be returned.', 'policy'),
('Payment Methods', 'We accept Bank Transfer (BCA, Mandiri, BRI), E-wallet (GoPay, OVO, Dana), and Cash on Delivery (COD) for certain areas.', 'policy'),
('Warranty Information', 'All products come with manufacturer warranty. Warranty period varies by product type. Contact us for warranty claims.', 'policy')
ON CONFLICT DO NOTHING;

-- ============================================================
-- 5. AUTO-UPDATE TIMESTAMP FUNCTION
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to products table
DROP TRIGGER IF EXISTS update_products_updated_at ON public.products;
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON public.products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to store_information table
DROP TRIGGER IF EXISTS update_store_info_updated_at ON public.store_information;
CREATE TRIGGER update_store_info_updated_at
    BEFORE UPDATE ON public.store_information
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 6. INSERT SAMPLE PRODUCTS (OPTIONAL)
-- ============================================================
-- Uncomment below to add sample products

/*
-- Sample Gundam Products
INSERT INTO public.products (name, sku, price, weight, status, category_id) VALUES
('MG Gundam Barbatos', 'MG-001', 450000, 0.5, 'active', (SELECT category_id FROM categories WHERE name = 'Gundam')),
('RG Wing Gundam EW', 'RG-002', 350000, 0.3, 'active', (SELECT category_id FROM categories WHERE name = 'Gundam')),
('HG Unicorn Gundam', 'HG-003', 250000, 0.2, 'active', (SELECT category_id FROM categories WHERE name = 'Gundam'));

-- Add product details
INSERT INTO public.product_details (product_id, description, material, size, age_recommendation, series, origin) VALUES
((SELECT product_id FROM products WHERE sku = 'MG-001'), 
 'Master Grade Gundam Barbatos from Iron-Blooded Orphans series. High detailed model kit with full inner frame.',
 'Plastic (PS/ABS)', 
 '1/100 Scale (approx 18cm)', 
 '15+', 
 'Iron-Blooded Orphans', 
 'Japan');

INSERT INTO public.product_details (product_id, description, material, size, age_recommendation, series, origin) VALUES
((SELECT product_id FROM products WHERE sku = 'RG-002'), 
 'Real Grade Wing Gundam Endless Waltz version. Perfect for experienced builders.',
 'Plastic (PS)', 
 '1/144 Scale (approx 13cm)', 
 '15+', 
 'Gundam Wing', 
 'Japan');

INSERT INTO public.product_details (product_id, description, material, size, age_recommendation, series, origin) VALUES
((SELECT product_id FROM products WHERE sku = 'HG-003'), 
 'High Grade Unicorn Gundam. Great for beginners. Includes LED unit.',
 'Plastic (PS)', 
 '1/144 Scale (approx 12cm)', 
 '12+', 
 'Gundam Unicorn', 
 'Japan');
*/

-- ============================================================
-- 7. VERIFICATION QUERIES
-- ============================================================
-- Run these to verify the setup

-- Check tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('categories', 'products', 'product_details', 'store_information');

-- Check categories
SELECT * FROM public.categories;

-- Check store information
SELECT * FROM public.store_information;

-- Check products count
SELECT 
    c.name as category,
    COUNT(p.product_id) as product_count
FROM public.categories c
LEFT JOIN public.products p ON c.category_id = p.category_id
GROUP BY c.name;

-- ============================================================
-- NOTES
-- ============================================================
-- 1. Run this entire script in Supabase SQL Editor
-- 2. Uncomment the sample products section if you need test data
-- 3. Make sure to enable Row Level Security (RLS) if needed
-- 4. Update the sample contact information with your actual details
-- ============================================================
