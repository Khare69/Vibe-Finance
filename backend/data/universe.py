"""
NIFTY 500 Universe Engine
In-memory fast prefix, substring, and fuzzy search engine for Indian NSE/BSE equities.
Provides zero-latency ticker resolution and sector mapping.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional

class StockUniverse:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StockUniverse, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._stocks: List[Dict[str, Any]] = []
        self._symbol_map: Dict[str, Dict[str, Any]] = {}
        self._load_universe()
        self._initialized = True

    def _load_universe(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        metadata_file = os.path.join(current_dir, "nifty500_metadata.json")
        
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    self._stocks = json.load(f)
            except Exception as e:
                print(f"[Universe] Error loading nifty500_metadata.json: {e}")
                self._stocks = []
        
        # Build lookup index
        self._symbol_map = {}
        for s in self._stocks:
            sym = s["symbol"].upper()
            self._symbol_map[sym] = s
            # Also index ticker without .NS
            if sym.endswith(".NS"):
                self._symbol_map[sym[:-3]] = s
            else:
                self._symbol_map[f"{sym}.NS"] = s

    def reload(self):
        self._initialized = False
        self.__init__()

    def get_stock(self, symbol_or_ticker: str) -> Optional[Dict[str, Any]]:
        if not symbol_or_ticker:
            return None
        cleaned = symbol_or_ticker.strip().upper()
        # Direct lookup
        if cleaned in self._symbol_map:
            return self._symbol_map[cleaned]
        # Strip .NS or .BO suffix
        base = re.sub(r'\.(NS|BO)$', '', cleaned)
        if base in self._symbol_map:
            return self._symbol_map[base]
        # Search by company name exact match
        for s in self._stocks:
            if s["company_name"].upper() == cleaned:
                return s
        return None

    def resolve_ticker(self, query: str) -> str:
        """
        Resolves any user-entered text (e.g. 'Zomato', 'cochin ship', 'RIL', 'TCS.NS')
        to its canonical Yahoo Finance NSE ticker (e.g. 'ZOMATO.NS', 'COCHINSHIP.NS').
        """
        if not query:
            return "RELIANCE.NS"
        stock = self.get_stock(query)
        if stock:
            return stock.get("ticker", f"{stock['symbol']}.NS")
        
        # Fuzzy match top candidate
        matches = self.search(query, limit=1)
        if matches:
            return matches[0].get("ticker", f"{matches[0]['symbol']}.NS")
        
        # Fallback normalization
        cleaned = query.strip().upper()
        if not cleaned.endswith(".NS") and not cleaned.endswith(".BO"):
            return f"{cleaned}.NS"
        return cleaned

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fast multi-factor relevance ranking:
        1. Exact symbol match (Score 100)
        2. Symbol prefix match (Score 80)
        3. Company name prefix match (Score 60)
        4. Alias/Keyword match (Score 50)
        5. Substring in Symbol (Score 40)
        6. Substring in Company Name (Score 30)
        """
        if not query or not query.strip():
            # Return top large-caps by default
            return self._stocks[:limit]

        q = query.strip().lower()
        scored: List[tuple[int, Dict[str, Any]]] = []

        for s in self._stocks:
            sym_lower = s["symbol"].lower()
            name_lower = s["company_name"].lower()
            keywords = s.get("keywords", [])
            score = 0

            if sym_lower == q:
                score = 100
            elif sym_lower.startswith(q):
                score = 80
            elif name_lower.startswith(q):
                score = 65
            elif any(k == q for k in keywords):
                score = 55
            elif any(k.startswith(q) for k in keywords):
                score = 50
            elif q in sym_lower:
                score = 40
            elif q in name_lower:
                score = 30
            elif any(q in k for k in keywords):
                score = 25

            if score > 0:
                # Add slight bonus for Large Cap
                tier_bonus = 5 if s.get("cap_tier") == "Large Cap" else (2 if s.get("cap_tier") == "Mid Cap" else 0)
                scored.append((score + tier_bonus, s))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]

    def get_all_symbols(self) -> List[str]:
        return [s["symbol"] for s in self._stocks]

    def get_all_stocks(self) -> List[Dict[str, Any]]:
        return list(self._stocks)

    def get_sector_stocks(self, sector: str) -> List[Dict[str, Any]]:
        return [s for s in self._stocks if s.get("sector", "").lower() == sector.lower()]

    def get_top_stocks(self, n: int = 50) -> List[Dict[str, Any]]:
        return self._stocks[:n]

# Singleton instance
universe_engine = StockUniverse()
