import sys
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["rag_corpus_documents"] >= 6
    print("✓ test_health passed")

def test_stocks():
    res = client.get("/api/stocks")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    tickers = [s["ticker"] for s in data]
    for t in ["RELIANCE", "TCS", "INFY", "NVDA", "AAPL", "TSLA"]:
        assert t in tickers
    print("✓ test_stocks passed")

def test_analyze_standard():
    payload = {
        "ticker": "RELIANCE",
        "user_profile": {
            "risk_level": "conservative",
            "investment_horizon": "medium",
            "panic_sell_tendency": 0.8,
            "preferred_sectors": ["Energy", "Tech"],
            "portfolio_cash": 250000
        },
        "explain_mode": "beginner",
        "simulated_stale_data": False,
        "simulated_rag_timeout": False
    }
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    
    # Check Price Data
    assert data["ticker"] == "RELIANCE"
    assert "Reliance Industries" in data["company_name"]
    assert data["price_data"]["feed_status"] == "LIVE"
    assert data["price_data"]["confidence_penalty"] == 0.0
    
    # Check Agents
    assert data["agents"]["quant"]["stance"] == "BULLISH"
    assert data["agents"]["rag"]["stance"] == "BEARISH"
    assert data["agents"]["rag"]["timed_out"] is False
    assert len(data["agents"]["rag"]["citations"]) > 0
    assert data["agents"]["behavioral_risk"]["stance"] == "CAUTION"

    # Check Debate Disagreement
    assert data["debate"]["has_disagreement"] is True
    assert len(data["debate"]["dialogue_steps"]) == 3
    assert data["debate"]["confidence_calibration_score"] == 63

    # Check Synthesis
    assert data["synthesis"]["final_action"] == "CAUTIOUS_ACCUMULATE"
    assert "expert" in data["synthesis"]["explain_modes"]
    assert "beginner" in data["synthesis"]["explain_modes"]

    # Check Sentiment Shift
    assert data["sentiment_shift"]["ticker"] == "RELIANCE"
    assert len(data["sentiment_shift"]["keyword_frequencies"]) >= 4

    # Check Telemetry
    assert data["telemetry"]["degraded_data"] is False
    print("✓ test_analyze_standard passed")

def test_analyze_stale_data():
    payload = {
        "ticker": "RELIANCE",
        "user_profile": {"risk_level": "conservative"},
        "simulated_stale_data": True,
        "simulated_rag_timeout": False
    }
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["price_data"]["feed_status"] == "STALE_FALLBACK_EOD"
    assert data["price_data"]["confidence_penalty"] > 0
    assert data["telemetry"]["degraded_data"] is True
    assert "stale" in data["telemetry"]["degraded_reason"].lower()
    assert data["telemetry"]["confidence_score"] <= 60
    print("✓ test_analyze_stale_data passed")

def test_analyze_rag_timeout():
    payload = {
        "ticker": "RELIANCE",
        "user_profile": {"risk_level": "conservative"},
        "simulated_stale_data": False,
        "simulated_rag_timeout": True
    }
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["agents"]["rag"]["timed_out"] is True
    assert data["synthesis"]["weight_breakdown"]["fundamentals"] == 0
    assert "pending" in data["synthesis"]["headline"].lower() or "technicals only" in data["synthesis"]["headline"].lower()
    assert data["telemetry"]["degraded_data"] is True
    print("✓ test_analyze_rag_timeout passed")

def test_simulate_trade():
    payload = {
        "ticker": "TSLA",
        "action": "BUY",
        "quantity": 10,
        "price": 240.0,
        "user_profile": { "risk_level": "conservative" }
    }
    res = client.post("/api/simulate-trade", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["warning_triggered"] is True
    assert "Conservative" in data["nudge_message"]
    assert "portfolio_delta" in data
    assert data["portfolio_delta"]["projected_tech_pct"] > data["portfolio_delta"]["current_tech_pct"]
    assert data["portfolio_delta"]["projected_beta"] > data["portfolio_delta"]["current_beta"]
    print("✓ test_simulate_trade passed")

def test_portfolio():
    res = client.get("/api/portfolio")
    assert res.status_code == 200
    data = res.json()
    assert "total_value" in data
    assert "holdings" in data
    assert "sector_allocations" in data
    assert "concentration_heatmap" in data
    assert len(data["holdings"]) >= 4
    print("✓ test_portfolio passed")

def test_backtest():
    payload = {
        "ticker": "NVDA",
        "historical_date": "2025-10-15",
        "holding_days": 90
    }
    res = client.post("/api/backtest", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["historical_date"] == "2025-10-15"
    assert data["entry_price"] == 132.50
    assert data["exit_price"] == 178.20
    assert data["actual_return_pct"] == 34.49
    assert data["agent_recommendation_then"] == "STRONG_BUY"
    assert data["was_profitable"] is True
    print("✓ test_backtest passed")

if __name__ == "__main__":
    test_health()
    test_stocks()
    test_analyze_standard()
    test_analyze_stale_data()
    test_analyze_rag_timeout()
    test_simulate_trade()
    test_portfolio()
    test_backtest()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
