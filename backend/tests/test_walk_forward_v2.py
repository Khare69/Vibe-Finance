"""
Unit and Property Tests for Institutional Walk-Forward Backtesting v2.
Verifies multi-window rolling execution, Calmar/Profit Factor metrics,
slippage/fee modeling, and point-in-time integrity.
"""

import os
import sys
import math
from contextlib import contextmanager

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.backtest.simulator import backtest_simulator


def test_single_window_institutional_metrics():
    """Verifies Calmar ratio, Profit Factor, and slippage deduction in single-window mode."""
    res = backtest_simulator.simulate(
        ticker="NVDA",
        historical_date="2024-10-15",
        holding_days=60,
        slippage_bps=10.0
    )
    assert res["status"] in ["SUCCESS", "FALLBACK_INSUFFICIENT_HISTORY"]
    assert "performance_metrics" in res
    metrics = res["performance_metrics"]

    # Invariants
    assert "calmar_ratio" in metrics
    assert "profit_factor" in metrics
    assert "information_ratio" in metrics
    assert "tracking_error_pct" in metrics
    assert "slippage_bps" in metrics
    assert metrics["slippage_bps"] == 10.0
    assert "net_return_pct" in metrics

    # Net return must equal actual return minus slippage drag (10 bps = 0.10%)
    expected_drag = 0.10
    assert abs((res["actual_return_pct"] - expected_drag) - metrics["net_return_pct"]) <= 0.02


def test_rolling_walk_forward_multi_window_execution():
    """Verifies that rolling walk-forward generates sequential point-in-time windows."""
    res = backtest_simulator.simulate_rolling_walk_forward(
        ticker="NVDA",
        num_windows=3,
        window_days=45,
        slippage_bps=10.0
    )
    assert res["simulation_mode"] == "rolling_walk_forward"
    assert "cumulative_metrics" in res
    cum = res["cumulative_metrics"]

    assert cum["total_windows"] >= 2
    assert "strategy_return_pct" in cum
    assert "buy_and_hold_return_pct" in cum
    assert "benchmark_return_pct" in cum
    assert "cumulative_alpha_pct" in cum
    assert "recommendation_hit_rate_pct" in cum
    assert 0.0 <= cum["recommendation_hit_rate_pct"] <= 100.0

    # Invariant: windows count matches breakdown
    assert len(res["windows"]) == cum["total_windows"]
    for w in res["windows"]:
        assert "window_index" in w
        assert "entry_date" in w
        assert "exit_date" in w
        assert "recommendation" in w
        assert "is_hit" in w
        assert w["entry_date"] < w["exit_date"]

    # Invariant: equity curve tracks windows
    assert len(res["equity_curve"]) == cum["total_windows"]
    for eq in res["equity_curve"]:
        assert "strategy_equity" in eq
        assert "asset_equity" in eq
        assert "benchmark_equity" in eq


def test_rolling_walk_forward_indian_asset():
    """Verifies rolling walk-forward against Nifty 50 benchmark for Indian assets."""
    res = backtest_simulator.simulate_rolling_walk_forward(
        ticker="RELIANCE",
        num_windows=2,
        window_days=45,
        slippage_bps=10.0
    )
    assert res["simulation_mode"] == "rolling_walk_forward"
    assert "NIFTY" in res["cumulative_metrics"]["benchmark_name"].upper()
    assert len(res["windows"]) >= 2


def test_rolling_walk_forward_fallback_honesty():
    """Verifies truthful offline fallback when ticker does not exist."""
    res = backtest_simulator._fallback_rolling_simulation(
        ticker="NONEXISTENT_TICKER",
        num_windows=4,
        window_days=45,
        slippage_bps=10.0
    )
    assert res["is_fallback"] is True
    assert res["status"] == "FALLBACK_INSUFFICIENT_HISTORY"
    assert res["cumulative_metrics"]["strategy_return_pct"] == 0.0
    assert res["cumulative_metrics"]["recommendation_hit_rate_pct"] == 0.0
    assert len(res["windows"]) == 0


if __name__ == "__main__":
    print("Running Institutional Walk-Forward v2 Test Suite...")
    test_single_window_institutional_metrics()
    test_rolling_walk_forward_multi_window_execution()
    test_rolling_walk_forward_indian_asset()
    test_rolling_walk_forward_fallback_honesty()
    print("ALL WALK-FORWARD V2 TESTS PASSED!")
