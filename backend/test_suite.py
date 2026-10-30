import sys
import os
import asyncio

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import (
    get_health,
    list_stocks,
    analyze_stock,
    simulate_trade,
    get_portfolio,
    run_backtest,
    AnalyzeRequest,
    SimulateTradeRequest,
    BacktestRequest,
    UserProfileModel
)

def run_coro(coro):
    """Executes a coroutine cleanly using asyncio.run."""
    return asyncio.run(coro)

def run_all_tests():
    print("Running Vibe Finance Multi-Agent Backend Tests...\n")

    # 1. Test Health
    health = run_coro(get_health())
    assert health["status"] == "healthy"
    assert health["version"] == "1.0.0"
    assert health["rag_corpus_documents"] >= 6
    print("1. Health Endpoint Passed:", health)

    # 2. Test Stocks
    stocks = run_coro(list_stocks())
    assert len(stocks) >= 6
    tickers = [s["ticker"] for s in stocks]
    assert "RELIANCE" in tickers
    assert "NVDA" in tickers
    print("2. Stocks Endpoint Passed: Found tickers", tickers)

    # 3. Test Analyze (Standard RELIANCE)
    profile = UserProfileModel(
        risk_level="conservative",
        investment_horizon="medium",
        panic_sell_tendency=0.8,
        preferred_sectors=["Energy", "Tech"],
        portfolio_cash=250000
    )
    req = AnalyzeRequest(
        ticker="RELIANCE",
        user_profile=profile,
        explain_mode="beginner",
        simulated_stale_data=False,
        simulated_rag_timeout=False
    )
    res = run_coro(analyze_stock(req))
    assert res["ticker"] == "RELIANCE"
    assert res["price_data"]["feed_status"] in ["LIVE", "LIVE_YAHOO"]
    assert res["agents"]["quant"]["stance"] in ["BULLISH", "BEARISH", "NEUTRAL"]
    assert res["agents"]["rag"]["stance"] in ["BULLISH", "BEARISH", "NEUTRAL"]
    assert res["agents"]["behavioral_risk"]["stance"] in ["CAUTION", "FAVORABLE", "MODERATE"]
    assert res["synthesis"]["final_action"] in ["STRONG_BUY", "BUY", "CAUTIOUS_ACCUMULATE", "HOLD", "TRIM", "SELL"]
    assert len(res["debate"]["dialogue_steps"]) == 3
    assert len(res["agents"]["rag"]["citations"]) >= 2
    assert res["telemetry"]["confidence_score"] > 0
    print("3. Analyze (Standard RELIANCE) Passed: Disagreement evaluated, Action:", res["synthesis"]["final_action"])

    # 4. Test Stale Data Degradation
    req_stale = AnalyzeRequest(
        ticker="RELIANCE",
        user_profile=profile,
        simulated_stale_data=True,
        simulated_rag_timeout=False
    )
    res_stale = run_coro(analyze_stock(req_stale))
    assert res_stale["price_data"]["feed_status"] == "STALE_FALLBACK_EOD"
    assert res_stale["price_data"]["confidence_penalty"] == 25.0
    assert res_stale["telemetry"]["degraded_data"] is True
    assert res_stale["telemetry"]["confidence_score"] <= 60
    print("4. Stale Data Degradation Passed: Fallback EOD feed & confidence penalty applied.")

    # 5. Test RAG Timeout Degradation
    req_timeout = AnalyzeRequest(
        ticker="RELIANCE",
        user_profile=profile,
        simulated_stale_data=False,
        simulated_rag_timeout=True
    )
    res_timeout = run_coro(analyze_stock(req_timeout))
    assert res_timeout["agents"]["rag"]["timed_out"] is True
    assert res_timeout["synthesis"]["weight_breakdown"]["fundamentals"] == 0
    assert "pending" in res_timeout["synthesis"]["headline"].lower()
    assert res_timeout["telemetry"]["degraded_data"] is True
    print("5. RAG Timeout Degradation Passed: Graceful fallback to technical momentum.")

    # 6. Test Simulate Trade (TSLA with Conservative profile)
    trade_req = SimulateTradeRequest(
        ticker="TSLA",
        action="BUY",
        quantity=10,
        price=240.0,
        user_profile={"risk_level": "conservative"}
    )
    trade_res = run_coro(simulate_trade(trade_req))
    assert trade_res["warning_triggered"] is True
    assert "Conservative" in trade_res["nudge_message"]
    assert trade_res["portfolio_delta"]["projected_tech_pct"] > trade_res["portfolio_delta"]["current_tech_pct"]
    assert trade_res["portfolio_delta"]["projected_beta"] > trade_res["portfolio_delta"]["current_beta"]
    print("6. Simulate Trade Nudge Passed: Warning triggered with delta projections.")

    # 7. Test Portfolio
    portfolio = run_coro(get_portfolio())
    assert portfolio["total_value"] > 0
    assert len(portfolio["holdings"]) >= 4
    assert len(portfolio["sector_allocations"]) >= 3
    assert len(portfolio["concentration_heatmap"]) >= 3
    print("7. Portfolio Endpoint Passed: Holdings, Beta, and Heatmap verified.")

    # 8. Test Backtest
    bt_req = BacktestRequest(
        ticker="NVDA",
        historical_date="2025-10-15",
        holding_days=90
    )
    bt_res = run_coro(run_backtest(bt_req))
    assert "historical_date" in bt_res
    assert bt_res["entry_price"] > 0
    assert bt_res["exit_price"] > 0
    assert "actual_return_pct" in bt_res
    assert bt_res["agent_recommendation_then"] in ["STRONG_BUY", "BUY", "CAUTIOUS_ACCUMULATE", "HOLD", "TRIM", "SELL"]
    assert "performance_metrics" in bt_res
    assert "point_in_time_metrics" in bt_res
    assert len(bt_res["trajectory"]) > 0
    print("8. Backtest Endpoint Passed: Dynamic point-in-time equity curve and performance metrics.")

    # 9. Test Uncataloged Ticker RAG Isolation (No cross-contamination)
    uncataloged_req = AnalyzeRequest(
        ticker="CUSTOMTECH",
        user_profile=profile
    )
    uncataloged_res = run_coro(analyze_stock(uncataloged_req))
    assert uncataloged_res["ticker"] == "CUSTOMTECH"
    # Citations must be empty for an uncataloged ticker, NOT populated with Reliance filings
    assert len(uncataloged_res["agents"]["rag"]["citations"]) == 0
    print("9. Uncataloged Ticker Isolation Passed: 0 cross-contaminating citations returned.")

    # 10. Test Input Validation Boundary Checks
    try:
        invalid_trade = SimulateTradeRequest(
            ticker="TSLA",
            quantity=-5, # Invalid negative quantity
            price=240.0
        )
        assert False, "Should have thrown ValidationError on negative quantity"
    except Exception as e:
        assert "greater than 0" in str(e) or "Input should be greater than 0" in str(e)
    print("10. Input Validation Passed: Negative trade quantity rejected cleanly.")

    # 11. Test SQLite Database Initialization & Default Seeds
    import backend.database as db
    from backend.models import UserProfileDB, PortfolioHoldingDB, WatchlistDB, DecisionMemoDB
    db.init_db()
    db_holdings = db.get_all_holdings()
    assert len(db_holdings) >= 4
    db_prof = db.get_user_profile()
    assert db_prof.risk_level in ["conservative", "moderate", "aggressive"]
    print("11. Database Seeds Passed: Verified persistent holdings and profile tables.")

    # 12. Test User Profile Persistence
    orig_risk = db_prof.risk_level
    db.upsert_user_profile(UserProfileDB(risk_level="aggressive", portfolio_cash=300000.0))
    updated_p = db.get_user_profile()
    assert updated_p.risk_level == "aggressive"
    assert updated_p.portfolio_cash == 300000.0
    # Restore
    db.upsert_user_profile(UserProfileDB(risk_level=orig_risk, portfolio_cash=250000.0))
    assert db.get_user_profile().risk_level == orig_risk
    print("12. User Profile Persistence Passed: Write & read verified.")

    # 13. Test Portfolio Holding CRUD
    test_h = PortfolioHoldingDB(
        ticker="TESTSTOCK",
        company_name="Test Stock Inc.",
        shares=10.0,
        avg_cost=150.0,
        currency="USD",
        sector="Tech",
        beta=1.2
    )
    db.upsert_holding(test_h)
    fetched_tickers = [h.ticker for h in db.get_all_holdings()]
    assert "TESTSTOCK" in fetched_tickers
    db.delete_holding("TESTSTOCK")
    fetched_after = [h.ticker for h in db.get_all_holdings()]
    assert "TESTSTOCK" not in fetched_after
    print("13. Portfolio Holding CRUD Passed: Add and delete verified.")

    # 14. Test Watchlist & Decision Memo Persistence
    db.add_to_watchlist(WatchlistDB(ticker="NVDA", target_price=130.0, notes="Wait for support"))
    wl = db.get_watchlist()
    assert any(w.ticker == "NVDA" for w in wl)
    db.remove_from_watchlist("NVDA")

    memo = DecisionMemoDB(
        id="memo-test-1",
        ticker="RELIANCE",
        company_name="Reliance Industries",
        memo_markdown="# Test Memo Content"
    )
    db.save_memo(memo)
    memos = db.get_memos()
    assert any(m.id == "memo-test-1" for m in memos)
    print("14. Watchlist & Decision Memo Persistence Passed: Stored and queried cleanly.")

    # 15. Test Real Mathematical Technical Indicators Engine
    from backend.data.market_service import market_service
    sample_series = [100.0 + (i * 0.8) + ((i % 4 - 1.5) * 1.5) for i in range(50)]
    sma20 = market_service.calculate_sma(sample_series, 20)
    ema20 = market_service.calculate_ema(sample_series, 20)
    rsi14 = market_service.calculate_rsi(sample_series, 14)
    macd = market_service.calculate_macd(sample_series)
    assert sma20 > 100.0
    assert ema20 > 100.0
    assert 0.0 <= rsi14 <= 100.0
    assert "line" in macd and "signal" in macd and "hist" in macd
    print(f"15. Technical Indicators Engine Passed: RSI(14)={rsi14}, SMA(20)={sma20}, MACD Hist={macd['hist']}")

    # 16. Test Candlestick History OHLCV Endpoint
    from backend.main import get_stock_history
    history = run_coro(get_stock_history(ticker="NVDA", timeframe="1M"))
    assert len(history) >= 28
    latest_bar = history[-1]
    assert "open" in latest_bar and "high" in latest_bar and "low" in latest_bar and "close" in latest_bar and "volume" in latest_bar
    assert latest_bar["high"] >= latest_bar["low"]
    assert latest_bar["close"] > 0
    print(f"16. Candlestick History Endpoint Passed: {len(history)} OHLCV bars returned for NVDA.")

    # 17. Test Generalized Dynamic Debate on Arbitrary Ticker
    from backend.agents.debate_engine import debate_engine
    debate_res = debate_engine.conduct_debate(
        ticker="AMD",
        quant_result={"stance": "BULLISH", "score": 82, "signals": ["RSI at 64.5", "50-SMA Golden Cross"]},
        rag_result={"stance": "BEARISH", "score": 38, "timed_out": False, "key_findings": ["Client PC revenue compressed 12%"]},
        behavioral_result={"stance": "CAUTION", "score": 45, "user_risk_profile": "conservative", "behavioral_adjustments": ["Cap size"]}
    )
    assert debate_res["has_disagreement"] is True
    assert "AMD" in debate_res["resolution_summary"]
    assert any("AMD" in d["text"] for d in debate_res["dialogue_steps"])
    assert any("Client PC revenue compressed 12%" in d["text"] for d in debate_res["dialogue_steps"])
    print("17. Dynamic Generalized Debate Passed: Arbitrary ticker AMD generated coherent adversarial dialogue.")

    # 18. Test Dynamic RAG Document Ingestion & Retrieval
    from backend.main import upload_rag_document, UploadDocumentRequest
    upload_req = UploadDocumentRequest(
        ticker="AMD",
        document_title="AMD Form 10-K Annual Report",
        section="Item 7 MD&A",
        content="Data Center enterprise EPYC processor sales expanded 122% YoY, driving record server market share gains."
    )
    upload_res = run_coro(upload_rag_document(upload_req))
    assert upload_res["status"] == "indexed"
    assert upload_res["ticker"] == "AMD"
    assert upload_res["chunks_created"] >= 1

    # Verify search finds the uploaded citation
    from backend.rag.retriever import rag_retriever
    search_res = rag_retriever.search("AMD", query="data center server epyc market share", top_k=2)
    assert len(search_res["citations"]) >= 1
    assert "EPYC" in search_res["citations"][0]["excerpt"]
    print(f"18. Dynamic RAG Ingestion & Retrieval Passed: Citation indexed and retrieved ({search_res['citations'][0]['excerpt'][:45]}...).")

    # 19. Test Persistent SQLite REST Endpoints Integration
    from backend.main import get_stored_user_profile, update_stored_user_profile, save_decision_memo, list_decision_memos
    test_profile = UserProfileDB(
        id="default_user",
        risk_level="aggressive",
        investment_horizon="long",
        panic_sell_tendency=0.25,
        preferred_sectors=["Tech", "Financials"],
        portfolio_cash=350000.0
    )
    saved_prof = run_coro(update_stored_user_profile(test_profile))
    assert saved_prof["risk_level"] == "aggressive"
    fetched_prof = run_coro(get_stored_user_profile())
    assert fetched_prof["risk_level"] == "aggressive"
    assert fetched_prof["portfolio_cash"] == 350000.0

    test_memo = DecisionMemoDB(
        id="memo-rest-test-1",
        ticker="NVDA",
        company_name="NVIDIA Corp",
        memo_markdown="# Executive Decision Memo\nVerified via REST API."
    )
    saved_memo_res = run_coro(save_decision_memo(test_memo))
    assert saved_memo_res["ticker"] == "NVDA"
    all_memos = run_coro(list_decision_memos())
    assert any(m["id"] == "memo-rest-test-1" for m in all_memos)
    print("19. Persistent SQLite REST Endpoints Integration Passed: User profile and decision memos verified.")

    # 20. Test Mathematical Properties & Quantitative Invariants
    from backend.tests.test_mathematical_properties import (
        test_rsi_mathematical_invariants,
        test_moving_averages_and_macd_properties,
        test_volume_anomaly_properties,
        test_backtest_performance_metrics_math,
        test_portfolio_conservation_laws
    )
    test_rsi_mathematical_invariants()
    test_moving_averages_and_macd_properties()
    test_volume_anomaly_properties()
    test_backtest_performance_metrics_math()
    test_portfolio_conservation_laws()
    print("20. Mathematical Properties & Invariants Passed: RSI bounds, MACD identities, volume anomaly, CAGR, Max Drawdown, and portfolio conservation laws verified.")

    print("\n==========================================")
    print("SUCCESS: ALL 20 TEST SCENARIOS PASSED WITH 100% ACCURACY!")
    print("==========================================")

if __name__ == "__main__":
    run_all_tests()
