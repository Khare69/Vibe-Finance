import os
import json
import sqlite3
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from backend.models import UserProfileDB, PortfolioHoldingDB, WatchlistDB, DecisionMemoDB

DB_PATH = os.path.join(os.path.dirname(__file__), "vibe_finance.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables and seeds baseline data if not present."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
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

        # Portfolio Holdings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_holdings (
                ticker TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                shares REAL NOT NULL,
                avg_cost REAL NOT NULL,
                currency TEXT NOT NULL,
                sector TEXT NOT NULL,
                beta REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Watchlist Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlists (
                ticker TEXT PRIMARY KEY,
                target_price REAL,
                notes TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # Decision Memos Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_memos (
                id TEXT PRIMARY KEY,
                ticker TEXT NOT NULL,
                company_name TEXT NOT NULL,
                memo_markdown TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()

        # Seed initial user profile if empty
        cursor.execute("SELECT COUNT(*) as cnt FROM user_profiles")
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

        # Seed initial holdings if empty
        cursor.execute("SELECT COUNT(*) as cnt FROM portfolio_holdings")
        if cursor.fetchone()["cnt"] == 0:
            seeds = [
                ("RELIANCE", "Reliance Industries Ltd.", 50.0, 2720.00, "INR", "Energy", 0.88),
                ("TCS", "Tata Consultancy Services Ltd.", 30.0, 3850.00, "INR", "Tech", 0.72),
                ("AAPL", "Apple Inc.", 35.0, 215.00, "USD", "Tech", 1.05),
                ("HDFCBANK", "HDFC Bank Ltd.", 40.0, 1640.00, "INR", "Financials", 0.92)
            ]
            for s in seeds:
                cursor.execute("""
                    INSERT INTO portfolio_holdings (ticker, company_name, shares, avg_cost, currency, sector, beta, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (*s, datetime.now(timezone.utc).isoformat()))

        conn.commit()

# --- Repository Methods ---

def get_user_profile(user_id: str = "default_user") -> UserProfileDB:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            # Fallback default
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

def get_all_holdings() -> List[PortfolioHoldingDB]:
    init_db()
    holdings = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM portfolio_holdings ORDER BY ticker ASC")
        for row in cursor.fetchall():
            holdings.append(PortfolioHoldingDB(
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

def upsert_holding(holding: PortfolioHoldingDB) -> PortfolioHoldingDB:
    init_db()
    holding.updated_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO portfolio_holdings (ticker, company_name, shares, avg_cost, currency, sector, beta, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticker) DO UPDATE SET
                company_name=excluded.company_name,
                shares=excluded.shares,
                avg_cost=excluded.avg_cost,
                currency=excluded.currency,
                sector=excluded.sector,
                beta=excluded.beta,
                updated_at=excluded.updated_at
        """, (
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

def delete_holding(ticker: str) -> bool:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM portfolio_holdings WHERE ticker = ?", (ticker.upper(),))
        conn.commit()
        return cursor.rowcount > 0

def get_watchlist() -> List[WatchlistDB]:
    init_db()
    watchlist = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM watchlists ORDER BY created_at DESC")
        for row in cursor.fetchall():
            watchlist.append(WatchlistDB(
                ticker=row["ticker"],
                target_price=row["target_price"],
                notes=row["notes"],
                created_at=row["created_at"]
            ))
    return watchlist

def add_to_watchlist(item: WatchlistDB) -> WatchlistDB:
    init_db()
    item.created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO watchlists (ticker, target_price, notes, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(ticker) DO UPDATE SET
                target_price=excluded.target_price,
                notes=excluded.notes
        """, (
            item.ticker.upper(),
            item.target_price,
            item.notes,
            item.created_at
        ))
        conn.commit()
    return item

def remove_from_watchlist(ticker: str) -> bool:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM watchlists WHERE ticker = ?", (ticker.upper(),))
        conn.commit()
        return cursor.rowcount > 0

def save_memo(memo: DecisionMemoDB) -> DecisionMemoDB:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO decision_memos (id, ticker, company_name, memo_markdown, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                memo_markdown=excluded.memo_markdown
        """, (
            memo.id,
            memo.ticker.upper(),
            memo.company_name,
            memo.memo_markdown,
            memo.created_at
        ))
        conn.commit()
    return memo

def get_memos(limit: int = 20) -> List[DecisionMemoDB]:
    init_db()
    memos = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM decision_memos ORDER BY created_at DESC LIMIT ?", (limit,))
        for row in cursor.fetchall():
            memos.append(DecisionMemoDB(
                id=row["id"],
                ticker=row["ticker"],
                company_name=row["company_name"],
                memo_markdown=row["memo_markdown"],
                created_at=row["created_at"]
            ))
    return memos


# --- Non-Blocking Asynchronous Database Wrappers ---

async def get_user_profile_async(user_id: str = "default_user") -> UserProfileDB:
    return await asyncio.to_thread(get_user_profile, user_id)

async def upsert_user_profile_async(profile: UserProfileDB) -> UserProfileDB:
    return await asyncio.to_thread(upsert_user_profile, profile)

async def get_all_holdings_async() -> List[PortfolioHoldingDB]:
    return await asyncio.to_thread(get_all_holdings)

async def upsert_holding_async(holding: PortfolioHoldingDB) -> PortfolioHoldingDB:
    return await asyncio.to_thread(upsert_holding, holding)

async def delete_holding_async(ticker: str) -> bool:
    return await asyncio.to_thread(delete_holding, ticker)

async def get_watchlist_async() -> List[WatchlistDB]:
    return await asyncio.to_thread(get_watchlist)

async def add_to_watchlist_async(item: WatchlistDB) -> WatchlistDB:
    return await asyncio.to_thread(add_to_watchlist, item)

async def remove_from_watchlist_async(ticker: str) -> bool:
    return await asyncio.to_thread(remove_from_watchlist, ticker)

async def save_memo_async(memo: DecisionMemoDB) -> DecisionMemoDB:
    return await asyncio.to_thread(save_memo, memo)

async def get_memos_async(limit: int = 20) -> List[DecisionMemoDB]:
    return await asyncio.to_thread(get_memos, limit)

