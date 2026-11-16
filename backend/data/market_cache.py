"""
Zero-Dependency SQLite WAL Market Cache Layer
Enables high-concurrency non-blocking reads for parallel Multi-Agent workers
(Quant, Fundamental, Risk) with in-memory micro-cache and multi-tier TTLs.
"""

import os
import json
import sqlite3
import time
from typing import Any, Optional, Dict

CACHE_TTL_QUOTE = 300          # 5 minutes
CACHE_TTL_HISTORY = 86400      # 24 hours
CACHE_TTL_FILINGS = 604800     # 7 days

class SQLiteMarketCache:
    _instance = None

    def __new__(cls, db_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(SQLiteMarketCache, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        if self._initialized:
            return
        if not db_path:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "market_cache.db")
        self.db_path = db_path
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._init_db()
        self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_cache (
                    key TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    data TEXT NOT NULL,
                    expires_at REAL NOT NULL,
                    created_at REAL NOT NULL
                );
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_expires ON market_cache (expires_at);
            """)
            conn.commit()

    def get(self, key: str) -> Optional[Any]:
        """Returns non-expired data from memory micro-cache or SQLite."""
        now = time.time()
        # 1. Check in-memory micro-cache
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if entry["expires_at"] > now:
                return entry["data"]
            else:
                del self._memory_cache[key]

        # 2. Check SQLite WAL
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT data, expires_at FROM market_cache WHERE key = ?",
                    (key,)
                )
                row = cur.fetchone()
                if row:
                    expires_at = float(row["expires_at"])
                    if expires_at > now:
                        val = json.loads(row["data"])
                        self._memory_cache[key] = {"data": val, "expires_at": expires_at}
                        return val
        except Exception as e:
            print(f"[MarketCache] Read error for {key}: {e}")
        return None

    def get_stale(self, key: str) -> Optional[Any]:
        """
        Returns data even if expired.
        Used by the Circuit Breaker during 429 backoff to serve stale data safely.
        """
        if key in self._memory_cache:
            return self._memory_cache[key]["data"]

        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT data FROM market_cache WHERE key = ?", (key,))
                row = cur.fetchone()
                if row:
                    return json.loads(row["data"])
        except Exception as e:
            print(f"[MarketCache] Stale read error for {key}: {e}")
        return None

    def set(self, key: str, data: Any, ttl_seconds: float, category: str = "quote"):
        now = time.time()
        expires_at = now + ttl_seconds
        serialized = json.dumps(data)

        # Update in-memory micro-cache
        self._memory_cache[key] = {"data": data, "expires_at": expires_at}

        # Persist to SQLite WAL
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO market_cache (key, category, data, expires_at, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        category=excluded.category,
                        data=excluded.data,
                        expires_at=excluded.expires_at,
                        created_at=excluded.created_at;
                """, (key, category, serialized, expires_at, now))
                conn.commit()
        except Exception as e:
            print(f"[MarketCache] Write error for {key}: {e}")

    def clear_expired(self):
        now = time.time()
        # Clean memory
        self._memory_cache = {k: v for k, v in self._memory_cache.items() if v["expires_at"] > now}
        # Clean SQLite
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM market_cache WHERE expires_at < ?", (now,))
                conn.commit()
        except Exception as e:
            print(f"[MarketCache] Eviction error: {e}")

# Singleton instance
market_cache = SQLiteMarketCache()
