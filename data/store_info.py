"""
Store Information Documents
Dynamic informasi dari Supabase
"""

from typing import List
from langchain.docstore.document import Document
from supabase import create_client, Client
import os
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def build_store_info_documents() -> List[Document]:
    """
    Build documents untuk informasi toko, kebijakan, FAQ umum
    Data diambil dari Supabase table: store_information
    """
    
    print("\n[STEP] Loading store information from Supabase...")
    
    try:
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            print("[ERROR] SUPABASE_URL or SUPABASE_KEY not found in environment variables")
            return _get_fallback_store_info()
        
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Query store_information table
        response = supabase.table('store_information') \
            .select('id, title, content, type') \
            .order('id') \
            .execute()
        
        if not response.data:
            print("[WARN] No store information found in Supabase, using fallback")
            return _get_fallback_store_info()
        
        store_info = response.data
        print(f"[SUCCESS] Loaded {len(store_info)} store information from Supabase")
        
    except Exception as e:
        print(f"[ERROR] Failed to load store information from Supabase: {e}")
        traceback.print_exc()
        print("[FALLBACK] Using static store information")
        return _get_fallback_store_info()
    
    # Build documents from Supabase data
    docs = []
    for info in store_info:
        docs.append(Document(
            page_content=f"{info['title']}\n\n{info['content']}",
            metadata={"type": info['type'], "title": info['title']}
        ))
    
    return docs


def _get_fallback_store_info() -> List[Document]:
    """
    Fallback static store info jika Supabase gagal
    """
    print("[INFO] Using fallback static store information")
    
    store_info = [
        {
            "title": "Tentang Toko GA Toys",
            "content": """
                GA Toys adalah toko spesialis mainan koleksi figurine import, terutama blind box series.
                Kami menjual berbagai karakter populer seperti Tokidoki, Molly, LABUBU, PUCKY, dan lainnya.

                Semua produk kami adalah original import dari China dengan kualitas terjamin.
                Kami fokus pada collectible toys untuk remaja dan dewasa (usia 13+).

                Produk kami meliputi:
                - Blind Box Series (berbagai karakter)
                - Limited Edition figurines
                - Seasonal Collections

                Kenapa memilih GA Toys?
                ✓ 100% Produk Original Import
                ✓ Quality Control ketat
                ✓ Packaging standar import terjamin
                ✓ Koleksi lengkap dan update
            """,
            "type": "store_info"
        },
        {
            "title": "Cara Pembelian",
            "content": """
                CARA PEMBELIAN DI GA TOYS:

                1. Browse produk di website kami
                2. Pilih produk yang diinginkan
                3. Klik tombol "Beli Sekarang" atau "Tambah ke Keranjang"
                4. Isi data pengiriman
                5. Pilih metode pembayaran (Transfer Bank / E-wallet)
                6. Selesaikan pembayaran
                7. Upload bukti pembayaran
                8. Pesanan akan diproses dalam 1x24 jam

                PEMBAYARAN:
                - Transfer Bank (BCA, Mandiri, BRI)
                - E-wallet (OVO, GoPay, DANA)
                - QRIS

                PENGIRIMAN:
                - JNE (Reguler & YES)
                - J&T Express
                - SiCepat
                - Gratis ongkir untuk pembelian di atas Rp 500.000

                Estimasi pengiriman: 2-5 hari kerja (tergantung lokasi)
            """,
            "type": "store_policy"
        },
        {
            "title": "Kebijakan Return & Garansi",
            "content": """
                KEBIJAKAN RETURN & GARANSI:

                RETURN/PENGEMBALIAN:
                ✓ Produk cacat produksi: Bisa ditukar/return dalam 3 hari
                ✓ Kesalahan pengiriman: Bisa ditukar dalam 3 hari
                ✗ Blind box tidak sesuai keinginan: TIDAK bisa return (sifat produk acak)
                ✗ Produk sudah dibuka segelnya: TIDAK bisa return

                SYARAT RETURN:
                - Packaging masih lengkap & rapi
                - Belum dibuka segel
                - Disertai bukti pembelian
                - Foto/video unboxing (untuk klaim cacat)

                GARANSI:
                - Garansi cacat produksi 7 hari sejak barang diterima
                - Harus ada video unboxing lengkap
                - Penggantian sesuai ketersediaan stock

                Untuk klaim, hubungi customer service dengan:
                - Nomor order
                - Foto produk
                - Video unboxing (jika ada)
            """,
            "type": "store_policy"
        },
        {
            "title": "Informasi Blind Box",
            "content": """
                APA ITU BLIND BOX?

                Blind box adalah sistem pembelian figurine dimana pembeli tidak tahu karakter mana yang akan didapat.
                Setiap box berisi 1 figurine dari seri tertentu (biasanya 8-12 varian berbeda).

                KARAKTERISTIK BLIND BOX:
                - Packaging tertutup rapat (tidak transparan)
                - Karakter yang didapat ACAK
                - Setiap varian punya probabilitas berbeda
                - Ada "secret" atau "hidden" figure dengan probabilitas sangat rendah

                PENTING DIKETAHUI:
                ⚠️ Karakter yang didapat TIDAK bisa dipilih
                ⚠️ Duplicate mungkin terjadi jika beli lebih dari 1
                ⚠️ TIDAK ADA RETURN untuk "karakter tidak sesuai harapan"
                ⚠️ Hanya return untuk produk CACAT atau RUSAK

                TIPS:
                - Beli 1 box lengkap (full set) untuk kemungkinan dapat semua varian lebih tinggi
                - Tukar dengan kolektor lain jika dapat duplicate
                - Join komunitas blind box untuk trading
            """,
            "type": "product_info"
        },
        {
            "title": "Rekomendasi Produk Berdasarkan Usia",
            "content": """
                REKOMENDASI BERDASARKAN USIA:

                REMAJA & DEWASA (13+):
                ✓ Semua produk kami direkomendasikan untuk usia 13 tahun ke atas
                ✓ Figurine PVC dengan detail kecil (tidak untuk anak kecil)
                ✓ Cocok untuk koleksi dan display

                ANAK-ANAK (di bawah 13 tahun):
                ⚠️ TIDAK DISARANKAN karena:
                - Ada part kecil yang bisa tertelan
                - Detail tajam
                - Bukan mainan untuk dimainkan
                - Lebih cocok untuk display/koleksi

                HADIAH:
                - Untuk remaja: Semua series cocok
                - Untuk dewasa kolektor: Limited edition series
                - Untuk pecinta kawaii: Molly, PUCKY, Sweet Bean
                - Untuk gothic lovers: Skullpanda series

                Jika ragu, hubungi customer service untuk konsultasi pemilihan produk.
            """,
            "type": "recommendation"
        },
        {
            "title": "Perawatan & Penyimpanan Figurine",
            "content": """
                TIPS PERAWATAN FIGURINE:

                PEMBERSIHAN:
                - Gunakan kuas halus untuk debu
                - Lap dengan kain microfiber lembut
                - JANGAN gunakan air atau cairan kimia
                - JANGAN semprot dengan cleaning spray

                PENYIMPANAN:
                ✓ Simpan di tempat sejuk dan kering
                ✓ Hindari sinar matahari langsung (bisa pudar)
                ✓ Display di dalam lemari kaca lebih baik
                ✓ Jauhkan dari sumber panas

                HANDLING:
                - Pegang dari bagian body (bukan bagian detail kecil)
                - Hindari menyentuh bagian yang dicat
                - Simpan packaging original untuk nilai jual kembali

                DISPLAY:
                - Gunakan stand atau base yang stabil
                - Jauhkan dari area sering tersenggol
                - Rotasi posisi agar tidak bosan
                - Foto untuk dokumentasi koleksi

                Figurine yang terawat baik bisa jadi investasi koleksi yang nilainya naik!
            """,
            "type": "guide"
        },
        {
            "title": "Jam Operasional & Kontak",
            "content": """
                JAM OPERASIONAL GA TOYS:

                ONLINE STORE:
                - Website: 24/7 (bisa order kapan saja)
                - Proses order: Senin - Sabtu, 09:00 - 17:00 WIB
                - Minggu & Tanggal Merah: Libur (order diproses hari kerja berikutnya)

                CUSTOMER SERVICE:
                - WhatsApp: 08123456789
                - Email: cs@gatoys.com
                - Instagram: @gatoys.id
                - Respond time: 1-3 jam (jam kerja)

                WAKTU RESPON:
                - Chat WA: 15-30 menit (jam kerja)
                - Email: 1x24 jam
                - Instagram DM: 1-3 jam (jam kerja)

                Untuk pertanyaan urgent, hubungi via WhatsApp.
            """,
            "type": "contact_info"
        },
        {
            "title": "FAQ Umum",
            "content": """
                PERTANYAAN YANG SERING DITANYAKAN:

                Q: Apakah produk original?
                A: Ya, 100% original import dari official distributor China.

                Q: Berapa lama pengiriman?
                A: 2-5 hari kerja tergantung lokasi dan ekspedisi yang dipilih.

                Q: Bisa COD?
                A: Maaf, untuk saat ini belum melayani COD. Hanya transfer bank/e-wallet.

                Q: Apakah ada toko offline?
                A: Saat ini kami hanya online store. Bisa cek Instagram untuk info pop-up store.

                Q: Bisa request karakter tertentu di blind box?
                A: Tidak bisa, karena sifat blind box memang acak. Tidak ada yang tahu isinya.

                Q: Kalau dapat duplicate gimana?
                A: Bisa trading dengan kolektor lain di komunitas atau jual kembali.

                Q: Apakah ready stock?
                A: Produk yang ditampilkan di website adalah ready stock. Update real-time.

                Q: Bisa pesan dalam jumlah banyak?
                A: Bisa! Hubungi CS untuk harga grosir (min. 10 box).
            """,
            "type": "faq"
        },
        {
            "title": "Promo & Diskon",
            "content": """
                PROMO RUTIN GA TOYS:

                📅 Flash Sale Jumat: Disc up to 30% produk pilihan
                📅 Weekend Sale: Gratis ongkir min. Rp 300.000
                📅 Member Day (tanggal 10): Extra disc 10% untuk member

                EVENT SPECIAL:
                🎉 Anniversary Sale (April): Disc hingga 50%
                🎉 12.12 Mega Sale: Buy 1 Get 1, bundle deals
                🎉 Chinese New Year: Limited edition series

                PRE-ORDER:
                - Pre-order series baru: Disc 20% + exclusive bonus
                - Early bird discount: First 50 buyers

                CARA DAPAT NOTIFIKASI PROMO:
                ✓ Follow Instagram @gatoys.id
                ✓ Subscribe email newsletter
                ✓ Join WhatsApp group member

                Jangan lewatkan promo menarik setiap bulannya!
            """,
            "type": "promo"
        }
    ]
    
    # Build fallback documents
    docs = []
    for info in store_info:
        docs.append(Document(
            page_content=f"{info['title']}\n\n{info['content']}",
            metadata={"type": info['type'], "title": info['title']}
        ))
    
    return docs