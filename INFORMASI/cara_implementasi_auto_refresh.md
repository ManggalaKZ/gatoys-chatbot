# Auto-Refresh FAISS Index dari Supabase Changes

## 📋 Overview

Sistem auto-refresh memungkinkan chatbot untuk **otomatis rebuild FAISS index** ketika ada perubahan di database Supabase, tanpa perlu restart server.

---

## 🎯 Cara Kerja

### **Opsi 1: Polling (RECOMMENDED)** ⭐

1. **Background thread** cek timestamp `updated_at` di Supabase setiap N detik
2. Jika ada perubahan → **rebuild FAISS index** otomatis
3. Chat tetap bisa berjalan (non-blocking)

**Pros:**
- ✅ Simple & reliable
- ✅ Tidak butuh webhook setup
- ✅ Bekerja di local & production
- ✅ Interval bisa diatur (60s, 120s, 300s, dll)

**Cons:**
- ⚠️ Ada delay maksimal = interval (misal 60 detik)
- ⚠️ Polling konsumsi resource (minimal)

---

## 🚀 Quick Start

### **1. Setup Database Schema**

Pastikan table `products` di Supabase punya column **`updated_at`**:

```sql
-- Jika belum ada, tambahkan column updated_at
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Buat trigger auto-update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger ke table products
DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### **2. Integrate ke FastAPI Server**

Edit `api/server.py`:

```python
from fastapi import FastAPI
from data.auto_refresh import start_auto_refresh_thread
from api import get_chatbot

app = FastAPI()

# Global refresh manager
refresh_manager = None

@app.on_event("startup")
async def startup_event():
    """Initialize chatbot dan auto-refresh on server startup"""
    global refresh_manager
    
    print("\n" + "="*70)
    print("🚀 STARTING CHATBOT SERVER")
    print("="*70)
    
    # Initialize chatbot (singleton)
    chatbot = get_chatbot()
    
    # Start auto-refresh thread
    print("\n[STARTUP] Starting auto-refresh...")
    refresh_manager = start_auto_refresh_thread(
        chatbot_instance=chatbot,
        check_interval=60  # Check setiap 60 detik (1 menit)
    )
    
    print("="*70)
    print("✅ SERVER READY")
    print("="*70 + "\n")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop auto-refresh on server shutdown"""
    global refresh_manager
    
    if refresh_manager:
        print("\n[SHUTDOWN] Stopping auto-refresh...")
        refresh_manager.stop()
```

### **3. Test**

1. **Start server:**
   ```bash
   python -m uvicorn api.server:app --reload --port 8000
   ```

2. **Log akan muncul:**
   ```
   [AUTO-REFRESH] Initialized with 60s interval
   [AUTO-REFRESH] Background thread started
   [AUTO-REFRESH] Initial timestamp: 2024-11-07 10:30:45+00:00
   ```

3. **Update data di Supabase** (via SQL atau admin panel)

4. **Tunggu max 60 detik**, log akan muncul:
   ```
   [AUTO-REFRESH] Change detected: 2024-11-07 10:30:45 → 2024-11-07 10:35:22
   [AUTO-REFRESH] 🔄 Detected database changes! Rebuilding index...
   [AUTO-REFRESH] ✅ Index rebuilt successfully in 2.34s
   [AUTO-REFRESH] Total products: 247
   ```

5. **Test chat request** → akan gunakan index yang baru!

---

## ⚙️ Configuration

### **Adjust Check Interval**

```python
# Check setiap 30 detik (lebih cepat detect changes)
refresh_manager = start_auto_refresh_thread(chatbot, check_interval=30)

# Check setiap 5 menit (lebih hemat resource)
refresh_manager = start_auto_refresh_thread(chatbot, check_interval=300)

# Recommended: 60-120 detik untuk balance antara responsiveness & efficiency
```

### **Custom Callback After Refresh**

```python
def on_refresh_complete(num_products):
    """Custom callback dipanggil setelah index rebuilt"""
    print(f"✅ Refresh complete! Now serving {num_products} products")
    # Send notification, update metrics, etc.

from data.auto_refresh import AutoRefreshManager

manager = AutoRefreshManager(
    chatbot,
    supabase_url=os.getenv('SUPABASE_URL'),
    supabase_key=os.getenv('SUPABASE_KEY'),
    check_interval=60,
    on_refresh_callback=on_refresh_complete
)
manager.start()
```

---

## 🔧 Advanced: Opsi Lain

### **Opsi 2: Supabase Realtime (Instant)** 🚀

Jika ingin **instant detection** tanpa delay:

```python
# TODO: Implement dengan Supabase Realtime Subscriptions
# Akan trigger rebuild IMMEDIATELY setelah INSERT/UPDATE/DELETE
# Butuh setup Supabase Realtime channel
```

### **Opsi 3: Webhook dari Admin Panel**

Jika kamu punya admin panel untuk manage products:

```python
@app.post("/api/admin/trigger-rebuild")
async def trigger_rebuild(admin_key: str):
    """Manual trigger rebuild via webhook"""
    if admin_key != os.getenv('ADMIN_SECRET_KEY'):
        raise HTTPException(status_code=403)
    
    # Rebuild index
    chatbot = get_chatbot()
    # ... rebuild logic
    
    return {"status": "success", "message": "Index rebuilt"}
```

---

## 📊 Monitoring

### **Check Status**

```python
@app.get("/api/status")
async def get_status():
    """Get auto-refresh status"""
    return {
        "auto_refresh_enabled": refresh_manager.is_running if refresh_manager else False,
        "check_interval": refresh_manager.check_interval if refresh_manager else None,
        "last_modified": refresh_manager.last_modified_at.isoformat() if refresh_manager and refresh_manager.last_modified_at else None
    }
```

### **Log Level**

File `data/auto_refresh.py` sudah punya log yang informatif:
- `[AUTO-REFRESH]` - status normal
- `[AUTO-REFRESH WARN]` - warning
- `[AUTO-REFRESH ERROR]` - error dengan traceback

---

## 🐛 Troubleshooting

### **Problem: "Column updated_at not found"**

**Solution:** Jalankan SQL di Supabase untuk add column:
```sql
ALTER TABLE products ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
```

### **Problem: "No changes detected padahal sudah update"**

**Kemungkinan:**
1. Trigger `update_updated_at_column()` belum di-apply
2. Update via SQL langsung tanpa trigger
3. Check interval terlalu lama

**Solution:** 
- Jalankan SQL trigger setup di atas
- Pastikan update via Supabase client (bukan raw SQL)
- Turunkan `check_interval` ke 30 detik

### **Problem: "Thread memory leak"**

**Solution:** Thread sudah di-set `daemon=True`, akan otomatis terminated ketika server shutdown.

---

## 📝 Best Practices

1. **Interval 60-120 detik** - balance antara responsiveness & efficiency
2. **Monitor logs** - pastikan rebuild success dan tidak error
3. **Test di development dulu** - pastikan tidak ada side effects
4. **Gunakan environment variables** - untuk Supabase credentials
5. **Add metrics** - track berapa kali rebuild, success rate, dll

---

## 🎯 Next Steps

1. ✅ Setup SQL trigger untuk `updated_at` column
2. ✅ Integrate `start_auto_refresh_thread()` di `server.py`
3. ✅ Test dengan update data di Supabase
4. ✅ Monitor logs untuk pastikan rebuild success
5. ⚡ (Optional) Implement Supabase Realtime untuk instant updates

---

**Done!** Sekarang chatbot kamu akan otomatis update ketika database berubah! 🚀
