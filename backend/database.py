import os
import json
import sqlite3
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from backend.models import (
    UserDB,
    UserProfileDB,
    PortfolioHoldingDB,
    WatchlistDB,
    DecisionMemoDB
)
from backend.auth.security import hash_password

DB_PATH = os.path.join(os.path.dirname(__file__), "vibe_finance.db")
_db_initialized = False

def get_connection():
    """Returns a SQLite connection configured with WAL journal mode and busy timeout for high concurrency."""
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

def init_db(force: bool = False):
    """
    Initializes tables, executes multi-tenant schema migrations, and seeds baseline data strictly once.
    Tracks one-time seeding completion in `app_metadata` to permanently prevent
    the auto-reseeding bug when a user clears all portfolio holdings.
    """
    global _db_initialized
    if _db_initialized and not force:
        return

    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Metadata / Migration Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Users Table (E.2 Authentication)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                email TEXT,
                role TEXT NOT NULL DEFAULT 'investor',
                created_at TEXT NOT NULL
            )
        """)

        # User Profile Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id TEXT PRIMARY KEY,
                risk_level TEXT NOT NULL,
                investment_horizon TEXT NOT NULL,
                panic_sell_tendency REAL NOT NULL,
                preferred_sectors TEXT NOT NULL,
                portfolio_cash REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # --- Multi-Tenant Table Migrations ---

        # 1. Portfolio Holdings Table Migration (composite key user_id, ticker)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='portfolio_holdings'")
        holdings_exists = cursor.fetchone() is not None

        if holdings_exists:
            cursor.execute("PRAGMA table_info(portfolio_holdings)")
            cols = [col["name"] for col in cursor.fetchall()]
            if "user_id" not in cols:
                # Migrate to composite primary key (user_id, ticker)
                cursor.execute("""
                    CREATE TABLE portfolio_holdings_v2 (
                        user_id TEXT NOT NULL DEFAULT 'default_user',
                        ticker TEXT NOT NULL,
                        company_name TEXT NOT NULL,
                        shares REAL NOT NULL,
                        avg_cost REAL NOT NULL,
                        currency TEXT NOT NULL,
                        sector TEXT NOT NULL,
                        beta REAL NOT NULL,
                        updated_at TEXT NOT NULL,
                        PRIMARY KEY (user_id, ticker)
                    )
                """)
                cursor.execute("""
                    INSERT INTO portfolio_holdings_v2 (user_id, ticker, company_name, shares, avg_cost, currency, sector, beta, updated_at)
                    SELECT 'default_user', ticker, company_name, shares, avg_cost, currency, sector, beta, updated_at FROM portfolio_holdings
                """)
                cursor.execute("DROP TABLE portfolio_holdings")
                cursor.execute("ALTER TABLE portfolio_holdings_v2 RENAME TO portfolio_holdings")
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_holdings (
                    user_id TEXT NOT NULL DEFAULT 'default_user',
                    ticker TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    shares REAL NOT NULL,
                    avg_cost REAL NOT NULL,
                    currency TEXT NOT NULL,
                    sector TEXT NOT NULL,
                    beta REAL NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, ticker)
                )
            """)

        # 2. Watchlist Table Migration (composite key user_id, ticker)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='watchlists'")
        watchlists_exists = cursor.fetchone() is not None

        if watchlists_exists:
            cursor.execute("PRAGMA table_info(watchlists)")
            cols = [col["name"] for col in cursor.fetchall()]
            if "user_id" not in cols:
                cursor.execute("""
                    CREATE TABLE watchlists_v2 (
                        user_id TEXT NOT NULL DEFAULT 'default_user',
                        ticker TEXT NOT NULL,
                        target_price REAL,
                        notes TEXT,
                        created_at TEXT NOT NULL,
                        PRIMARY KEY (user_id, ticker)
                    )
                """)
                cursor.execute("""
                    INSERT INTO watchlists_v2 (user_id, ticker, target_price, notes, created_at)
                    SELECT 'default_user', ticker, target_price, notes, created_at FROM watchlists
                """)
                cursor.execute("DROP TABLE watchlists")
                cursor.execute("ALTER TABLE watchlists_v2 RENAME TO watchlists")
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS watchlists (
                    user_id TEXT NOT NULL DEFAULT 'default_user',
                    ticker TEXT NOT NULL,
                    target_price REAL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, ticker)
                )
            """)

        # 3. Decision Memos Table Migration
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='decision_memos'")
        memos_exists = cursor.fetchone() is not None

        if memos_exists:
            cursor.execute("PRAGMA table_info(decision_memos)")
            cols = [col["name"] for col in cursor.fetchall()]
            if "user_id" not in cols:
                cursor.execute("ALTER TABLE decision_memos ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default_user'")
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decision_memos (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL DEFAULT 'default_user',
                    ticker TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    memo_markdown TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decision_memos_user ON decision_memos (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_holdings_user ON portfolio_holdings (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_watchlists_user ON watchlists (user_id)")

        conn.commit()

        # Seed baseline demo user in `users` table if absent
        cursor.execute("SELECT id FROM users WHERE username = 'demo_user'")
        if not cursor.fetchone():
            demo_pw_hash = hash_password("DemoUser@2026")
            cursor.execute("""
                INSERT OR IGNORE INTO users (id, username, hashed_password, email, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "default_user",
                "demo_user",
                demo_pw_hash,
                "demo@vibefinance.internal",
                "investor",
                datetime.now(timezone.utc).isoformat()
            ))

        # Check if initial one-time seed has already been recorded
        cursor.execute("SELECT value FROM app_metadata WHERE key = 'initial_seed_completed'")
        seed_meta = cursor.fetchone()

        if not seed_meta:
            # Seed initial user profile for default_user if empty
            cursor.execute("SELECT COUNT(*) as cnt FROM user_profiles WHERE id = 'default_user'")
            if cursor.fetchone()["cnt"] == 0:
                cursor.execute("""
                    INSERT INTO user_profiles (id, risk_level, investment_horizon, panic_sell_tendency, preferred_sectors, portfolio_cash, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    "default_user",
                    "conservative",
                    "medium",
                    0.8,
                    json.dumps(["Energy", "Tech"]),
                    250000.0,
                    datetime.now(timezone.utc).isoformat()
                ))

            # Seed initial holdings for default_user if empty
            cursor.execute("SELECT COUNT(*) as cnt FROM portfolio_holdings WHERE user_id = 'default_user'")
            if cursor.fetchone()["cnt"] == 0:
                seeds = [
                    ("default_user", "RELIANCE", "Reliance Industries Ltd.", 50.0, 2720.00, "INR", "Energy", 0.88),
                    ("default_user", "TCS", "Tata Consultancy Services Ltd.", 30.0, 3850.00, "INR", "Tech", 0.72),
                    ("default_user", "AAPL", "Apple Inc.", 35.0, 215.00, "USD", "Tech", 1.05),
                    ("default_user", "HDFCBANK", "HDFC Bank Ltd.", 40.0, 1640.00, "INR", "Financials", 0.92)
                ]
                for s in seeds:
                    cursor.execute("""
                        INSERT INTO portfolio_holdings (user_id, ticker, company_name, shares, avg_cost, currency, sector, beta, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (*s, datetime.now(timezone.utc).isoformat()))

            # Record that one-time initial seed completed
            cursor.execute("""
                INSERT OR REPLACE INTO app_metadata (key, value, created_at)
                VALUES ('initial_seed_completed', 'true', ?)
            """, (datetime.now(timezone.utc).isoformat(),))
            conn.commit()

    _db_initialized = True


# --- User Authentication Repository Methods ---

def create_user(user: UserDB) -> UserDB:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (id, username, hashed_password, email, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user.id,
            user.username,
            user.hashed_password,
            user.email,
            user.role,
            user.created_at
        ))
        conn.commit()
    return user


def get_user_by_username(username: str) -> Optional[UserDB]:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username.strip(),))
        row = cursor.fetchone()
        if not row:
            return None
        return UserDB(
            id=row["id"],
            username=row["username"],
            hashed_password=row["hashed_password"],
            email=row["email"],
            role=row["role"],
            created_at=row["created_at"]
        )


def get_user_by_id(user_id: str) -> Optional[UserDB]:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id.strip(),))
        row = cursor.fetchone()
        if not row:
            return None
        return UserDB(
            id=row["id"],
            username=row["username"],
            hashed_password=row["hashed_password"],
            email=row["email"],
            role=row["role"],
            created_at=row["created_at"]
        )


# --- Multi-Tenant Repository Methods ---

def get_user_profile(user_id: str = "default_user") -> UserProfileDB:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return UserProfileDB(id=user_id)
        
        sectors = json.loads(row["preferred_sectors"]) if row["preferred_sectors"] else ["Energy", "Tech"]
        return UserProfileDB(
            id=row["id"],
            risk_level=row["risk_level"],
            investment_horizon=row["investment_horizon"],
            panic_sell_tendency=row["panic_sell_tendency"],
            preferred_sectors=sectors,
            portfolio_cash=row["portfolio_cash"],
            updated_at=row["updated_at"]
        )


def upsert_user_profile(profile: UserProfileDB) -> UserProfileDB:
    init_db()
    profile.updated_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_profiles (id, risk_level, investment_horizon, panic_sell_tendency, preferred_sectors, portfolio_cash, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                risk_level=excluded.risk_level,
                investment_horizon=excluded.investment_horizon,
                panic_sell_tendency=excluded.panic_sell_tendency,
                preferred_sectors=excluded.preferred_sectors,
                portfolio_cash=excluded.portfolio_cash,
                updated_at=excluded.updated_at
        """, (
            profile.id,
            profile.risk_level,
            profile.investment_horizon,
            profile.panic_sell_tendency,
            json.dumps(profile.preferred_sectors),
            profile.portfolio_cash,
            profile.updated_at
        ))
        conn.commit()
    return profile


def get_all_holdings(user_id: str = "default_user") -> List[PortfolioHoldingDB]:
    init_db()
    holdings = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM portfolio_holdings WHERE user_id = ? ORDER BY ticker ASC", (user_id,))
        for row in cursor.fetchall():
            holdings.append(PortfolioHoldingDB(
                user_id=row["user_id"],
                ticker=row["ticker"],
                company_name=row["company_name"],
                shares=row["shares"],
                avg_cost=row["avg_cost"],
                currency=row["currency"],
                sector=row["sector"],
                beta=row["beta"],
                updated_at=row["updated_at"]
            ))
    return holdings


def upsert_holding(holding: PortfolioHoldingDB, user_id: str = "default_user") -> PortfolioHoldingDB:
    init_db()
    holding.user_id = user_id
    holding.updated_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO portfolio_holdings (user_id, ticker, company_name, shares, avg_cost, currency, sector, beta, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, ticker) DO UPDATE SET
                company_name=excluded.company_name,
                shares=excluded.shares,
                avg_cost=excluded.avg_cost,
                currency=excluded.currency,
                sector=excluded.sector,
                beta=excluded.beta,
                updated_at=excluded.updated_at
        """, (
            holding.user_id,
            holding.ticker.upper(),
            holding.company_name,
            holding.shares,
            holding.avg_cost,
            holding.currency,
            holding.sector,
            holding.beta,
            holding.updated_at
        ))
        conn.commit()
    return holding


def delete_holding(ticker: str, user_id: str = "default_user") -> bool:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM portfolio_holdings WHERE user_id = ? AND ticker = ?", (user_id, ticker.upper()))
        conn.commit()
        return cursor.rowcount > 0


def clear_all_holdings(user_id: str = "default_user") -> int:
    """Safely deletes all portfolio holdings for a specific tenant without triggering re-seeding."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM portfolio_holdings WHERE user_id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount


def get_watchlist(user_id: str = "default_user") -> List[WatchlistDB]:
    init_db()
    watchlist = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM watchlists WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        for row in cursor.fetchall():
            watchlist.append(WatchlistDB(
                user_id=row["user_id"],
                ticker=row["ticker"],
                target_price=row["target_price"],
                notes=row["notes"],
                created_at=row["created_at"]
            ))
    return watchlist


def add_to_watchlist(item: WatchlistDB, user_id: str = "default_user") -> WatchlistDB:
    init_db()
    item.user_id = user_id
    item.created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO watchlists (user_id, ticker, target_price, notes, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, ticker) DO UPDATE SET
                target_price=excluded.target_price,
                notes=excluded.notes
        """, (
            item.user_id,
            item.ticker.upper(),
            item.target_price,
            item.notes,
            item.created_at
        ))
        conn.commit()
    return item


def remove_from_watchlist(ticker: str, user_id: str = "default_user") -> bool:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM watchlists WHERE user_id = ? AND ticker = ?", (user_id, ticker.upper()))
        conn.commit()
        return cursor.rowcount > 0


def save_memo(memo: DecisionMemoDB, user_id: str = "default_user") -> DecisionMemoDB:
    init_db()
    memo.user_id = user_id
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO decision_memos (id, user_id, ticker, company_name, memo_markdown, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                memo_markdown=excluded.memo_markdown
        """, (
            memo.id,
            memo.user_id,
            memo.ticker.upper(),
            memo.company_name,
            memo.memo_markdown,
            memo.created_at
        ))
        conn.commit()
    return memo


def get_memos(limit: int = 20, user_id: str = "default_user") -> List[DecisionMemoDB]:
    init_db()
    memos = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM decision_memos WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
        for row in cursor.fetchall():
            memos.append(DecisionMemoDB(
                id=row["id"],
                user_id=row["user_id"],
                ticker=row["ticker"],
                company_name=row["company_name"],
                memo_markdown=row["memo_markdown"],
                created_at=row["created_at"]
            ))
    return memos


def delete_memo(memo_id: str, user_id: str = "default_user") -> bool:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM decision_memos WHERE user_id = ? AND id = ?", (user_id, memo_id))
        conn.commit()
        return cursor.rowcount > 0


# --- Non-Blocking Asynchronous Database Wrappers ---

async def create_user_async(user: UserDB) -> UserDB:
    return await asyncio.to_thread(create_user, user)

async def get_user_by_username_async(username: str) -> Optional[UserDB]:
    return await asyncio.to_thread(get_user_by_username, username)

async def get_user_by_id_async(user_id: str) -> Optional[UserDB]:
    return await asyncio.to_thread(get_user_by_id, user_id)

async def get_user_profile_async(user_id: str = "default_user") -> UserProfileDB:
    return await asyncio.to_thread(get_user_profile, user_id)

async def upsert_user_profile_async(profile: UserProfileDB) -> UserProfileDB:
    return await asyncio.to_thread(upsert_user_profile, profile)

async def get_all_holdings_async(user_id: str = "default_user") -> List[PortfolioHoldingDB]:
    return await asyncio.to_thread(get_all_holdings, user_id)

async def upsert_holding_async(holding: PortfolioHoldingDB, user_id: str = "default_user") -> PortfolioHoldingDB:
    return await asyncio.to_thread(upsert_holding, holding, user_id)

async def delete_holding_async(ticker: str, user_id: str = "default_user") -> bool:
    return await asyncio.to_thread(delete_holding, ticker, user_id)

async def clear_all_holdings_async(user_id: str = "default_user") -> int:
    return await asyncio.to_thread(clear_all_holdings, user_id)

async def get_watchlist_async(user_id: str = "default_user") -> List[WatchlistDB]:
    return await asyncio.to_thread(get_watchlist, user_id)

async def add_to_watchlist_async(item: WatchlistDB, user_id: str = "default_user") -> WatchlistDB:
    return await asyncio.to_thread(add_to_watchlist, item, user_id)

async def remove_from_watchlist_async(ticker: str, user_id: str = "default_user") -> bool:
    return await asyncio.to_thread(remove_from_watchlist, ticker, user_id)

async def save_memo_async(memo: DecisionMemoDB, user_id: str = "default_user") -> DecisionMemoDB:
    return await asyncio.to_thread(save_memo, memo, user_id)

async def get_memos_async(limit: int = 20, user_id: str = "default_user") -> List[DecisionMemoDB]:
    return await asyncio.to_thread(get_memos, limit, user_id)

async def delete_memo_async(memo_id: str, user_id: str = "default_user") -> bool:
    return await asyncio.to_thread(delete_memo, memo_id, user_id)
