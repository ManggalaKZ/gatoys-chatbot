# 🔍 FLOW ULTRA VALIDATOR - Dokumentasi Lengkap

## 📋 Overview
Ultra Validator adalah sistem validasi berlapis (multi-layer) dengan 8 layer defense untuk memastikan hanya pertanyaan yang relevan dengan toko GA Toys yang diproses oleh chatbot.

**Target Accuracy:** 97-100%  
**Current Performance:** 97-100% (33-34/34 test cases)

---

## 🎯 Main Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER QUESTION INPUT                       │
│                  "Bisa kasih foto real pict                  │
│                   sebelum checkout?"                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              🔵 LAYER 0: PRE-CHECK                          │
│                                                               │
│  ✓ Check panjang pertanyaan >= 3 karakter                   │
│                                                               │
│  IF question.length < 3:                                     │
│     ❌ RETURN (False, "too_short", 1.0)                     │
│                                                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼ PASS
┌─────────────────────────────────────────────────────────────┐
│         🔴 LAYER 1: EXPLICIT BLACKLIST CHECK                │
│                                                               │
│  ✓ Scan 50+ blacklisted keywords dengan regex \b pattern    │
│  ✓ Keywords: bitcoin, coding, resep, band, anime, game,     │
│              restoran, bola, politik, etc.                   │
│                                                               │
│  IF found blacklist keyword:                                 │
│     ❌ RETURN (False, "blacklist_keyword:xxx", 0.98)        │
│                                                               │
│  Example REJECT:                                             │
│    - "Harga bitcoin?" → blacklist: bitcoin                   │
│    - "Cara coding?" → blacklist: coding                      │
│    - "Resep kue?" → blacklist: resep                         │
│                                                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼ NO BLACKLIST
┌─────────────────────────────────────────────────────────────┐
│          🟠 LAYER 2: REGEX PATTERN REJECT                   │
│                                                               │
│  ✓ Gunakan ContextValidator.is_in_context() dari validator  │
│    lama untuk cek pattern OUT_OF_CONTEXT_PATTERNS           │
│                                                               │
│  IF reason == "out_of_context_pattern":                      │
│     ❌ RETURN (False, "regex_pattern_reject", 0.95)         │
│                                                               │
│  Example REJECT:                                             │
│    - "Berapa 5 + 3?" → math pattern                          │
│    - "Cuaca hari ini?" → weather pattern                     │
│                                                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼ NO REGEX REJECT
┌─────────────────────────────────────────────────────────────┐
│           🟡 LAYER 3: INTENT CLASSIFICATION                 │
│                                                               │
│  ✓ Analyze question intent dengan _check_question_intent()  │
│                                                               │
│  Intent Categories:                                          │
│    • math (1.0 conf) - Calculation questions                │
│    • weather (0.95 conf) - Weather inquiry                  │
│    • shopping (0.9 conf) - Has shopping keywords            │
│    • product_inquiry (0.85 conf) - Has product context      │
│    • general (0.3 conf) - Unknown intent                    │
│                                                               │
│  IF intent IN ['math', 'weather'] AND confidence > 0.8:      │
│     ❌ RETURN (False, "intent_reject:xxx", confidence)      │
│                                                               │
│  IF intent IN ['shopping', 'product_inquiry'] AND conf>0.8: │
│     ✅ RETURN (True, "intent_accept:xxx", confidence)       │
│                                                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼ AMBIGUOUS INTENT
┌─────────────────────────────────────────────────────────────┐
│        🟢 LAYER 3.5: STORE OPERATION CHECK                  │
│                                                               │
│  ✓ Check dengan _has_store_operation_context()              │
│                                                               │
│  Method 1: Exact Phrase Matching                             │
│    - Cek 20+ store operation phrases di                     │
│      STORE_OPERATION_KEYWORDS                                │
│    - Example: "cara membeli", "pengiriman",                  │
│               "bisa tukar", "foto real", "checkout"          │
│                                                               │
│  Method 2: Regex Pattern Matching                            │
│    Pattern 1: r'bisa\s+(tukar|cod|kasih)'                   │
│      → "bisa tukar", "bisa COD", "bisa kasih"               │
│                                                               │
│    Pattern 2: r'bisa\s+kasih\s+foto'                         │
│      → "bisa kasih foto"                                     │
│                                                               │
│    Pattern 3: r'(dapet|dapat)\s+duplikat'                    │
│      → "dapet duplikat", "dapat duplikat"                    │
│                                                               │
│    Pattern 4: r'foto\s+real'                                 │
│      → "foto real", "foto real pict"                         │
│                                                               │
│    Pattern 5: r'real\s+pict'                                 │
│      → "real pict", "kasih real pict"                        │
│                                                               │
│    Pattern 6: r'sebelum\s+checkout'                          │
│      → "sebelum checkout", "foto sebelum checkout"           │
│                                                               │
│  IF store operation detected:                                │
│     ✅ RETURN (True, "store_operation_inquiry", 0.92)       │
│                                                               │
│  Example ACCEPT:                                             │
│    ✓ "Kalo dapet duplikat bisa tukar gak?"                   │
│      → Pattern: r'(dapet|dapat)\s+duplikat' ✓               │
│      → Pattern: r'bisa\s+(tukar|cod|kasih)' ✓               │
│                                                               │
│    ✓ "Bisa kasih foto real pict sebelum checkout?"           │
│      → Pattern: r'bisa\s+kasih\s+foto' ✓                     │
│      → Pattern: r'foto\s+real' ✓                             │
│      → Pattern: r'real\s+pict' ✓                             │
│      → Pattern: r'sebelum\s+checkout' ✓                      │
│                                                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼ NOT STORE OPERATION
┌─────────────────────────────────────────────────────────────┐
│         🔵 LAYER 4: AMBIGUOUS KEYWORD CHECK                 │
│                                                               │
│  ✓ Check dengan _is_ambiguous_keyword_question()            │
│                                                               │
│  Ambiguous Keywords: ['harga', 'berapa', 'ada', 'punya']    │
│                                                               │
│  Logic:                                                       │
│    IF ambiguous_keyword IN question:                         │
│       IF NOT has_product_context():                          │
│          AND NOT has_shopping_keyword():                     │
│             → AMBIGUOUS (needs context!)                     │
│                                                               │
│  IF strict_mode AND is_ambiguous:                            │
│     ❌ RETURN (False, "ambiguous_keyword:xxx", 0.85)        │
│                                                               │
│  Example REJECT (strict mode):                               │
│    - "Harga bitcoin?" → ambiguous 'harga' no product ctx    │
│    - "Berapa umur presiden?" → ambiguous 'berapa' no ctx    │
│                                                               │
│  Example ACCEPT:                                             │
│    - "Harga Molly berapa?" → has product context (Molly)    │
│    - "Ada stok blind box?" → has product context            │
│                                                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼ NOT AMBIGUOUS / NON-STRICT
┌─────────────────────────────────────────────────────────────┐
│          🟣 LAYER 5: BRAND/PRODUCT NAME CHECK               │
│                                                               │
│  ✓ Check brand names (15+ brands) di BRAND_NAMES            │
│    Brands: tokidoki, molly, labubu, pucky, dimoo,           │
│            skullpanda, hirono, sweet bean, etc.              │
│                                                               │
│  IF brand_name IN question:                                  │
│     ┌─────────────────────────────────────────┐             │
│     │  Sub-Check 1: Wrong Context Words       │             │
│     │  ────────────────────────────────────   │             │
│     │  IF 'band', 'musik', 'anime', 'game',   │             │
│     │     'restoran', 'maskot' IN question:   │             │
│     │     ❌ REJECT: brand_in_wrong_context   │             │
│     │                                          │             │
│     │  Example:                                │             │
│     │    - "Tokidoki itu band rock?"           │             │
│     │    - "Dimoo karakter game ya?"           │             │
│     └─────────────────────────────────────────┘             │
│                    │                                          │
│                    ▼ CONTEXT OK                              │
│     ┌─────────────────────────────────────────┐             │
│     │  Sub-Check 2: Brand Origin Inquiry      │             │
│     │  ────────────────────────────────────   │             │
│     │  IF 'dari anime', 'dari game',          │             │
│     │     'dari mana', 'apa tokidoki',        │             │
│     │     'siapa dimoo' IN question:          │             │
│     │     ❌ REJECT: brand_origin_inquiry     │             │
│     │                                          │             │
│     │  Example:                                │             │
│     │    - "Tokidoki dari anime apa?"          │             │
│     │    - "Apa tokidoki itu?"                 │             │
│     └─────────────────────────────────────────┘             │
│                    │                                          │
│                    ▼ ALL CHECKS PASS                         │
│     ✅ RETURN (True, "brand_name_match:xxx", 0.88)          │
│                                                               │
│  Example ACCEPT:                                             │
│    ✓ "Ada koleksi terbaru Skullpanda?"                       │
│    ✓ "Molly Sweet Home harganya berapa?"                     │
│    ✓ "Dimoo edisi Halloween ready?"                          │
│                                                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼ NO BRAND NAME
┌─────────────────────────────────────────────────────────────┐
│          🟠 LAYER 6: SEMANTIC VALIDATION                    │
│           (IF enable_semantic = True)                        │
│                                                               │
│  ✓ Use SemanticValidator.is_semantically_related()          │
│  ✓ Embedding Model: paraphrase-multilingual-MiniLM-L12-v2   │
│                                                               │
│  Process:                                                     │
│    1. Encode question → embedding vector                     │
│    2. Compare with BUSINESS_SCOPE embedding                  │
│    3. Compare with IN_SCOPE_EXAMPLES embeddings              │
│    4. Compare with OUT_OF_SCOPE_EXAMPLES embeddings          │
│    5. Calculate cosine similarity scores                     │
│                                                               │
│  Decision Logic:                                              │
│    max_in_score = max similarity with in-scope examples      │
│    max_out_score = max similarity with out-scope examples    │
│                                                               │
│    IF max_in_score > in_scope_threshold (0.35):              │
│       ✅ is_related = True                                   │
│    ELIF max_out_score > out_of_scope_threshold (0.25):       │
│       ❌ is_related = False                                  │
│    ELSE:                                                      │
│       → confidence < 0.5 (ambiguous)                         │
│                                                               │
│  IF is_related AND confidence > 0.5:                         │
│     ✅ RETURN (True, "semantic_accept:xxx", confidence)     │
│                                                               │
│  IF NOT is_related AND confidence > 0.5:                     │
│     ❌ RETURN (False, "semantic_reject:xxx", confidence)    │
│                                                               │
│  IF confidence <= 0.5:                                       │
│     → Continue to next layer (ambiguous)                     │
│                                                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼ SEMANTIC AMBIGUOUS / DISABLED
┌─────────────────────────────────────────────────────────────┐
│           🟡 LAYER 7: KEYWORD FALLBACK                      │
│                                                               │
│  ✓ Use old ContextValidator.is_in_context() result          │
│                                                               │
│  IF reason == "has_context_keyword":                         │
│     ✅ RETURN (True, "keyword_fallback", 0.65)              │
│                                                               │
│  Keywords checked (dari validator lama):                     │
│    - Shopping: beli, pesan, order, harga, etc.              │
│    - Product: blind box, figurine, mainan, etc.             │
│    - Store: toko, stok, ready, tersedia, etc.               │
│                                                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼ NO KEYWORD MATCH
┌─────────────────────────────────────────────────────────────┐
│          🔴 LAYER 8: DEFAULT DECISION                       │
│                                                               │
│  IF strict_mode == True:                                     │
│     ❌ RETURN (False, "strict_mode_default_reject", 0.60)   │
│     → Better reject than answer wrong!                       │
│                                                               │
│  ELSE (non-strict):                                          │
│     ✅ RETURN (True, "default_allow", 0.50)                 │
│     → Give benefit of doubt                                  │
│                                                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                   ┌────────────────┐
                   │  FINAL RESULT  │
                   │                │
                   │ (is_valid,     │
                   │  reason,       │
                   │  confidence)   │
                   └────────────────┘
```


## 📊 Example Flow Traces

### ✅ Example 1: "Bisa kasih foto real pict sebelum checkout?"

```
INPUT: "Bisa kasih foto real pict sebelum checkout?"

Layer 0: Pre-Check
  ✓ Length = 45 chars (>= 3) → PASS

Layer 1: Blacklist Check
  ✓ No blacklist keyword found → PASS

Layer 2: Regex Pattern
  ✓ Not math/weather pattern → PASS

Layer 3: Intent Classification
  ✓ Intent: general (conf: 0.3) → AMBIGUOUS, continue

Layer 3.5: Store Operation Check ⭐
  ✓ Check STORE_OPERATION_KEYWORDS:
    - "foto real" ✓ FOUND
    - "real pict" ✓ FOUND  
    - "checkout" ✓ FOUND
  
  ✓ Check regex patterns:
    - r'bisa\s+kasih\s+foto' → MATCH! ✓
    - r'foto\s+real' → MATCH! ✓
    - r'real\s+pict' → MATCH! ✓
    - r'sebelum\s+checkout' → MATCH! ✓
  
  ✅ RETURN (True, "store_operation_inquiry", 0.92)

FINAL RESULT: ✅ IN-CONTEXT (confidence: 0.92)
```

## 🔧 Configuration Options

### Strict Mode
```python
# Strict Mode = True (Production recommended)
validator = UltraValidator(enable_semantic=True, strict_mode=True)

# Behavior:
# - Layer 4: Reject ambiguous keywords without product context
# - Layer 8: Default reject if no match found
# - Better for production: prevent false positives
```

### Non-Strict Mode
```python
# Strict Mode = False (Development/Testing)
validator = UltraValidator(enable_semantic=True, strict_mode=False)

# Behavior:
# - Layer 4: Allow ambiguous keywords (continue to semantic)
# - Layer 8: Default accept if no clear reject
# - More permissive, may allow some edge cases
```

### Semantic Layer Toggle
```python
# With Semantic (Recommended)
validator = UltraValidator(enable_semantic=True, strict_mode=True)
# → Uses AI embedding for intelligent validation

# Without Semantic (Faster, rule-based only)
validator = UltraValidator(enable_semantic=False, strict_mode=True)
# → Pure rule-based, faster but less intelligent
```
minggu 