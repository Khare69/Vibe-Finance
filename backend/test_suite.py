import sys
import os
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
    """Executes a coroutine cleanly without requiring an external IOCP Proactor network loop."""
    try:
        return coro.send(None)
    except StopIteration as e:
        return e.value
    except AttributeError:
        return coro

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
    assert res["price_data"]["feed_status"] == "LIVE"
    assert res["agents"]["quant"]["stance"] == "BULLISH"
    assert res["agents"]["rag"]["stance"] == "BEARISH"
    assert res["agents"]["behavioral_risk"]["stance"] == "CAUTION"
    assert res["debate"]["has_disagreement"] is True
    assert res["synthesis"]["final_action"] == "CAUTIOUS_ACCUMULATE"
    assert len(res["debate"]["dialogue_steps"]) == 3
    assert len(res["agents"]["rag"]["citations"]) >= 2
    assert res["telemetry"]["confidence_score"] == 63
    print("3. Analyze (Standard RELIANCE) Passed: Disagreement detected, Action:", res["synthesis"]["final_action"])

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
    assert bt_res["historical_date"] == "2025-10-15"
    assert bt_res["entry_price"] == 132.50
    assert bt_res["exit_price"] == 178.20
    assert bt_res["actual_return_pct"] == 34.49
    assert bt_res["agent_recommendation_then"] == "STRONG_BUY"
    assert bt_res["was_profitable"] is True
    print("8. Backtest Endpoint Passed: Replayed recommendation and return matching benchmark.")

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

    print("\n==========================================")
    print("SUCCESS: ALL 14 TEST SCENARIOS PASSED WITH 100% ACCURACY!")
    print("==========================================")

if __name__ == "__main__":
    run_all_tests()
