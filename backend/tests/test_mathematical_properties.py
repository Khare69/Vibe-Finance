import os
import sys
import math
from typing import List
import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.data.market_service import market_service
from backend.agents.behavioral_agent import behavioral_agent
from backend.agents.synthesis_agent import synthesis_agent
from backend.backtest.simulator import backtest_simulator
from backend.personalization.portfolio import portfolio_service


def test_rsi_mathematical_invariants():
    print("\n--- 1. Testing RSI Mathematical Boundary & Monotonicity Invariants ---")
    
    # Invariant A: Pure upward price series must yield RSI == 100.0
    strictly_increasing = [100.0 + (i * 2.5) for i in range(30)]
    rsi_up = market_service.calculate_rsi(strictly_increasing, 14)
    assert rsi_up == 100.0, f"Expected RSI 100.0 on pure upseries, got {rsi_up}"
    print("  [PASSED] Invariant A: Pure upward price walk -> RSI = 100.0")

    # Invariant B: Pure downward price series must yield RSI == 0.0
    strictly_decreasing = [200.0 - (i * 2.0) for i in range(30)]
    rsi_down = market_service.calculate_rsi(strictly_decreasing, 14)
    assert rsi_down == 0.0, f"Expected RSI 0.0 on pure downseries, got {rsi_down}"
    print("  [PASSED] Invariant B: Pure downward price walk -> RSI = 0.0")

    # Invariant C: Flat series (zero delta) must stay bounded at 50.0
    flat_series = [150.0] * 30
    rsi_flat = market_service.calculate_rsi(flat_series, 14)
    assert rsi_flat == 50.0, f"Expected RSI 50.0 on zero-variance series, got {rsi_flat}"
    print("  [PASSED] Invariant C: Flat series -> RSI = 50.0")

    # Invariant D: General random walk must stay strictly bounded within [0, 100]
    oscillating_series = [100.0 + 15.0 * math.sin(i * 0.3) for i in range(100)]
    rsi_osc = market_service.calculate_rsi(oscillating_series, 14)
    assert 0.0 <= rsi_osc <= 100.0, f"RSI out of bounds: {rsi_osc}"
    print(f"  [PASSED] Invariant D: General series strictly bounded [0, 100] (RSI = {rsi_osc})")


def test_rsi_factor_scoring_non_linearity():
    print("\n--- 2. Testing Non-Linear RSI Factor Scoring (Overbought Mean-Reversion Guard) ---")
    
    score_30 = market_service.calculate_rsi_factor_score(30.0)
    score_50 = market_service.calculate_rsi_factor_score(50.0)
    score_65 = market_service.calculate_rsi_factor_score(65.0)
    score_85 = market_service.calculate_rsi_factor_score(85.0)

    # Invariant 2A: Optimal momentum is at 60-65
    assert score_65 > score_50, f"RSI 65 ({score_65}) must exceed RSI 50 ({score_50})"
    print(f"  [PASSED] Invariant 2A: Healthy momentum at RSI 65 (+{score_65} pts) > neutral RSI 50 ({score_50} pts)")

    # Invariant 2B: Severe overbought (RSI 85) is penalized for mean-reversion risk, NOT rewarded
    assert score_85 < 0, f"RSI 85 must be penalized with a negative score, got {score_85}"
    assert score_85 < score_65, f"RSI 85 ({score_85}) must be lower than RSI 65 ({score_65})"
    print(f"  [PASSED] Invariant 2B: Overbought froth at RSI 85 penalized ({score_85} pts) < peak momentum RSI 65 (+{score_65} pts)")


def test_moving_averages_and_macd_properties():
    print("\n--- 3. Testing Moving Averages & MACD Algebraic Identities ---")

    test_prices = [10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0]
    expected_sma5 = sum(test_prices[-5:]) / 5.0
    calc_sma5 = market_service.calculate_sma(test_prices, 5)
    assert abs(calc_sma5 - expected_sma5) < 1e-4, f"SMA mismatch: expected {expected_sma5}, got {calc_sma5}"
    print(f"  [PASSED] SMA Identity: calculated {calc_sma5} == expected {expected_sma5}")

    flat_prices = [42.0] * 15
    assert market_service.calculate_ema(flat_prices, 5) == 42.0
    print("  [PASSED] EMA Identity: Constant series -> EMA = constant price (42.0)")

    surge_prices = [10.0] * 10 + [50.0]
    calc_ema = market_service.calculate_ema(surge_prices, 5)
    assert calc_ema > 10.0
    print(f"  [PASSED] EMA Surge Response: EMA-5 responded from baseline 10.0 to {calc_ema}")

    longer_series = [50.0 + (i * 0.5) + math.sin(i) * 2.0 for i in range(60)]
    macd_res = market_service.calculate_macd(longer_series)
    diff = round(macd_res["line"] - macd_res["signal"], 2)
    assert abs(macd_res["hist"] - diff) < 0.05, f"MACD Identity violated: hist={macd_res['hist']} vs line-signal={diff}"
    print(f"  [PASSED] MACD Algebraic Identity: {macd_res['line']} - {macd_res['signal']} == {macd_res['hist']}")


def test_volume_anomaly_properties():
    print("\n--- 4. Testing Volume Anomaly Mathematical Properties ---")
    
    # Baseline of 20 days with 100,000, current volume is 250,000 -> ratio must equal 2.50
    vol_history = [100000] * 20
    current_vol = 250000
    ratio = market_service.calculate_volume_anomaly(current_vol, vol_history)
    assert ratio == 2.5, f"Expected volume anomaly ratio 2.50, got {ratio}"
    print(f"  [PASSED] Volume Anomaly ratio: {current_vol} / 100,000 == {ratio}x")

    # Ratio on zero or empty history must gracefully fallback to 1.0
    assert market_service.calculate_volume_anomaly(current_vol, []) == 1.0
    print("  [PASSED] Empty history edge-case handled gracefully (1.0x).")


def test_weekly_drawdown_risk_scaling():
    print("\n--- 5. Testing Square-Root-of-Time Weekly Drawdown Risk Scaling ---")

    # TCS (defensive stock, annual vol 18%):
    # weekly_vol = 0.18 / sqrt(52) = ~0.02496
    # 95% 1-week VaR = 1.65 * 0.02496 = ~0.0412 (4.12%)
    # Under a conservative limit of 8% (0.08), TCS MUST NOT exceed the limit!
    tcs_market = {"current_price": 3915.0, "annualized_volatility": 0.18, "beta": 0.72}
    tcs_profile = {"risk_level": "conservative", "panic_sell_tendency": 0.2}
    tcs_eval = behavioral_agent.analyze("TCS", tcs_profile, tcs_market)

    assert tcs_eval["weekly_95_var"] <= 0.08, f"TCS weekly risk ({tcs_eval['weekly_95_var']}) should not exceed 8%"
    assert any("remains within user's tolerable risk threshold" in adj for adj in tcs_eval["behavioral_adjustments"])
    print(f"  [PASSED] Defensive Stock (TCS): Weekly VaR = {round(tcs_eval['weekly_95_var']*100, 1)}% <= 8.0% conservative cap")

    # TSLA (high-beta stock, annual vol 52%):
    # weekly_vol = 0.52 / sqrt(52) = ~0.0721
    # 95% 1-week VaR = 1.65 * 0.0721 = ~0.119 (11.9%)
    # Under conservative limit of 8%, TSLA MUST exceed the limit and trigger risk warnings!
    tsla_market = {"current_price": 240.0, "annualized_volatility": 0.52, "beta": 2.05}
    tsla_eval = behavioral_agent.analyze("TSLA", tcs_profile, tsla_market)

    assert tsla_eval["weekly_95_var"] > 0.08, f"TSLA weekly risk ({tsla_eval['weekly_95_var']}) should exceed 8%"
    assert any("exceeds user's stated max tolerable weekly drawdown" in adj for adj in tsla_eval["behavioral_adjustments"])
    print(f"  [PASSED] High-Vol Stock (TSLA): Weekly VaR = {round(tsla_eval['weekly_95_var']*100, 1)}% > 8.0% conservative cap (correctly flagged)")


def test_beta_and_volatility_calculation():
    print("\n--- 6. Testing Dynamic Beta & Volatility Propagation ---")

    # Synthetic covariance test: Asset moves 1.5x of benchmark
    bench_returns = [0.01, -0.02, 0.015, -0.005, 0.02, -0.01, 0.008, -0.012, 0.025, -0.018] * 3
    asset_returns = [r * 1.5 + 0.001 for r in bench_returns]

    # Convert returns to closes series
    b_closes = [100.0]
    for r in bench_returns:
        b_closes.append(b_closes[-1] * (1.0 + r))

    a_closes = [100.0]
    for r in asset_returns:
        a_closes.append(a_closes[-1] * (1.0 + r))

    calc_beta = market_service.calculate_beta(a_closes, b_closes)
    assert abs(calc_beta - 1.5) < 0.1, f"Expected calculated beta ~1.5, got {calc_beta}"
    print(f"  [PASSED] Dynamic Beta Calculation: Cov(r, rm)/Var(rm) = {calc_beta} (target: 1.5)")

    # Verify market_service returns beta and annualized_volatility in get_market_data
    nvda_data = market_service.get_market_data("NVDA")
    assert "beta" in nvda_data and nvda_data["beta"] > 1.0, f"Expected NVDA beta > 1.0, got {nvda_data.get('beta')}"
    assert "annualized_volatility" in nvda_data and nvda_data["annualized_volatility"] > 0.30
    print(f"  [PASSED] MarketData Propagation: NVDA Beta = {nvda_data['beta']}, Volatility = {nvda_data['annualized_volatility']}")


def test_dynamic_macro_regimes():
    print("\n--- 7. Testing Dynamic Macro Regime Synthesis & Data Provenance ---")

    dummy_quant = {"score": 75, "stance": "BULLISH"}
    dummy_rag = {"score": 70, "stance": "BULLISH", "timed_out": False}
    dummy_risk = {"score": 60, "user_risk_profile": "moderate"}
    dummy_debate = {"has_disagreement": False}
    dummy_market = {
        "current_price": 217.94,
        "symbol": "$",
        "beta": 1.75,
        "annualized_volatility": 0.44,
        "feed_status": "LIVE_YAHOO"
    }

    res = synthesis_agent._calculate_action_and_weights("NVDA", dummy_quant, dummy_rag, dummy_risk, dummy_debate, dummy_market)
    regime = res["macro_regime"]

    assert "High Beta (1.75x)" in regime["volatility_environment"]
    assert "Expansionary Growth & Momentum Regime" in regime["regime_title"]
    assert regime["provenance"]["method"] == "computed_dynamic_factors"
    assert regime["provenance"]["source"] == "LIVE_YAHOO"
    print(f"  [PASSED] Dynamic Regime: Title = '{regime['regime_title']}', Env = '{regime['volatility_environment']}'")


def test_portfolio_conservation_laws():
    print("\n--- 8. Testing Portfolio Conservation Laws ---")
    
    port = portfolio_service.get_portfolio()
    total_val = port["total_value"]
    invested_val = port["invested_value"]
    cash = port["cash"]
    
    # Law 1: Total Value == Invested Value + Cash
    assert abs(total_val - (invested_val + cash)) < 0.05, f"Portfolio Value Conservation violated: {total_val} != {invested_val} + {cash}"
    print(f"  [PASSED] Conservation Law 1: Total ({total_val}) == Invested ({invested_val}) + Cash ({cash})")

    # Law 2: Sum of sector allocations + cash allocation == 100.0%
    alloc_sum = sum(sec["allocation_pct"] for sec in port["sector_allocations"])
    assert abs(alloc_sum - 100.0) < 0.5, f"Allocation sum does not equal 100%: {alloc_sum}%"
    print(f"  [PASSED] Conservation Law 2: Sum of sector allocations == {alloc_sum}%")

    # Law 3: Stress Shock Value Conservation
    stress_res = portfolio_service.simulate_stress_test("rate_hike_2022")
    orig_sum = sum(a["original_value"] for a in stress_res["asset_impacts"])
    shocked_sum = sum(a["shocked_value"] for a in stress_res["asset_impacts"])
    delta_sum = sum(a["pnl_delta"] for a in stress_res["asset_impacts"])
    assert abs(shocked_sum - (orig_sum + delta_sum)) < 0.1, "Stress Test Value Conservation violated"
    print(f"  [PASSED] Conservation Law 3: Shocked Invested ({round(shocked_sum, 2)}) == Original ({round(orig_sum, 2)}) + Delta ({round(delta_sum, 2)})")


def test_attribution_weights_invariance():
    print("\n--- 9. Testing Synthesis Attribution Weights Conservation Law ---")

    dummy_quant = {"score": 75, "stance": "BULLISH"}
    dummy_rag = {"score": 45, "stance": "BEARISH", "timed_out": False}
    dummy_risk = {"score": 50, "user_risk_profile": "conservative"}
    dummy_debate = {"has_disagreement": True}
    dummy_market = {"current_price": 100.0, "symbol": "$", "beta": 1.0, "annualized_volatility": 0.25}

    # Standard deliberation mode
    res_normal = synthesis_agent._calculate_action_and_weights("TEST", dummy_quant, dummy_rag, dummy_risk, dummy_debate, dummy_market)
    weights_normal = res_normal["weight_breakdown"]
    sum_normal = sum(weights_normal.values())
    assert sum_normal == 100, f"Normal weights sum {sum_normal} != 100"
    print(f"  [PASSED] Invariant 9A: Normal Attribution Decomposition {weights_normal} == 100%")

    # Circuit breaker / RAG timeout mode
    dummy_rag_timeout = {"score": 50, "stance": "NEUTRAL", "timed_out": True}
    res_timeout = synthesis_agent._calculate_action_and_weights("TEST", dummy_quant, dummy_rag_timeout, dummy_risk, dummy_debate, dummy_market)
    weights_timeout = res_timeout["weight_breakdown"]
    sum_timeout = sum(weights_timeout.values())
    assert sum_timeout == 100, f"Timeout weights sum {sum_timeout} != 100"
    print(f"  [PASSED] Invariant 9B: Degraded RAG-Timeout Decomposition {weights_timeout} == 100%")


def main():
    print("=== Testing Sub-phase A.1: Mathematical Properties, Volatility Scaling & Scoring Invariants ===")
    test_rsi_mathematical_invariants()
    test_rsi_factor_scoring_non_linearity()
    test_moving_averages_and_macd_properties()
    test_volume_anomaly_properties()
    test_weekly_drawdown_risk_scaling()
    test_beta_and_volatility_calculation()
    test_dynamic_macro_regimes()
    test_portfolio_conservation_laws()
    test_attribution_weights_invariance()
    print("\n[SUCCESS] Sub-phase A.1 Mathematical Properties & Invariants verified with 100% accuracy!")


if __name__ == "__main__":
    main()
