import time
import math
import asyncio
from typing import Dict, Any, List


class BehavioralAgent:
    """
    Behavioral Risk Manager Agent.
    Evaluates retail psychological vulnerabilities, panic selling propensities,
    historical drawdown tolerances, and portfolio concentration risks.
    Uses institutional square-root-of-time volatility scaling and 95% 1-week VaR.
    """

    STOCK_VOLATILITIES = {
        "TSLA": 52.0,
        "NVDA": 46.0,
        "RELIANCE": 22.0,
        "TCS": 18.0,
        "INFY": 24.0,
        "AAPL": 21.0,
        "HDFCBANK": 19.5
    }

    def analyze(self, ticker: str, user_profile: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.perf_counter()
        risk_level = user_profile.get("risk_level", "moderate").lower()
        panic_tendency = float(user_profile.get("panic_tendency", 0.4))
        loss_tolerance_pct = float(user_profile.get("loss_tolerance_pct", 15.0))

        ticker_up = ticker.upper()

        # Prioritize live computed annualized volatility if available in market_data
        if "annualized_volatility" in market_data and market_data["annualized_volatility"] is not None:
            # market_data annualized_volatility is in decimal form (e.g. 0.22)
            annual_vol = round(float(market_data["annualized_volatility"]) * 100.0, 1)
        else:
            annual_vol = self.STOCK_VOLATILITIES.get(ticker_up, 28.0)

        # Standard square-root-of-time scaling: weekly_vol = annual_vol / sqrt(52)
        # 95% 1-week Value-at-Risk (Parametric Normal approximation: 1.65 * sigma_weekly)
        weekly_vol = annual_vol / math.sqrt(52.0)
        weekly_drawdown_risk = round(1.65 * weekly_vol, 1)

        adjustments: List[str] = []
        base_score = 65

        # Maximum tolerable 1-week drawdown by risk tier
        if risk_level == "conservative":
            max_tolerable = 8.0
            if weekly_drawdown_risk > max_tolerable:
                adjustments.append(
                    f"Asset 1-week 95% drawdown risk ({weekly_drawdown_risk}%) exceeds conservative cap ({max_tolerable}%). "
                    f"Trim single-position sizing to <5% of total portfolio."
                )
        elif risk_level == "moderate":
            max_tolerable = 14.0
            if weekly_drawdown_risk > max_tolerable:
                adjustments.append(
                    f"Asset 1-week 95% drawdown risk ({weekly_drawdown_risk}%) exceeds moderate risk band ({max_tolerable}%). "
                    f"Implement strict trailing stop-loss."
                )
        else:
            max_tolerable = 20.0
            if weekly_drawdown_risk > max_tolerable:
                adjustments.append(
                    f"High-beta tail-risk profile ({weekly_drawdown_risk}% 1-week 95% VaR). Ensure portfolio rebalancing buffers are active."
                )

        if panic_tendency >= 0.6:
            adjustments.append(
                f"Elevated retail panic sensitivity detected ({int(panic_tendency * 100)}%). "
                f"Recommend pre-committing to automated rule-based limit orders."
            )

        # Staggered entry recommendations only trigger on genuinely volatile assets (>30% annual vol) or high panic tendency
        if annual_vol > 30.0 or panic_tendency >= 0.6:
            adjustments.append(
                f"High asset volatility ({annual_vol}% annualized). Allocate capital in 3 staggered SIP tranches over 60 days."
            )

        if risk_level == "conservative":
            base_score -= 10
        elif risk_level == "aggressive":
            base_score += 15

        if panic_tendency > 0.6:
            base_score -= int((panic_tendency - 0.5) * 30)

        if weekly_drawdown_risk > max_tolerable:
            base_score -= 10

        behavioral_score = max(20, min(85, base_score))

        if behavioral_score < 55 or panic_tendency > 0.65:
            stance = "CAUTION"
        elif behavioral_score >= 70:
            stance = "FAVORABLE"
        else:
            stance = "MODERATE"

        elapsed_ms = max(int((time.perf_counter() - start_time) * 1000), 1)

        return {
            "name": "Behavioral Risk Manager",
            "stance": stance,
            "score": behavioral_score,
            "latency_ms": elapsed_ms,
            "user_risk_profile": risk_level,
            "annualized_volatility": annual_vol,
            "weekly_95_var": weekly_drawdown_risk,
            "behavioral_adjustments": adjustments,
            "provenance": {
                "source": "PARAMETRIC_VAR_SCALING",
                "method": "square_root_of_time_95_var",
                "volatility_source": "live_market_data" if "annualized_volatility" in market_data else "catalog_baseline"
            }
        }

    async def analyze_async(self, ticker: str, user_profile: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronous non-blocking interface for parallel agent execution."""
        return await asyncio.to_thread(self.analyze, ticker, user_profile, market_data)


behavioral_agent = BehavioralAgent()
