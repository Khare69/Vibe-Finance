import os
import sys
import math
from typing import List
import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.data.market_service import market_service
from backend.agents.quant_agent import quant_agent
from backend.agents.rag_agent import rag_agent
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
    score_60 = market_service.calculate_rsi_factor_score(60.0)
    score_75 = market_service.calculate_rsi_factor_score(75.0)
    score_85 = market_service.calculate_rsi_factor_score(85.0)

    # Optimal momentum (55-65) must score higher than neutral (50)
    assert score_60 > score_50, f"Optimal RSI 60 ({score_60}) should score higher than neutral 50 ({score_50})"
    
    # Overbought extreme (85) must be heavily penalized compared to optimal momentum (60)
    assert score_85 < score_60, f"Overbought RSI 85 ({score_85}) should be penalized below optimal RSI 60 ({score_60})"
    
    # Overbought extreme (85) must be negative to reflect extreme mean-reversion risk
    assert score_85 < 0, f"Overbought RSI 85 ({score_85}) should yield negative factor score"

    # Mild overbought threshold (75) should start tapering downwards
    assert score_75 < score_60, f"RSI 75 ({score_75}) should taper below peak RSI 60 ({score_60})"

    print(f"  [PASSED] Non-linear factor curve validated: RSI 30={score_30}, RSI 50={score_50}, RSI 60={score_60} (PEAK), RSI 75={score_75}, RSI 85={score_85} (PENALTY)")


def test_moving_averages_and_macd_properties():
    print("\n--- 3. Testing Moving Averages & MACD Algebraic Invariants ---")
    
    # Invariant A: SMA of constant c is c
    constant_series = [42.0] * 50
    sma = market_service.calculate_sma(constant_series, 50)
    assert abs(sma - 42.0) < 1e-6, f"SMA of constant series should be 42.0, got {sma}"
    print("  [PASSED] Invariant A: SMA of constant series == c")

    # Invariant B: EMA recency weighting (recent spike pulls EMA faster than SMA)
    stepped_series = [10.0] * 40 + [20.0] * 10
    ema = market_service.calculate_ema(stepped_series, 20)
    sma_comp = market_service.calculate_sma(stepped_series, 20)
    assert ema > sma_comp, f"EMA ({ema}) must respond faster to recent upward step than SMA ({sma_comp})"
    print(f"  [PASSED] Invariant B: EMA recency weighting verified (EMA={ema:.2f} > SMA={sma_comp:.2f})")

    # Invariant C: MACD Algebraic Identity: hist == line - signal
    macd = market_service.calculate_macd([100.0 + i for i in range(60)], 12, 26, 9)
    algebraic_diff = macd["line"] - macd["signal"]
    assert abs(macd["hist"] - algebraic_diff) < 1e-4, f"MACD histogram identity violated: {macd['hist']} != {algebraic_diff}"
    print(f"  [PASSED] Invariant C: MACD Identity verified: hist ({macd['hist']}) == line ({macd['line']}) - signal ({macd['signal']})")


def test_volume_anomaly_properties():
    print("\n--- 4. Testing Volume Anomaly Baseline Independence ---")
    
    # When current volume spikes by 3x over past 20-day mean
    past_20_days = [1_000_000] * 20
    current_day = [3_000_000]
    full_history = past_20_days + current_day
    
    vol_ratio = market_service.calculate_volume_anomaly(full_history, baseline_window=20)
    # The anomaly must equal 3.0x because the 20-day baseline excludes the current day spike
    assert abs(vol_ratio - 3.0) < 0.05, f"Expected 3.0x volume anomaly, got {vol_ratio}"
    print(f"  [PASSED] Volume Anomaly ratio against prior baseline: {vol_ratio}x (exact 3.0x)")


def test_weekly_drawdown_risk_scaling():
    print("\n--- 5. Testing Square-Root-of-Time Weekly Drawdown Risk Scaling ---")

    # Test conservative user on low-volatility TCS (18% annual vol)
    tcs_market_data = {
        "annualized_volatility": 0.18,
        "current_price": 3900.0,
        "metrics": {"rsi_14": 52.0}
    }
    tcs_profile = {"risk_level": "conservative", "panic_tendency": 0.3}
    tcs_res = behavioral_agent.analyze("TCS", tcs_profile, tcs_market_data)

    # 18% / sqrt(52) * 1.65 = 4.1% 1-week 95% VaR
    expected_tcs_var = round(1.65 * (18.0 / math.sqrt(52.0)), 1)
    assert tcs_res["weekly_95_var"] == expected_tcs_var, f"Expected weekly VaR {expected_tcs_var}, got {tcs_res['weekly_95_var']}"
    # Conservative cap is 8.0%. TCS at 4.1% should NOT trigger the "exceeds conservative cap" adjustment
    assert not any("exceeds conservative cap" in adj for adj in tcs_res["behavioral_adjustments"]), (
        f"Low-volatility asset TCS ({tcs_res['weekly_95_var']}%) should not trigger conservative risk cap warning!"
    )
    print(f"  [PASSED] Low-volatility asset (TCS 18% vol): 1-week VaR = {tcs_res['weekly_95_var']}%, conservative cap compliant.")

    # Test high-volatility TSLA (52% annual vol)
    tsla_market_data = {
        "annualized_volatility": 0.52,
        "current_price": 250.0,
        "metrics": {"rsi_14": 65.0}
    }
    tsla_res = behavioral_agent.analyze("TSLA", tcs_profile, tsla_market_data)
    # 52% / sqrt(52) * 1.65 = 11.9%
    expected_tsla_var = round(1.65 * (52.0 / math.sqrt(52.0)), 1)
    assert tsla_res["weekly_95_var"] == expected_tsla_var
    assert any("exceeds conservative cap" in adj for adj in tsla_res["behavioral_adjustments"]), (
        f"High-volatility asset TSLA ({tsla_res['weekly_95_var']}%) must trigger conservative risk cap warning!"
    )
    print(f"  [PASSED] High-volatility asset (TSLA 52% vol): 1-week VaR = {tsla_res['weekly_95_var']}%, conservative cap breached as expected.")


def test_beta_and_volatility_calculation():
    print("\n--- 6. Testing Dynamic Beta and Volatility Calculations ---")

    # Invariant A: Asset perfectly correlated with benchmark with identical variance has Beta == 1.0
    np.random.seed(42)
    bench_returns = np.random.normal(0.001, 0.015, 60)
    bench = [100.0]
    for r in bench_returns:
        bench.append(bench[-1] * (1.0 + r))

    asset_identical = list(bench)
    beta_identical = market_service.calculate_beta(asset_identical, bench)
    assert abs(beta_identical - 1.0) < 0.05, f"Beta of identical series should be 1.0, got {beta_identical}"
    print(f"  [PASSED] Invariant A: Identical series Beta == 1.0 (got {beta_identical})")

    # Invariant B: Asset with 2x returns of benchmark has Beta == 2.0
    asset_levered = [100.0]
    for r in bench_returns:
        asset_levered.append(asset_levered[-1] * (1.0 + 2.0 * r))
    beta_levered = market_service.calculate_beta(asset_levered, bench)
    assert abs(beta_levered - 2.0) < 0.15, f"Beta of 2x series should be ~2.0, got {beta_levered}"
    print(f"  [PASSED] Invariant B: 2x leveraged series Beta == 2.0 (got {beta_levered})")

    # Invariant C: Catalog contains realistic seeded baselines
    for sym in ["RELIANCE", "TCS", "INFY", "HDFCBANK", "AAPL", "NVDA", "TSLA"]:
        info = market_service.STOCK_CATALOG.get(sym)
        assert info is not None, f"Stock info missing for {sym}"
        assert "baseline_beta" in info, f"baseline_beta missing for {sym}"
        assert "baseline_volatility" in info, f"baseline_volatility missing for {sym}"
        assert info["baseline_beta"] > 0
        assert info["baseline_volatility"] > 0
    print("  [PASSED] Invariant C: All 7 tracked assets have positive baseline beta and volatility.")


def test_dynamic_macro_regimes():
    print("\n--- 7. Testing Dynamic Macro Regime Synthesis ---")

    dummy_quant = {"score": 75, "stance": "BULLISH", "metrics": {"rsi_14": 62.0}}
    dummy_rag = {"score": 70, "stance": "BULLISH", "timed_out": False}
    dummy_risk = {"score": 60, "user_risk_profile": "moderate"}
    dummy_debate = {"has_disagreement": False}
    dummy_market = {
        "current_price": 135.0,
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


def test_parametric_shortfall_and_beta_adjusted_stress():
    print("\n--- 10. Testing Continuous Parametric Shortfall Risk & Beta-Adjusted Stress ---")

    # Invariant A: Continuous parametric shortfall probability
    stress_res = portfolio_service.simulate_stress_test("rate_hike_2022")
    cash_buf = stress_res["cash_buffer"]
    ruin_prob = cash_buf["projected_ruin_probability_pct"]
    assert cash_buf["calculation_method"] == "parametric_gaussian_shortfall"
    assert "provenance" in cash_buf
    assert 0.0 < ruin_prob < 100.0
    print(f"  [PASSED] Invariant 10A: Continuous Parametric Shortfall Risk = {ruin_prob}%, Z = {cash_buf['provenance']['z_score']}")

    # Invariant B: Asset beta-adjusted sector shock sensitivity
    impacts = {a["ticker"]: a for a in stress_res["asset_impacts"]}
    # In Rate Hike 2022, Tech sector has base shock -24.5%
    # TCS has beta 0.72, AAPL has beta 1.05
    if "TCS" in impacts and "AAPL" in impacts:
        tcs_shock = impacts["TCS"]["shock_pct"]
        aapl_shock = impacts["AAPL"]["shock_pct"]
        assert abs(tcs_shock) < abs(aapl_shock), f"Lower beta TCS ({tcs_shock}%) should have smaller drawdown than AAPL ({aapl_shock}%)"
        print(f"  [PASSED] Invariant 10B: Beta scaling verified: TCS (beta 0.72) shock = {tcs_shock}% vs AAPL (beta 1.05) shock = {aapl_shock}%")


def test_backtest_fallback_honesty_and_provenance():
    print("\n--- 11. Testing Backtest Fallback Honesty & Provenance Badges ---")

    # Test fallback simulation returns honest zero-alpha metrics without fabrication
    fallback_res = backtest_simulator._fallback_simulation("NVDA", "2025-10-15", 90)
    assert fallback_res["is_fallback"] is True
    assert fallback_res["status"] == "FALLBACK_INSUFFICIENT_HISTORY"
    assert fallback_res["actual_return_pct"] == 0.0
    assert fallback_res["agent_recommendation_then"] == "INSUFFICIENT_DATA"
    assert fallback_res["performance_metrics"]["sharpe_ratio"] == 0.0
    assert fallback_res["performance_metrics"]["sortino_ratio"] == 0.0
    assert fallback_res["performance_metrics"]["win_rate_trajectory_pct"] == 0.0
    assert "disclaimer" in fallback_res["provenance"]
    print("  [PASSED] Invariant 11A: Backtest fallback returns honest zero-alpha baseline with explicit disclaimer.")

    # Invariant B: Agent and service provenance badges present
    dummy_market = {"current_price": 100.0, "metrics": {"rsi_14": 50.0}, "feed_status": "LIVE_YAHOO"}
    q_res = quant_agent.analyze("AAPL", dummy_market)
    assert "provenance" in q_res
    b_res = behavioral_agent.analyze("AAPL", {"risk_level": "moderate"}, dummy_market)
    assert "provenance" in b_res
    r_res = rag_agent.analyze("AAPL")
    assert "provenance" in r_res
    port_res = portfolio_service.get_portfolio()
    assert "provenance" in port_res
    print("  [PASSED] Invariant 11B: Provenance badges verified across Quant, Behavioral, RAG, and Portfolio services.")


def main():
    print("=== Testing Sub-phases A.1 & A.2: Mathematical Properties, Risk Scaling, Shortfall Risk & Provenance ===")
    test_rsi_mathematical_invariants()
    test_rsi_factor_scoring_non_linearity()
    test_moving_averages_and_macd_properties()
    test_volume_anomaly_properties()
    test_weekly_drawdown_risk_scaling()
    test_beta_and_volatility_calculation()
    test_dynamic_macro_regimes()
    test_portfolio_conservation_laws()
    test_attribution_weights_invariance()
    test_parametric_shortfall_and_beta_adjusted_stress()
    test_backtest_fallback_honesty_and_provenance()
    print("\n[SUCCESS] Sub-phases A.1 & A.2 Mathematical Properties & Invariants verified with 100% accuracy!")


if __name__ == "__main__":
    main()
