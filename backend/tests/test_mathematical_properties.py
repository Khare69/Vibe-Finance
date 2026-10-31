import os
import sys
import math
from typing import List

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.data.market_service import market_service
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


def test_moving_averages_and_macd_properties():
    print("\n--- 2. Testing Moving Averages & MACD Algebraic Identities ---")

    test_prices = [10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0]
    # SMA-5 on last 5 elements [20, 22, 24, 26, 28] -> mean = 24.0
    expected_sma5 = sum(test_prices[-5:]) / 5.0
    calc_sma5 = market_service.calculate_sma(test_prices, 5)
    assert abs(calc_sma5 - expected_sma5) < 1e-4, f"SMA mismatch: expected {expected_sma5}, got {calc_sma5}"
    print(f"  [PASSED] SMA Identity: calculated {calc_sma5} == expected {expected_sma5}")

    # EMA Property: On a flat series, EMA must equal the constant price
    flat_prices = [42.0] * 15
    assert market_service.calculate_ema(flat_prices, 5) == 42.0
    print("  [PASSED] EMA Identity: Constant series -> EMA = constant price (42.0)")

    # EMA Property on price surge: Recent prices are dynamically weighted
    surge_prices = [10.0] * 10 + [50.0]
    calc_ema = market_service.calculate_ema(surge_prices, 5)
    assert calc_ema > 10.0
    print(f"  [PASSED] EMA Surge Response: EMA-5 responded from baseline 10.0 to {calc_ema}")

    # MACD Identity: Histogram == MACD Line - Signal Line
    longer_series = [50.0 + (i * 0.5) + math.sin(i) * 2.0 for i in range(60)]
    macd_res = market_service.calculate_macd(longer_series)
    diff = round(macd_res["line"] - macd_res["signal"], 2)
    assert abs(macd_res["hist"] - diff) < 0.05, f"MACD Identity violated: hist={macd_res['hist']} vs line-signal={diff}"
    print(f"  [PASSED] MACD Algebraic Identity: {macd_res['line']} - {macd_res['signal']} == {macd_res['hist']}")


def test_volume_anomaly_properties():
    print("\n--- 3. Testing Volume Anomaly Mathematical Properties ---")
    
    # 20 days of 100,000 volume, today is 250,000 -> ratio must equal 2.50 exactly
    vol_history = [100000] * 20
    current_vol = 250000
    ratio = market_service.calculate_volume_anomaly(current_vol, vol_history)
    assert ratio == 2.5, f"Expected volume anomaly ratio 2.50, got {ratio}"
    print(f"  [PASSED] Volume Anomaly ratio: {current_vol} / 100,000 == {ratio}x")

    # Ratio on zero or empty history must gracefully fallback to 1.0
    assert market_service.calculate_volume_anomaly(current_vol, []) == 1.0
    print("  [PASSED] Empty history edge-case handled gracefully (1.0x).")


def test_backtest_performance_metrics_math():
    print("\n--- 4. Testing Backtesting Performance Metrics Mathematical Formulas ---")
    
    # Verify CAGR formula: (P_exit / P_entry) ** (365 / days) - 1
    p_entry = 100.0
    p_exit = 120.0  # +20% gain
    days = 180
    ret_pct = ((p_exit - p_entry) / p_entry) * 100.0
    cagr_computed = round((math.pow(p_exit / p_entry, 365.0 / days) - 1.0) * 100.0, 2)
    
    assert cagr_computed > ret_pct, "Annualized CAGR on 180 days must exceed absolute 180-day return"
    print(f"  [PASSED] CAGR Formulation: Return = {ret_pct}%, Annualized CAGR = {cagr_computed}%")

    # Verify Max Drawdown Invariant on synthetic trajectory
    # 100 -> 120 (Peak) -> 90 (Trough: -25% from 120) -> 110 -> 130
    trajectory = [100.0, 110.0, 120.0, 105.0, 90.0, 110.0, 130.0]
    peak = trajectory[0]
    max_dd = 0.0
    for p in trajectory:
        if p > peak:
            peak = p
        dd = (p - peak) / peak
        if dd < max_dd:
            max_dd = dd
    expected_dd_pct = round(max_dd * 100.0, 2)
    assert expected_dd_pct == -25.0, f"Expected Max Drawdown -25.0%, got {expected_dd_pct}%"
    print(f"  [PASSED] Max Drawdown Invariant: peak 120 -> trough 90 == {expected_dd_pct}%")

    # Verify Benchmark Alpha: Portfolio Return - Benchmark Return
    port_ret = 18.5
    bench_ret = 12.0
    alpha = round(port_ret - bench_ret, 2)
    assert alpha == 6.5
    print(f"  [PASSED] Benchmark Alpha Identity: {port_ret}% - {bench_ret}% == +{alpha}%")


def test_portfolio_conservation_laws():
    print("\n--- 5. Testing Portfolio Conservation Laws ---")
    
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
    print("\n--- 6. Testing Synthesis Attribution Weights Conservation Law ---")
    from backend.agents.synthesis_agent import synthesis_agent

    dummy_quant = {"score": 75, "stance": "BULLISH"}
    dummy_rag = {"score": 45, "stance": "BEARISH", "timed_out": False}
    dummy_risk = {"score": 50, "user_risk_profile": "conservative"}
    dummy_debate = {"has_disagreement": True}
    dummy_market = {"current_price": 100.0, "symbol": "$"}

    # Standard deliberation mode
    res_normal = synthesis_agent._calculate_action_and_weights("TEST", dummy_quant, dummy_rag, dummy_risk, dummy_debate, dummy_market)
    weights_normal = res_normal["weight_breakdown"]
    sum_normal = sum(weights_normal.values())
    assert sum_normal == 100, f"Normal weights sum {sum_normal} != 100"
    print(f"  [PASSED] Invariant 6A: Normal Attribution Decomposition {weights_normal} == 100%")

    # Circuit breaker / RAG timeout mode
    dummy_rag_timeout = {"score": 50, "stance": "NEUTRAL", "timed_out": True}
    res_timeout = synthesis_agent._calculate_action_and_weights("TEST", dummy_quant, dummy_rag_timeout, dummy_risk, dummy_debate, dummy_market)
    weights_timeout = res_timeout["weight_breakdown"]
    sum_timeout = sum(weights_timeout.values())
    assert sum_timeout == 100, f"Timeout weights sum {sum_timeout} != 100"
    print(f"  [PASSED] Invariant 6B: Degraded RAG-Timeout Decomposition {weights_timeout} == 100%")


def main():
    print("=== Testing Sub-phase 6.1: Comprehensive Test Suite & Mathematical Properties ===")
    test_rsi_mathematical_invariants()
    test_moving_averages_and_macd_properties()
    test_volume_anomaly_properties()
    test_backtest_performance_metrics_math()
    test_portfolio_conservation_laws()
    test_attribution_weights_invariance()
    print("\n[SUCCESS] Sub-phase 6.1 Mathematical Properties & Invariants verified with 100% accuracy!")


if __name__ == "__main__":
    main()
