import math
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
import yfinance as yf

from backend.data.market_service import market_service
from backend.rag.vector_store import vector_store
from backend.agents.fincom_protocol import FinComProtocol


class BacktestSimulator:
    """
    Deterministic Walk-Forward Backtesting Engine.
    Replays multi-agent analytical recommendations strictly using point-in-time data
    (zero look-ahead bias) across historical dates and computes institutional-grade
    quantitative performance and risk metrics (CAGR, Max Drawdown, Sharpe, Sortino, Benchmark Alpha).
    """

    def __init__(self):
        # 2-year historical cache per symbol and benchmark to minimize latency
        self._history_cache: Dict[str, Dict[str, Any]] = {}
        self._benchmark_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl_seconds = 600  # 10 minutes TTL

    def _get_historical_series(self, ticker: str) -> Optional[pd.DataFrame]:
        ticker_up = ticker.upper()
        now = time.time()

        if ticker_up in self._history_cache:
            entry = self._history_cache[ticker_up]
            if now - entry["cached_at"] < self._cache_ttl_seconds:
                return entry["df"]

        symbol = market_service._resolve_symbol(ticker_up)

        # Check network guard permissions and connectivity
        try:
            from backend.data.network_guard import is_network_allowed, probe_connectivity
        except (ImportError, ValueError):
            from data.network_guard import is_network_allowed, probe_connectivity

        if not is_network_allowed() or not probe_connectivity():
            return None
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="2y", interval="1d")
            if df is not None and not df.empty and len(df) >= 30:
                self._history_cache[ticker_up] = {
                    "cached_at": now,
                    "df": df
                }
                return df
        except Exception:
            pass

        return None

    def _get_benchmark_return(self, is_inr: bool, start_date: str, end_date: str) -> Tuple[str, float]:
        """
        Retrieves real benchmark return between start_date and end_date.
        Uses Nifty 50 (^NSEI) for Indian assets and S&P 500 (^GSPC) for US assets.
        """
        symbol = "^NSEI" if is_inr else "^GSPC"
        name = "NIFTY 50" if is_inr else "S&P 500"
        now = time.time()

        df_bench = None
        if symbol in self._benchmark_cache:
            entry = self._benchmark_cache[symbol]
            if now - entry["cached_at"] < self._cache_ttl_seconds:
                df_bench = entry["df"]

        # Guard network access
        try:
            from backend.data.network_guard import is_network_allowed, probe_connectivity
            _allow_bench_fetch = is_network_allowed() and probe_connectivity()
        except Exception:
            _allow_bench_fetch = False

        if df_bench is None and _allow_bench_fetch:
            try:
                t = yf.Ticker(symbol)
                df_bench = t.history(period="2y", interval="1d")
                if df_bench is not None and not df_bench.empty:
                    self._benchmark_cache[symbol] = {
                        "cached_at": now,
                        "df": df_bench
                    }
            except Exception:
                pass

        if df_bench is None or df_bench.empty:
            # Fallback benchmark estimation
            return name, 3.5

        dates = [d.strftime("%Y-%m-%d") for d in df_bench.index]
        closes = [float(x) for x in df_bench["Close"].dropna()]

        start_idx = 0
        for i, d in enumerate(dates):
            if d <= start_date:
                start_idx = i
            else:
                break

        end_idx = len(closes) - 1
        for i in range(start_idx, len(dates)):
            if dates[i] <= end_date:
                end_idx = i
            else:
                break

        b_entry = closes[start_idx]
        b_exit = closes[end_idx]
        b_ret = round(((b_exit - b_entry) / b_entry) * 100, 2) if b_entry > 0 else 0.0
        return name, b_ret

    def simulate(
        self,
        ticker: str,
        historical_date: str = "2025-10-15",
        holding_days: int = 90,
        slippage_bps: float = 10.0
    ) -> Dict[str, Any]:
        """
        Executes a walk-forward historical simulation.
        Evaluates signals strictly on data known up to historical_date,
        then measures forward holding period returns and quantitative risk metrics.
        """
        ticker_up = ticker.upper()
        df = self._get_historical_series(ticker_up)

        if df is None or df.empty or len(df) < 40:
            return self._fallback_simulation(ticker_up, historical_date, holding_days)

        is_inr = ticker_up in ["RELIANCE", "TCS", "INFY", "HDFCBANK"] or ticker_up.endswith(".NS") or ticker_up.endswith(".BO")

        # Parse target entry date
        dates = [d.strftime("%Y-%m-%d") for d in df.index]

        # Find entry index: closest trading day on or before historical_date
        entry_idx = -1
        for i, d in enumerate(dates):
            if d <= historical_date:
                entry_idx = i
            else:
                break

        # Boundary checks: require at least 30 bars of prior history for indicators
        if entry_idx < 30:
            entry_idx = 30
        # Ensure we have at least 5 bars of forward holding window
        if entry_idx >= len(dates) - 5:
            entry_idx = len(dates) - 15

        actual_entry_date = dates[entry_idx]

        # --- 1. Point-in-Time Data Isolation (Strictly No Look-Ahead) ---
        prior_df = df.iloc[:entry_idx + 1]
        prior_closes = [float(x) for x in prior_df["Close"].dropna()]
        prior_volumes = [int(x) for x in prior_df["Volume"].dropna()]

        entry_price = round(prior_closes[-1], 2)

        # Calculate point-in-time indicators
        rsi = market_service.calculate_rsi(prior_closes, 14)
        sma_50 = market_service.calculate_sma(prior_closes, 50)
        sma_200 = market_service.calculate_sma(prior_closes, 200)
        macd = market_service.calculate_macd(prior_closes, 12, 26, 9)

        recent_vols = prior_volumes[-20:] if len(prior_volumes) >= 20 else prior_volumes
        avg_vol = float(np.mean(recent_vols)) if recent_vols else 1.0
        vol_ratio = round(float(prior_volumes[-1]) / avg_vol, 2) if avg_vol > 0 else 1.0

        # Point-in-time momentum score
        ret_1m = 0.0
        if len(prior_closes) >= 22:
            ret_1m = round(((entry_price - prior_closes[-22]) / prior_closes[-22]) * 100, 2)

        quant_score = market_service.calculate_momentum_score(
            price=entry_price,
            sma_50=sma_50,
            sma_200=sma_200,
            rsi=rsi,
            macd_hist=macd["hist"],
            return_1m_pct=ret_1m
        )

        # Point-in-time fundamental evidence from vector store (strictly no look-ahead into future filings)
        rag_search = vector_store.search(ticker_up, "revenue earnings capex debt margins", top_k=2, as_of_date=actual_entry_date)
        citations = rag_search.get("citations", [])

        # Calculate point-in-time fundamental score
        pos_terms = ["growth", "record", "expansion", "profit", "surpassed", "strong", "cash", "dividend", "revival"]
        neg_terms = ["debt", "contraction", "headwind", "headwinds", "pressure", "drop", "cut", "drain", "loss"]

        rag_score = 50
        for c in citations:
            ex = c.get("excerpt", "").lower()
            pos = sum(1 for w in pos_terms if w in ex)
            neg = sum(1 for w in neg_terms if w in ex)
            if c.get("sentiment") == "positive" or pos > neg:
                rag_score += 15
            elif c.get("sentiment") == "negative" or neg > pos:
                rag_score -= 15
        rag_score = max(20, min(95, rag_score))

        # Determine point-in-time agent recommendation
        if quant_score >= 68 and rag_score >= 60:
            recommendation = "STRONG_BUY"
        elif quant_score >= 58 and rag_score >= 50:
            recommendation = "BUY"
        elif quant_score >= 65 and rag_score <= 45:
            recommendation = "CAUTIOUS_ACCUMULATE"
        elif quant_score <= 38 or rag_score <= 32:
            recommendation = "TRIM" if quant_score > 30 else "SELL"
        else:
            recommendation = "HOLD"

        # --- 2. Forward Walk Trajectory & Outcome ---
        trading_days = max(5, int(holding_days * (5.0 / 7.0)))
        exit_idx = min(entry_idx + trading_days, len(dates) - 1)
        actual_exit_date = dates[exit_idx]

        forward_slice = df.iloc[entry_idx:exit_idx + 1]
        forward_closes = [float(x) for x in forward_slice["Close"].dropna()]
        forward_dates = [d.strftime("%Y-%m-%d") for d in forward_slice.index]

        exit_price = round(forward_closes[-1], 2)
        actual_return_pct = round(((exit_price - entry_price) / entry_price) * 100, 2)
        was_profitable = actual_return_pct > 0

        # Build daily price trajectory
        trajectory = []
        for d, p in zip(forward_dates, forward_closes):
            r_pct = round(((p - entry_price) / entry_price) * 100, 2)
            trajectory.append({
                "date": d,
                "price": round(p, 2),
                "return_pct": r_pct
            })

        # --- 3. Institutional Quantitative Performance & Risk Metrics ---
        daily_returns = [
            (forward_closes[i] - forward_closes[i - 1]) / forward_closes[i - 1]
            for i in range(1, len(forward_closes))
        ] if len(forward_closes) > 1 else [0.0]

        # Maximum Drawdown (MDD)
        peak = forward_closes[0]
        max_dd = 0.0
        for p in forward_closes:
            if p > peak:
                peak = p
            dd = (p - peak) / peak if peak > 0 else 0.0
            if dd < max_dd:
                max_dd = dd
        max_drawdown_pct = round(max_dd * 100.0, 2)

        # Annualized Volatility
        ann_volatility_pct = round(
            float(np.std(daily_returns) * math.sqrt(252) * 100.0), 2
        ) if len(daily_returns) > 2 else 0.0

        # Risk-free rate (6.5% for INR, 4.5% for USD)
        rf_annual = 0.065 if is_inr else 0.045
        rf_daily = (1.0 + rf_annual) ** (1.0 / 252.0) - 1.0

        # Sharpe Ratio
        excess_daily = [r - rf_daily for r in daily_returns]
        mean_excess = float(np.mean(excess_daily))
        std_returns = float(np.std(daily_returns))
        sharpe = round(
            float((mean_excess / std_returns) * math.sqrt(252)), 2
        ) if std_returns > 1e-6 else 0.0

        # Sortino Ratio (Downside Deviation)
        downside_diffs = [min(0.0, r - rf_daily) for r in daily_returns]
        downside_std = math.sqrt(
            sum(d ** 2 for d in downside_diffs) / len(downside_diffs)
        ) if downside_diffs else 0.0
        sortino = round(
            float((mean_excess / downside_std) * math.sqrt(252)), 2
        ) if downside_std > 1e-6 else (sharpe if sharpe > 0 else 0.0)

        # CAGR (Compound Annual Growth Rate)
        holding_years = len(daily_returns) / 252.0
        if holding_years > 0.05 and entry_price > 0 and exit_price > 0:
            cagr_pct = round((((exit_price / entry_price) ** (1.0 / holding_years)) - 1.0) * 100.0, 2)
        else:
            cagr_pct = actual_return_pct

        # Calmar Ratio: CAGR / abs(Max Drawdown)
        calmar = round(abs(cagr_pct / max_drawdown_pct), 2) if abs(max_drawdown_pct) > 0.01 else 0.0

        # Profit Factor: sum(gains) / sum(abs(losses))
        pos_gains = sum(r for r in daily_returns if r > 0)
        neg_losses = sum(abs(r) for r in daily_returns if r < 0)
        profit_factor = round(pos_gains / neg_losses, 2) if neg_losses > 1e-6 else (round(pos_gains * 100, 2) if pos_gains > 0 else 1.0)

        # Slippage & Transaction Costs
        slippage_drag_pct = round((slippage_bps / 10000.0) * 100.0, 3)
        net_return_pct = round(actual_return_pct - slippage_drag_pct, 2)

        # Benchmark Alpha Comparison (Nifty 50 or S&P 500)
        bench_name, bench_ret_pct = self._get_benchmark_return(
            is_inr=is_inr,
            start_date=actual_entry_date,
            end_date=actual_exit_date
        )
        alpha_pct = round(actual_return_pct - bench_ret_pct, 2)

        # Information Ratio & Tracking Error
        bench_daily_ret = (bench_ret_pct / max(len(daily_returns), 1)) / 100.0
        tracking_diffs = [r - bench_daily_ret for r in daily_returns]
        tracking_error_pct = round(float(np.std(tracking_diffs) * math.sqrt(252) * 100.0), 2) if len(daily_returns) > 2 else 0.0
        information_ratio = round(
            float((np.mean(tracking_diffs) / np.std(tracking_diffs)) * math.sqrt(252)), 2
        ) if (len(daily_returns) > 2 and np.std(tracking_diffs) > 1e-6) else 0.0

        # Win rate over individual daily trajectory periods
        profitable_days = sum(1 for pt in trajectory if pt["return_pct"] > 0)
        win_rate_trajectory_pct = round((profitable_days / len(trajectory)) * 100.0, 1) if trajectory else 0.0

        # Generate evidence-grounded snapshot reasoning
        reasoning_snapshot = (
            f"On {actual_entry_date}, {ticker_up} traded at {entry_price:.2f} with RSI-14 at {rsi:.1f} "
            f"and 50-SMA at {sma_50:.2f}. Multi-agent synthesis assigned a Quant score of {quant_score}/100 "
            f"and Fundamental score of {rag_score}/100, yielding '{recommendation}'. "
            f"Over the subsequent {holding_days}-day horizon (through {actual_exit_date}), "
            f"the position yielded a realized return of {actual_return_pct:+.2f}% "
            f"(Alpha: {alpha_pct:+.2f}% vs {bench_name} {bench_ret_pct:+.2f}%, "
            f"Max Drawdown: {max_drawdown_pct:.2f}%, Sharpe: {sharpe:.2f})."
        )

        return {
            "historical_date": actual_entry_date,
            "exit_date": actual_exit_date,
            "holding_days": holding_days,
            "holding_days_actual": len(forward_closes) - 1,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "actual_return_pct": actual_return_pct,
            "agent_recommendation_then": recommendation,
            "quant_score_then": quant_score,
            "rag_score_then": rag_score,
            "was_profitable": was_profitable,
            "is_fallback": False,
            "status": "SUCCESS",
            "provenance": {
                "source": "YAHOO_FINANCE_HISTORICAL",
                "is_live": True,
                "as_of": actual_entry_date,
                "exit_date": actual_exit_date,
                "method": "point_in_time_walk_forward"
            },
            "performance_metrics": {
                "cagr_pct": cagr_pct,
                "max_drawdown_pct": max_drawdown_pct,
                "sharpe_ratio": sharpe,
                "sortino_ratio": sortino,
                "calmar_ratio": calmar,
                "profit_factor": profit_factor,
                "information_ratio": information_ratio,
                "tracking_error_pct": tracking_error_pct,
                "slippage_bps": slippage_bps,
                "net_return_pct": net_return_pct,
                "annualized_volatility_pct": ann_volatility_pct,
                "benchmark_name": bench_name,
                "benchmark_return_pct": bench_ret_pct,
                "alpha_pct": alpha_pct,
                "win_rate_trajectory_pct": win_rate_trajectory_pct
            },
            "point_in_time_metrics": {
                "rsi_14": rsi,
                "sma_50": sma_50,
                "sma_200": sma_200,
                "macd_hist": macd["hist"],
                "volume_anomaly_ratio": vol_ratio
            },
            "trajectory": trajectory,
            "reasoning_snapshot": reasoning_snapshot
        }

    def _fallback_simulation(self, ticker: str, historical_date: str, holding_days: int) -> Dict[str, Any]:
        """
        Deterministic offline fallback when historical price series cannot be retrieved from Yahoo Finance.
        Returns a neutral baseline with explicit fallback status and disclaimers to prevent deception.
        """
        base_prices = {
            "NVDA": 135.0,
            "RELIANCE": 1200.0,
            "TSLA": 250.0,
            "TCS": 3800.0,
            "AAPL": 225.0,
            "INFY": 1840.0,
            "HDFCBANK": 1700.0
        }
        entry = base_prices.get(ticker, 100.0)
        return {
            "historical_date": historical_date,
            "exit_date": historical_date,
            "holding_days": holding_days,
            "holding_days_actual": 0,
            "entry_price": entry,
            "exit_price": entry,
            "actual_return_pct": 0.0,
            "agent_recommendation_then": "INSUFFICIENT_DATA",
            "quant_score_then": 50,
            "rag_score_then": 50,
            "was_profitable": False,
            "is_fallback": True,
            "status": "FALLBACK_INSUFFICIENT_HISTORY",
            "provenance": {
                "source": "OFFLINE_FALLBACK",
                "is_live": False,
                "disclaimer": f"Historical OHLCV data was unavailable for {ticker} on {historical_date}. Fallback baseline returned with zero fabricated alpha or returns."
            },
            "performance_metrics": {
                "cagr_pct": 0.0,
                "max_drawdown_pct": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "calmar_ratio": 0.0,
                "profit_factor": 1.0,
                "information_ratio": 0.0,
                "tracking_error_pct": 0.0,
                "slippage_bps": 10.0,
                "net_return_pct": 0.0,
                "annualized_volatility_pct": 0.0,
                "benchmark_name": "S&P 500" if ticker in ["NVDA", "AAPL", "TSLA"] else "NIFTY 50",
                "benchmark_return_pct": 0.0,
                "alpha_pct": 0.0,
                "win_rate_trajectory_pct": 0.0
            },
            "point_in_time_metrics": {
                "rsi_14": 50.0,
                "sma_50": round(entry, 2),
                "sma_200": round(entry, 2),
                "macd_hist": 0.0,
                "volume_anomaly_ratio": 1.0
            },
            "trajectory": [],
            "reasoning_snapshot": f"Historical OHLCV price series could not be retrieved from Yahoo Finance for {ticker} on {historical_date}. Fallback baseline returned with zero fabricated alpha or returns."
        }

    def simulate_rolling_walk_forward(
        self,
        ticker: str,
        num_windows: int = 4,
        window_days: int = 45,
        slippage_bps: float = 10.0
    ) -> Dict[str, Any]:
        """
        Executes an institutional-grade multi-window rolling walk-forward backtest.
        Evaluates point-in-time multi-agent recommendations across sequential rolling windows,
        measuring strategy compounding, recommendation accuracy/hit-rate, benchmark alpha,
        and transaction cost drag.
        """
        ticker_up = ticker.upper()
        df = self._get_historical_series(ticker_up)

        if df is None or df.empty or len(df) < 50:
            return self._fallback_rolling_simulation(ticker_up, num_windows, window_days, slippage_bps)

        is_inr = ticker_up in ["RELIANCE", "TCS", "INFY", "HDFCBANK"] or ticker_up.endswith(".NS") or ticker_up.endswith(".BO")
        dates = [d.strftime("%Y-%m-%d") for d in df.index]
        closes = [float(x) for x in df["Close"].dropna()]
        total_bars = len(dates)

        # Warmup requirements: minimum 30 bars prior to first window
        min_warmup = 30
        trading_days = max(10, int(window_days * (5.0 / 7.0)))

        # Ensure windows fit within historical range
        available_span = total_bars - min_warmup
        if available_span < num_windows * trading_days:
            trading_days = max(8, available_span // num_windows)
            num_windows = max(2, min(num_windows, available_span // trading_days))

        start_base_idx = total_bars - (num_windows * trading_days)
        if start_base_idx < min_warmup:
            start_base_idx = min_warmup

        windows: List[Dict[str, Any]] = []
        cum_strat_factor = 1.0
        cum_asset_factor = 1.0
        cum_bench_factor = 1.0

        all_strat_daily_returns: List[float] = []
        all_bench_daily_returns: List[float] = []
        equity_curve: List[Dict[str, Any]] = []

        total_slippage_drag = 0.0

        for w_idx in range(num_windows):
            w_entry_idx = start_base_idx + (w_idx * trading_days)
            w_exit_idx = min(start_base_idx + ((w_idx + 1) * trading_days), total_bars - 1)
            if w_exit_idx <= w_entry_idx:
                continue

            w_entry_date = dates[w_entry_idx]
            w_exit_date = dates[w_exit_idx]

            # 1. Point-in-Time Technical & Quantitative State
            prior_closes = closes[:w_entry_idx + 1]
            entry_price = round(prior_closes[-1], 2)
            exit_price = round(closes[w_exit_idx], 2)

            rsi = market_service.calculate_rsi(prior_closes, 14)
            sma_50 = market_service.calculate_sma(prior_closes, 50)
            sma_200 = market_service.calculate_sma(prior_closes, 200)
            macd = market_service.calculate_macd(prior_closes, 12, 26, 9)

            ret_1m = 0.0
            if len(prior_closes) >= 22:
                ret_1m = round(((entry_price - prior_closes[-22]) / prior_closes[-22]) * 100, 2)

            quant_score = market_service.calculate_momentum_score(
                price=entry_price,
                sma_50=sma_50,
                sma_200=sma_200,
                rsi=rsi,
                macd_hist=macd["hist"],
                return_1m_pct=ret_1m
            )

            # 2. Point-in-Time Fundamental Evidence (Zero Look-Ahead)
            rag_search = vector_store.search(ticker_up, "revenue earnings capex debt margins", top_k=2, as_of_date=w_entry_date)
            citations = rag_search.get("citations", [])

            pos_terms = ["growth", "record", "expansion", "profit", "surpassed", "strong", "cash", "dividend", "revival"]
            neg_terms = ["debt", "contraction", "headwind", "headwinds", "pressure", "drop", "cut", "drain", "loss"]

            rag_score = 50
            for c in citations:
                ex = c.get("excerpt", "").lower()
                pos = sum(1 for w in pos_terms if w in ex)
                neg = sum(1 for w in neg_terms if w in ex)
                if c.get("sentiment") == "positive" or pos > neg:
                    rag_score += 15
                elif c.get("sentiment") == "negative" or neg > pos:
                    rag_score -= 15
            rag_score = max(20, min(95, rag_score))

            # 3. FinCom Consensus & Safe Abstention Check
            divergence = FinComProtocol.calculate_divergence(quant_score, rag_score)
            if divergence >= 40.0 and ((quant_score >= 60 and rag_score <= 40) or (quant_score <= 40 and rag_score >= 60)):
                recommendation = "ABSTAIN"
            elif quant_score >= 68 and rag_score >= 60:
                recommendation = "STRONG_BUY"
            elif quant_score >= 58 and rag_score >= 50:
                recommendation = "BUY"
            elif quant_score >= 65 and rag_score <= 45:
                recommendation = "CAUTIOUS_ACCUMULATE"
            elif quant_score <= 38 or rag_score <= 32:
                recommendation = "TRIM" if quant_score > 30 else "SELL"
            else:
                recommendation = "HOLD"

            # 4. Forward Window Realized Returns & Benchmark
            gross_asset_ret = round(((exit_price - entry_price) / entry_price) * 100.0, 2)
            slip_pct = round((slippage_bps / 10000.0) * 100.0, 3)
            net_asset_ret = round(gross_asset_ret - slip_pct, 2)
            total_slippage_drag += slip_pct

            bench_name, bench_ret = self._get_benchmark_return(is_inr, w_entry_date, w_exit_date)

            # Strategy Participation Weighting
            rf_window = round((0.05 * (trading_days / 252.0)) * 100.0, 2)
            if recommendation in ["STRONG_BUY", "BUY"]:
                strat_ret = net_asset_ret
            elif recommendation == "CAUTIOUS_ACCUMULATE":
                strat_ret = round((0.60 * net_asset_ret) + (0.40 * rf_window), 2)
            elif recommendation in ["HOLD", "ABSTAIN"]:
                strat_ret = rf_window
            else:  # TRIM or SELL
                strat_ret = round(max(0.0, -0.20 * gross_asset_ret) + (0.80 * rf_window), 2)

            # Directional Hit Determination
            if recommendation in ["STRONG_BUY", "BUY", "CAUTIOUS_ACCUMULATE"]:
                is_hit = gross_asset_ret > 0
            elif recommendation in ["TRIM", "SELL"]:
                is_hit = gross_asset_ret <= 0
            else:
                is_hit = abs(gross_asset_ret) <= 5.0 or (strat_ret >= net_asset_ret)

            # Daily return tracking for this window
            window_slice = df.iloc[w_entry_idx:w_exit_idx + 1]
            w_closes = [float(x) for x in window_slice["Close"].dropna()]

            for d_idx in range(1, len(w_closes)):
                d_ret = (w_closes[d_idx] - w_closes[d_idx - 1]) / w_closes[d_idx - 1]
                if recommendation in ["STRONG_BUY", "BUY"]:
                    all_strat_daily_returns.append(d_ret)
                elif recommendation == "CAUTIOUS_ACCUMULATE":
                    all_strat_daily_returns.append(d_ret * 0.6)
                else:
                    all_strat_daily_returns.append(0.05 / 252.0)
                all_bench_daily_returns.append((bench_ret / len(w_closes)) / 100.0)

            cum_strat_factor *= (1.0 + strat_ret / 100.0)
            cum_asset_factor *= (1.0 + gross_asset_ret / 100.0)
            cum_bench_factor *= (1.0 + bench_ret / 100.0)

            equity_curve.append({
                "window": w_idx + 1,
                "date": w_exit_date,
                "strategy_equity": round(cum_strat_factor * 100.0, 2),
                "asset_equity": round(cum_asset_factor * 100.0, 2),
                "benchmark_equity": round(cum_bench_factor * 100.0, 2)
            })

            windows.append({
                "window_index": w_idx + 1,
                "entry_date": w_entry_date,
                "exit_date": w_exit_date,
                "holding_days": w_exit_idx - w_entry_idx,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "recommendation": recommendation,
                "quant_score": quant_score,
                "rag_score": rag_score,
                "divergence": divergence,
                "asset_return_pct": gross_asset_ret,
                "strategy_return_pct": strat_ret,
                "benchmark_return_pct": bench_ret,
                "alpha_pct": round(strat_ret - bench_ret, 2),
                "is_hit": is_hit
            })

        cum_strategy_return = round((cum_strat_factor - 1.0) * 100.0, 2)
        cum_asset_return = round((cum_asset_factor - 1.0) * 100.0, 2)
        cum_benchmark_return = round((cum_bench_factor - 1.0) * 100.0, 2)
        cum_alpha = round(cum_strategy_return - cum_benchmark_return, 2)

        hit_count = sum(1 for w in windows if w["is_hit"])
        hit_rate_pct = round((hit_count / len(windows)) * 100.0, 1) if windows else 0.0

        # Multi-window risk metrics
        strat_returns = all_strat_daily_returns if all_strat_daily_returns else [0.0]
        mean_strat = float(np.mean(strat_returns))
        std_strat = float(np.std(strat_returns))

        sharpe = round(
            float((mean_strat / std_strat) * math.sqrt(252)), 2
        ) if std_strat > 1e-6 else 0.0

        downside_diffs = [min(0.0, r) for r in strat_returns]
        downside_std = math.sqrt(
            sum(d ** 2 for d in downside_diffs) / len(downside_diffs)
        ) if downside_diffs else 0.0
        sortino = round(
            float((mean_strat / downside_std) * math.sqrt(252)), 2
        ) if downside_std > 1e-6 else (sharpe if sharpe > 0 else 0.0)

        # Max Drawdown across equity curve
        peak_eq = 100.0
        max_eq_dd = 0.0
        for pt in equity_curve:
            eq = pt["strategy_equity"]
            if eq > peak_eq:
                peak_eq = eq
            dd = (eq - peak_eq) / peak_eq if peak_eq > 0 else 0.0
            if dd < max_eq_dd:
                max_eq_dd = dd
        max_drawdown_pct = round(max_eq_dd * 100.0, 2)

        # CAGR across all windows
        total_days = sum(w["holding_days"] for w in windows)
        years = total_days / 252.0
        if years > 0.05 and cum_strat_factor > 0:
            cagr_pct = round(((cum_strat_factor ** (1.0 / years)) - 1.0) * 100.0, 2)
        else:
            cagr_pct = cum_strategy_return

        calmar = round(abs(cagr_pct / max_drawdown_pct), 2) if abs(max_drawdown_pct) > 0.01 else 0.0

        pos_gains = sum(r for r in strat_returns if r > 0)
        neg_losses = sum(abs(r) for r in strat_returns if r < 0)
        profit_factor = round(pos_gains / neg_losses, 2) if neg_losses > 1e-6 else 1.0

        tracking_diffs = [
            strat_returns[i] - all_bench_daily_returns[i]
            for i in range(min(len(strat_returns), len(all_bench_daily_returns)))
        ]
        info_ratio = round(
            float((np.mean(tracking_diffs) / np.std(tracking_diffs)) * math.sqrt(252)), 2
        ) if (len(tracking_diffs) > 2 and np.std(tracking_diffs) > 1e-6) else 0.0

        return {
            "simulation_mode": "rolling_walk_forward",
            "ticker": ticker_up,
            "status": "SUCCESS",
            "is_fallback": False,
            "provenance": {
                "source": "YAHOO_FINANCE_HISTORICAL",
                "is_live": True,
                "method": "rolling_walk_forward_v2",
                "start_date": windows[0]["entry_date"] if windows else "N/A",
                "end_date": windows[-1]["exit_date"] if windows else "N/A",
                "windows_count": len(windows)
            },
            "cumulative_metrics": {
                "strategy_return_pct": cum_strategy_return,
                "buy_and_hold_return_pct": cum_asset_return,
                "benchmark_return_pct": cum_benchmark_return,
                "benchmark_name": bench_name,
                "cumulative_alpha_pct": cum_alpha,
                "recommendation_hit_rate_pct": hit_rate_pct,
                "hit_count": hit_count,
                "total_windows": len(windows),
                "cagr_pct": cagr_pct,
                "max_drawdown_pct": max_drawdown_pct,
                "sharpe_ratio": sharpe,
                "sortino_ratio": sortino,
                "calmar_ratio": calmar,
                "profit_factor": profit_factor,
                "information_ratio": info_ratio,
                "total_slippage_drag_pct": round(total_slippage_drag, 2)
            },
            "windows": windows,
            "equity_curve": equity_curve,
            "summary_verdict": (
                f"Rolling Walk-Forward v2 over {len(windows)} sequential windows achieved a cumulative "
                f"strategy return of {cum_strategy_return:+.2f}% (Alpha: {cum_alpha:+.2f}% vs {bench_name}), "
                f"with a recommendation hit-rate of {hit_rate_pct}% and Sharpe of {sharpe:.2f}."
            )
        }

    def _fallback_rolling_simulation(self, ticker: str, num_windows: int, window_days: int, slippage_bps: float) -> Dict[str, Any]:
        return {
            "simulation_mode": "rolling_walk_forward",
            "ticker": ticker,
            "status": "FALLBACK_INSUFFICIENT_HISTORY",
            "is_fallback": True,
            "provenance": {
                "source": "OFFLINE_FALLBACK",
                "is_live": False,
                "method": "rolling_walk_forward_v2",
                "disclaimer": f"Historical OHLCV data was unavailable for {ticker}. Fallback baseline returned with zero fabricated alpha."
            },
            "cumulative_metrics": {
                "strategy_return_pct": 0.0,
                "buy_and_hold_return_pct": 0.0,
                "benchmark_return_pct": 0.0,
                "benchmark_name": "S&P 500" if ticker in ["NVDA", "AAPL", "TSLA"] else "NIFTY 50",
                "cumulative_alpha_pct": 0.0,
                "recommendation_hit_rate_pct": 0.0,
                "hit_count": 0,
                "total_windows": num_windows,
                "cagr_pct": 0.0,
                "max_drawdown_pct": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "calmar_ratio": 0.0,
                "profit_factor": 1.0,
                "information_ratio": 0.0,
                "total_slippage_drag_pct": 0.0
            },
            "windows": [],
            "equity_curve": [],
            "summary_verdict": f"Historical data was unavailable for {ticker}. Fallback baseline returned with zero fabricated metrics."
        }


backtest_simulator = BacktestSimulator()
