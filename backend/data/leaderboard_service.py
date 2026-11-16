"""
Market Leaderboard Service
Maintains a 5-minute sliding cache of top Indian equities across NIFTY indices,
ranking them by percentage returns (Top Gainers/Losers), volume breakout shockers,
and quantitative momentum scores.
"""

import time
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    from backend.data.market_service import market_service
    from backend.data.universe import universe_engine
except (ImportError, ValueError):
    from data.market_service import market_service
    from data.universe import universe_engine


class LeaderboardService:
    def __init__(self, ttl_seconds: int = 300):
        self._ttl_seconds = ttl_seconds
        self._cached_leaderboard: Optional[Dict[str, Any]] = None
        self._last_refresh_timestamp: float = 0.0

    def get_leaderboard(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Returns the ranked leaderboard.
        If the cache is older than 5 minutes (300 seconds) or force_refresh is True,
        it recomputes and ranks the leaderboard.
        """
        now = time.time()
        age = now - self._last_refresh_timestamp

        if not force_refresh and self._cached_leaderboard and age < self._ttl_seconds:
            # Add dynamic countdown seconds remaining
            time_remaining = max(0, int(self._ttl_seconds - age))
            return {
                **self._cached_leaderboard,
                "seconds_until_next_refresh": time_remaining,
                "is_cached": True
            }

        # Recompute leaderboard
        computed = self._compute_leaderboard()
        self._cached_leaderboard = computed
        self._last_refresh_timestamp = now

        return {
            **computed,
            "seconds_until_next_refresh": self._ttl_seconds,
            "is_cached": False
        }

    def _compute_leaderboard(self) -> Dict[str, Any]:
        """
        Samples the active Indian equity universe across Large-Cap, Mid-Cap, and Small-Cap
        to generate accurate rankings.
        """
        top_stocks = universe_engine.get_top_stocks(n=60)
        scored_stocks = []

        for stock in top_stocks:
            sym = stock["symbol"]
            mkt = market_service.get_market_data(sym)
            metrics = mkt.get("metrics") or {}

            price = float(mkt.get("current_price", 1000.0))
            change_pct = float(mkt.get("change_percent", 0.0))
            vol_ratio = float(mkt.get("volume_anomaly_ratio", 1.0))
            momentum = int(metrics.get("momentum_score", 50))
            beta = float(mkt.get("beta", stock.get("baseline_beta", 1.0)))

            scored_stocks.append({
                "symbol": sym,
                "company_name": stock.get("company_name", sym),
                "sector": stock.get("sector", "Diversified"),
                "cap_tier": stock.get("cap_tier", "Mid Cap"),
                "ticker": f"{sym}.NS",
                "price": price,
                "change_percent": change_pct,
                "volume_anomaly_ratio": round(vol_ratio, 2),
                "momentum_score": momentum,
                "beta": beta,
                "currency": "INR",
                "symbol_currency": "₹"
            })

        # Rank 1: Top Gainers (highest % return)
        gainers = sorted(scored_stocks, key=lambda s: s["change_percent"], reverse=True)
        top_gainers = [
            {**s, "rank": idx + 1} for idx, s in enumerate(gainers[:15])
        ]

        # Rank 2: Top Losers (lowest % return)
        losers = sorted(scored_stocks, key=lambda s: s["change_percent"])
        top_losers = [
            {**s, "rank": idx + 1} for idx, s in enumerate(losers[:15])
        ]

        # Rank 3: Volume Shockers (highest volume breakout ratio)
        volume_shockers = sorted(scored_stocks, key=lambda s: s["volume_anomaly_ratio"], reverse=True)
        top_volume_shockers = [
            {**s, "rank": idx + 1} for idx, s in enumerate(volume_shockers[:15])
        ]

        # Rank 4: Momentum Leaders (highest quantitative momentum score)
        momentum_leaders = sorted(scored_stocks, key=lambda s: s["momentum_score"], reverse=True)
        top_momentum_leaders = [
            {**s, "rank": idx + 1} for idx, s in enumerate(momentum_leaders[:15])
        ]

        now_utc = datetime.now(timezone.utc)

        return {
            "status": "success",
            "last_updated": now_utc.strftime("%H:%M:%S UTC"),
            "last_updated_iso": now_utc.isoformat(),
            "refresh_interval_seconds": self._ttl_seconds,
            "total_universe_scanned": len(scored_stocks),
            "rankings": {
                "top_gainers": top_gainers,
                "top_losers": top_losers,
                "volume_shockers": top_volume_shockers,
                "momentum_leaders": top_momentum_leaders
            }
        }


leaderboard_service = LeaderboardService(ttl_seconds=300)
