"""
Exact Matcher - Pre-filter untuk query yang butuh exact match

Handles:
- SKU search (contoh: "sku BLB-001044", "ada BLB-001044?")
- Brand-specific search (contoh: "produk LABUBU", "ada LABUBU?")
- Product name search
- Fuzzy matching untuk typos (contoh: "labuba" → "labubu")

Cara kerja:
1. Detect jika query butuh exact match
2. Query langsung ke products_cache dengan filter
3. Return matched products atau None (fallback ke vector search)
"""

import re
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher


class ExactMatcher:
    """Pre-filter untuk exact match queries sebelum vector search"""
    # menggunakan pattern matching dan fuzzy matching untuk handle typos
    def __init__(self, products_cache: List[Dict]):
        """
        Args:
            products_cache: List of product dicts dari load_products_from_db()
        """
        self.products = products_cache
        print(f"[EXACT_MATCHER] Initialized with {len(products_cache)} products")
    
    def match(self, question: str) -> Optional[Tuple[str, List[Dict]]]:
        """
        Try to match question dengan exact criteria
        
        Args:
            question: User question
            
        Returns:
            Tuple of (match_type, matched_products) if found, else None
            match_type: 'sku' | 'brand' | 'product_name'
        """
        question_lower = question.lower()
        
        # 1. SKU Match
        sku_match = self._match_sku(question_lower)
        if sku_match:
            return ('sku', sku_match)
        
        # 2. Brand Match
        brand_match = self._match_brand(question_lower)
        if brand_match:
            return ('brand', brand_match)
        
       
        
        return None
    
    def _match_sku(self, question_lower: str) -> Optional[List[Dict]]:
        """
        Match SKU pattern dalam question
        
        SKU formats:
        - TOY-25-00001
        - FIG-25-00002
        - BLB-001044
        - COL-25-12345
        """
        # Pattern untuk SKU format kita
        sku_patterns = [
            r'\b([A-Z]{3}-\d{2}-\d{5})\b',  # TOY-25-00001
            r'\b([A-Z]{3}-\d{6})\b',         # BLB-001044 (old format)
        ]
        
        for pattern in sku_patterns:
            match = re.search(pattern, question_lower.upper())
            if match:
                sku = match.group(1)
                print(f"[EXACT_MATCHER] SKU detected: {sku}")
                
                # Search dalam products_cache
                matches = [p for p in self.products if p['sku'].upper() == sku.upper()]
                
                if matches:
                    print(f"[EXACT_MATCHER] ✓ Found {len(matches)} product(s) with SKU {sku}")
                    return matches
                else:
                    print(f"[EXACT_MATCHER] ✗ No product found with SKU {sku}")
                    return []  # Empty list = SKU not found (different dari None)
        
        return None  # None = bukan SKU query
    
    def _fuzzy_match_brand(self, word: str, brands: List[str], threshold: float = 0.8) -> Optional[str]:
        """
        Fuzzy match untuk handle typos in brand names
        
        Args:
            word: Word to match (potentially typo)
            brands: List of correct brand names
            threshold: Similarity threshold (0-1), default 0.8
            
        Returns:
            Matched brand name if similarity >= threshold, else None
            
        Example:
            "labuba" → "labubu" (similarity: 0.83)
            "pucky" → "pucky" (exact match: 1.0)
            "hello kity" → "hello kitty" (similarity: 0.92)
        """
        best_match = None
        best_score = 0.0
        
        for brand in brands:
            # Calculate similarity ratio
            similarity = SequenceMatcher(None, word.lower(), brand.lower()).ratio()
            
            if similarity > best_score:
                best_score = similarity
                best_match = brand
        
        # Return match if above threshold
        if best_score >= threshold:
            if word.lower() != best_match.lower():  # Ada typo yang di-correct
                print(f"[FUZZY_MATCH] '{word}' → '{best_match}' (similarity: {best_score:.2f})")
            return best_match
        
        return None
    
    def _match_brand(self, question_lower: str) -> Optional[List[Dict]]:
        """
        Match brand name dalam question (with fuzzy matching for typos)
        
        Trigger words: "produk {brand}", "ada {brand}", "{brand} apa saja", etc.
        """
        # Common brands (dari auto_create_data.py)
        brands = [
            'tokidoki', 'molly', 'labubu', 'pucky', 'dimoo',
            'skullpanda', 'hirono', 'sweet bean', 'the monsters',
            'crybaby', 'zimomo', 'satyr rory', 'have a seat',
            'skull panda', 'pop mart', 'kennyswork', 'instinctoy',
            'fluffy house', 'bean sprout', 'azura', 'hacipupu',
            'yuki', 'penny', 'baby three', 'kasing lung',
            'buzz', 'panda roll', 'little amber', 'cosmo', 'vivi cat',
            'cookie', 'bunny', 'seulgi', 'fortune cat', 'miffy',
            'snoopy', 'hello kitty', 'kuromi', 'my melody', 'cinnamoroll',
            'little twin stars', 'pompompurin', 'badtz-maru', 'keroppi'
        ]
        
        # Trigger patterns untuk brand search
        brand_triggers = [
            r'produk\s+(\w+)',           # "produk LABUBU"
            r'ada\s+(\w+)',              # "ada LABUBU"
            r'(\w+)\s+apa\s+saja',       # "LABUBU apa saja"
            r'berapa\s+(\w+)',           # "berapa produk LABUBU"
            r'(\w+)\s+yang\s+tersedia',  # "LABUBU yang tersedia"
            r'list\s+(\w+)',             # "list LABUBU"
            r'katalog\s+(\w+)',          # "katalog LABUBU"
        ]
        
        for trigger in brand_triggers:
            match = re.search(trigger, question_lower)
            if match:
                potential_brand = match.group(1).lower()
                
                # STEP 1: Try exact match first
                if potential_brand in brands:
                    matched_brand = potential_brand
                    print(f"[EXACT_MATCHER] Brand detected (exact): {matched_brand}")
                else:
                    # STEP 2: Try fuzzy match (handle typos)
                    matched_brand = self._fuzzy_match_brand(potential_brand, brands, threshold=0.75)
                    
                    if not matched_brand:
                        # No match even with fuzzy - skip
                        continue
                
                # Search products by matched brand
                matches = [
                    p for p in self.products 
                    if matched_brand.lower() in p['name'].lower()
                ]
                
                if matches:
                    print(f"[EXACT_MATCHER] ✓ Found {len(matches)} product(s) for brand '{matched_brand}'")
                    return matches
                else:
                    print(f"[EXACT_MATCHER] ✗ No products found for brand '{matched_brand}'")
                    return []
        
        return None
   
    
    def update_products(self, new_products: List[Dict]):
        """Update products cache (called saat auto-refresh)"""
        self.products = new_products
        print(f"[EXACT_MATCHER] Updated products cache: {len(new_products)} products")
