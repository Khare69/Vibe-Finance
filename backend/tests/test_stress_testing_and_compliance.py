import os
import sys
from fastapi.testclient import TestClient

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.main import app
from backend.personalization.portfolio import portfolio_service


def test_stress_scenarios_listing():
    print("\n--- 1. Testing Stress Scenarios Listing ---")
    scenarios = portfolio_service.get_stress_scenarios()
    assert len(scenarios) >= 4, f"Expected at least 4 stress scenarios, got {len(scenarios)}"
    scenario_ids = [s["id"] for s in scenarios]
    assert "rate_hike_2022" in scenario_ids
    assert "covid_liquidity_2020" in scenario_ids
    assert "crude_supply_shock" in scenario_ids
    assert "tech_multiple_pullback_2024" in scenario_ids

    for sc in scenarios:
        assert "name" in sc
        assert "description" in sc
        assert "sector_shocks" in sc
        assert "agent_guidance" in sc
        assert "recovery_horizon_months" in sc
        assert "Tech" in sc["sector_shocks"]
        assert "Energy" in sc["sector_shocks"]
    print(f"[PASSED] Stress scenarios verified: {scenario_ids}")


def test_simulate_stress_test_direct():
    print("\n--- 2. Testing Direct Stress Test Execution ---")
    # Test 2022 Rate Hike Shock
    res = portfolio_service.simulate_stress_test("rate_hike_2022")
    assert res["scenario"]["id"] == "rate_hike_2022"
    assert res["baseline_total_value"] > 0
    assert res["shocked_total_value"] > 0
    assert res["portfolio_pnl_delta"] != 0
    assert -50.0 <= res["portfolio_drawdown_pct"] <= 50.0
    assert res["shocked_portfolio_beta"] > 0
    assert len(res["asset_impacts"]) >= 3

    # Check cash buffer and ruin probability
    cash_buf = res["cash_buffer"]
    assert cash_buf["cash_amount"] >= 0
    assert cash_buf["cash_pct_after_shock"] >= 0
    assert cash_buf["adequacy_rating"] in ["STRONG_LIQUIDITY_BUFFER", "ADEQUATE_BUFFER", "VULNERABLE_DEFICIT"]
    assert 0.0 <= cash_buf["projected_ruin_probability_pct"] <= 100.0

    # Check statutory compliance guardrail
    guard = res["regulatory_compliance_guardrail"]
    assert "SEBI (Investment Advisers) Regulations, 2013" in guard["framework"]
    assert "disclaimer_text" in guard
    assert "SEBI-registered" in guard["disclaimer_text"]
    print(f"[PASSED] 2022 Rate Hike Shock simulated: Drawdown = {res['portfolio_drawdown_pct']}%, Ruin Prob = {cash_buf['projected_ruin_probability_pct']}%.")

    # Test Covid 2020 Liquidity Crunch
    res_covid = portfolio_service.simulate_stress_test("covid_liquidity_2020")
    assert res_covid["portfolio_drawdown_pct"] < 0
    print(f"[PASSED] 2020 Liquidity Crunch simulated: Drawdown = {res_covid['portfolio_drawdown_pct']}%.")


def test_api_stress_endpoints():
    print("\n--- 3. Testing REST API Stress Testing Endpoints ---")
    with TestClient(app) as client:
        # GET scenarios
        res_get = client.get("/api/portfolio/stress-scenarios")
        assert res_get.status_code == 200
        scenarios_data = res_get.json()
        assert len(scenarios_data) >= 4
        print(f"[PASSED] GET /api/portfolio/stress-scenarios returned {len(scenarios_data)} scenarios.")

        # POST run stress test
        res_post = client.post(
            "/api/portfolio/stress-test",
            json={"scenario_id": "tech_multiple_pullback_2024"}
        )
        assert res_post.status_code == 200
        data = res_post.json()
        assert data["scenario"]["id"] == "tech_multiple_pullback_2024"
        assert len(data["asset_impacts"]) >= 3
        assert "regulatory_compliance_guardrail" in data
        print("[PASSED] POST /api/portfolio/stress-test verified.")

        # POST simulate trade has SEBI guardrail
        res_trade = client.post(
            "/api/simulate-trade",
            json={"ticker": "RELIANCE", "action": "BUY", "quantity": 10, "price": 2850.0}
        )
        assert res_trade.status_code == 200
        trade_data = res_trade.json()
        assert "regulatory_compliance_guardrail" in trade_data
        print("[PASSED] POST /api/simulate-trade SEBI compliance guardrail verified.")


def main():
    print("=== Testing Sub-phase 5.3: Portfolio Stress-Testing & SEBI Compliance Guardrails ===")
    test_stress_scenarios_listing()
    test_simulate_stress_test_direct()
    test_api_stress_endpoints()
    print("\n[SUCCESS] Sub-phase 5.3 Portfolio Stress-Testing & SEBI Compliance Guardrails verified with 100% accuracy!")


if __name__ == "__main__":
    main()
