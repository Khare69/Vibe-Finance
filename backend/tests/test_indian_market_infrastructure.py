import time
import os
import sqlite3
from backend.data.universe import universe_engine
from backend.data.leaderboard_service import leaderboard_service
from backend.rag.filings_crawler import filings_crawler
from backend.data.market_cache import market_cache
from backend.data.rate_limiter import market_rate_limiter, market_circuit_breaker
from backend.data.session_manager import session_manager
from backend.personalization.portfolio import portfolio_service
from backend.rag.vector_store import vector_store

def test_nifty500_universe_autocomplete_and_resolution():
    """Scenario 26: NIFTY 500 Autocomplete & Zero-Latency Universe Resolution (<2ms)."""
    # 1. Total universe count
    total_symbols = len(universe_engine.stocks)
    assert total_symbols >= 500, f"Expected at least 500 symbols in NIFTY 500 metadata, got {total_symbols}"
    
    # 2. Search / Autocomplete functionality
    cochin_results = universe_engine.search("cochin")
    assert len(cochin_results) > 0, "Expected search for 'cochin' to return results"
    assert any(r["symbol"] == "COCHINSHIP" for r in cochin_results), "Expected COCHINSHIP in results for 'cochin'"
    
    zomato_results = universe_engine.search("zomato")
    assert len(zomato_results) > 0
    assert zomato_results[0]["symbol"] == "ZOMATO"
    assert zomato_results[0]["cap_tier"] in ["Large Cap", "Mid Cap"]
    
    cdsl_results = universe_engine.search("cdsl")
    assert len(cdsl_results) > 0
    assert cdsl_results[0]["symbol"] == "CDSL"
    
    tata_results = universe_engine.search("tata")
    assert len(tata_results) >= 4, f"Expected multiple Tata group stocks, got {len(tata_results)}"
    
    # 3. Ticker resolution to Yahoo Finance NSE symbol
    assert universe_engine.resolve_ticker("cochinship") == "COCHINSHIP.NS"
    assert universe_engine.resolve_ticker("ZOMATO") == "ZOMATO.NS"
    assert universe_engine.resolve_ticker("CDSL") == "CDSL.NS"
    assert universe_engine.resolve_ticker("RELIANCE.NS") == "RELIANCE.NS"
    assert universe_engine.resolve_ticker("NVDA") == "NVDA"
    
    # 4. Sector & Metadata Context
    cochin_meta = universe_engine.get_stock("COCHINSHIP")
    assert cochin_meta is not None
    assert "Shipyard" in cochin_meta["company_name"] or "Defense" in cochin_meta["sector"] or "Shipbuilding" in cochin_meta["sector"]
    
    # 5. Zero-latency benchmark (<2ms per operation)
    t0 = time.perf_counter()
    for _ in range(100):
        universe_engine.search("tata")
        universe_engine.resolve_ticker("INFY")
        universe_engine.get_stock("HDFCBANK")
    elapsed_ms = (time.perf_counter() - t0) * 1000
    avg_latency_ms = elapsed_ms / 300.0
    assert avg_latency_ms < 2.0, f"Lookup benchmark too slow: {avg_latency_ms:.3f}ms per operation (expected < 2.0ms)"


def test_sliding_window_leaderboard_engine():
    """Scenario 27: 5-Minute Sliding-Window Market Leaderboard Calculation & Monotonicity."""
    lb = leaderboard_service.get_leaderboard()
    assert lb["status"] == "success"
    assert "last_updated" in lb or "last_updated_iso" in lb
    assert 1 <= lb["seconds_until_next_refresh"] <= 300
    
    rankings = lb.get("rankings", {})
    top_gainers = rankings.get("top_gainers", [])
    top_losers = rankings.get("top_losers", [])
    volume_shockers = rankings.get("volume_shockers", [])
    momentum_leaders = rankings.get("momentum_leaders", [])
    
    assert len(top_gainers) >= 3, f"Expected at least 3 top gainers, got {len(top_gainers)}"
    assert len(top_losers) >= 3, f"Expected at least 3 top losers, got {len(top_losers)}"
    assert len(volume_shockers) >= 3, f"Expected at least 3 volume shockers, got {len(volume_shockers)}"
    assert len(momentum_leaders) >= 3, f"Expected at least 3 momentum leaders, got {len(momentum_leaders)}"
    
    # Verify Gainers Monotonicity (descending)
    for i in range(len(top_gainers) - 1):
        assert top_gainers[i]["change_percent"] >= top_gainers[i + 1]["change_percent"], (
            f"Top gainers not monotonic: {top_gainers[i]['change_percent']} < {top_gainers[i+1]['change_percent']}"
        )
    
    # Verify Losers Monotonicity (ascending)
    for i in range(len(top_losers) - 1):
        assert top_losers[i]["change_percent"] <= top_losers[i + 1]["change_percent"], (
            f"Top losers not monotonic: {top_losers[i]['change_percent']} > {top_losers[i+1]['change_percent']}"
        )
        
    # Verify Indian currency and NSE metadata
    for item in top_gainers:
        assert item["currency"] == "INR"
        assert item["price"] > 0
        assert item["ticker"].endswith(".NS") or not "." in item["ticker"]


def test_dynamic_midcap_ingestion_and_isolation():
    """Scenario 28: Dynamic Mid-Cap Ingestion Fallback Chain with Uncataloged Ticker Isolation."""
    # 1. Crawl filings for mid-cap Cochin Shipyard
    cochin_docs = filings_crawler.crawl_filings("COCHINSHIP")
    assert len(cochin_docs) >= 1, "Expected at least 1 document for COCHINSHIP"
    for doc in cochin_docs:
        assert ("document_title" in doc or "title" in doc)
        assert ("excerpt" in doc or "content" in doc)
        assert ("source_type" in doc or "doc_type" in doc)
        assert ("filing_date" in doc or "published_date" in doc)
        
    # 2. Strict isolation test: Uncataloged fake ticker "CUSTOMTECH"
    # Ensure vector_store does not leak spurious results
    fake_results = vector_store.search(ticker="CUSTOMTECH", query="CUSTOMTECH dividend and quarterly results", top_k=3)
    assert len(fake_results["citations"]) == 0, f"Expected 0 results for uncataloged ticker CUSTOMTECH, got {len(fake_results['citations'])}"
    assert fake_results["status"] == "UNCATALOGED_CORPUS"


def test_whatif_simulator_before_after_delta_indian_equity():
    """Scenario 29: 'What-If' Pre-Trade Simulator Before-vs-After Delta Verification."""
    initial_cash = 500000.0
    
    # 1. Simulate BUY 50 shares of high-beta Indian equity COCHINSHIP
    buy_sim = portfolio_service.simulate_trade({
        "ticker": "COCHINSHIP",
        "action": "BUY",
        "quantity": 50,
        "price": 1580.0,
        "portfolio_cash": initial_cash,
        "user_profile": {"risk_level": "conservative"}
    })
    
    assert buy_sim["ticker"] == "COCHINSHIP"
    assert buy_sim["action"] == "BUY"
    assert buy_sim["quantity"] == 50
    assert buy_sim["price"] == 1580.0
    
    expected_trade_amount = 50 * 1580.0  # 79000.0
    assert buy_sim["trade_amount"] == expected_trade_amount
    assert buy_sim["current_cash"] == initial_cash
    assert buy_sim["projected_cash"] == initial_cash - expected_trade_amount
    assert buy_sim["estimated_stt_charges"] > 0
    assert buy_sim["estimated_stt_charges"] == round(expected_trade_amount * 0.00115, 2)
    assert "Defense" in buy_sim["sector"] or "Shipyard" in buy_sim["sector"] or len(buy_sim["sector"]) > 0
    
    # Verify portfolio beta sensitivity
    delta = buy_sim["portfolio_delta"]
    assert "current_beta" in delta
    assert "projected_beta" in delta
    assert delta["projected_beta"] > delta["current_beta"]
    
    # 2. Simulate SELL 25 shares of TCS
    sell_sim = portfolio_service.simulate_trade({
        "ticker": "TCS",
        "action": "SELL",
        "quantity": 25,
        "price": 3950.0,
        "portfolio_cash": initial_cash
    })
    assert sell_sim["action"] == "SELL"
    sell_trade_amount = 25 * 3950.0
    assert sell_sim["trade_amount"] == sell_trade_amount
    assert sell_sim["projected_cash"] == initial_cash + sell_trade_amount


def test_sqlite_wal_cache_rate_limiter_and_circuit_breaker():
    """Scenario 30: Token Bucket Rate Limiter, SQLite WAL Cache & Circuit Breaker 60s 429 Cooldown."""
    # 1. SQLite WAL Cache Verification
    # Check that database is using WAL journal mode
    db_path = market_cache.db_path
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode;")
    mode = cur.fetchone()[0].lower()
    conn.close()
    assert mode == "wal", f"Expected SQLite WAL mode, got {mode}"
    
    # Test Cache Store and Retrieval
    test_data = {"ticker": "TESTCORP", "price": 1250.50, "currency": "INR"}
    market_cache.set("quote:TESTCORP", test_data, ttl_seconds=2, category="quote")
    
    cached = market_cache.get("quote:TESTCORP")
    assert cached is not None
    assert cached["price"] == 1250.50
    assert cached["currency"] == "INR"
    
    # Test Stale Data Retrieval
    stale = market_cache.get_stale("quote:TESTCORP")
    assert stale is not None
    assert stale["price"] == 1250.50
    
    # 2. Token Bucket Rate Limiter
    # Rate limiter allows 2.0 req/s, capacity 10.0
    assert market_rate_limiter.acquire(1.0) is True
    assert market_rate_limiter.tokens >= 0.0
    
    # 3. Circuit Breaker
    can_exec, _ = market_circuit_breaker.can_execute()
    assert can_exec is True
    assert market_circuit_breaker.state == "CLOSED"
    
    # Simulate HTTP 429 Too Many Requests
    market_circuit_breaker.record_429()
    assert market_circuit_breaker.state == "OPEN"
    can_exec_tripped, _ = market_circuit_breaker.can_execute()
    assert can_exec_tripped is False
    
    # Ensure cache serves stale during open circuit
    fallback_data = market_cache.get_stale("quote:TESTCORP")
    assert fallback_data is not None
    assert fallback_data["price"] == 1250.50
    
    # Reset Circuit Breaker
    market_circuit_breaker.record_success()
    assert market_circuit_breaker.state == "CLOSED"
    can_exec_reset, _ = market_circuit_breaker.can_execute()
    assert can_exec_reset is True
    
    # 4. Session Manager
    headers = session_manager.get_headers()
    assert "User-Agent" in headers
    assert "Mozilla/5.0" in headers["User-Agent"]
    assert "Accept-Language" in headers
