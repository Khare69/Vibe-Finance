import math
import time
import asyncio
from typing import Dict, Any, List


class BehavioralAgent:
    """
    Behavioral Risk Manager Agent.
    Evaluates individual investor psychology, panic selling propensity,
    risk capacity, and downweights speculative momentum to protect capital.
    """

    TOLERABLE_DRAWDOWN = {
        "conservative": 0.08,
        "moderate": 0.15,
        "aggressive": 0.28
    }

    STOCK_VOLATILITIES = {
        "RELIANCE": 0.22,
        "TCS": 0.18,
        "INFY": 0.24,
        "HDFCBANK": 0.19,
        "NVDA": 0.44,
        "AAPL": 0.21,
        "TSLA": 0.52
    }

    def analyze(self, ticker: str, user_profile: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.perf_counter()
        risk_level = user_profile.get("risk_level", "moderate").lower()
        panic_tendency = float(user_profile.get("panic_sell_tendency", 0.5))
        horizon = user_profile.get("investment_horizon", "medium").lower()

        # Volatility: use live computed volatility from market_data if available, otherwise baseline
        ticker_up = ticker.upper()
        annual_vol = float(
            market_data.get("annualized_volatility")
            or self.STOCK_VOLATILITIES.get(ticker_up, 0.25)
        )

        # Standard quantitative square-root-of-time scaling:
        # Weekly volatility = annual_vol / sqrt(52)
        # Approximate 95% 1-week Value-at-Risk (VaR) = 1.65 * weekly_vol
        weekly_vol = annual_vol / math.sqrt(52.0)
        weekly_drawdown_risk = round(1.65 * weekly_vol, 4)

        max_tolerable = self.TOLERABLE_DRAWDOWN.get(risk_level, 0.15)
        adjustments: List[str] = []

        # Behavioral adjustment checks
        if panic_tendency >= 0.7:
            adjustments.append(f"User has high panic-sell score ({panic_tendency:.2f}). Down-weighting breakout momentum.")
        elif panic_tendency <= 0.3:
            adjustments.append(f"User exhibits high emotional discipline (panic-sell score {panic_tendency:.2f}). Allowing normal risk budget.")

        if weekly_drawdown_risk > max_tolerable:
            adjustments.append(
                f"Estimated 1-week 95% downside volatility of {round(weekly_drawdown_risk * 100, 1)}% exceeds user's stated max tolerable weekly drawdown (-{int(max_tolerable * 100)}%)."
            )
        else:
            adjustments.append(
                f"Estimated 1-week 95% downside volatility of {round(weekly_drawdown_risk * 100, 1)}% remains within user's tolerable risk threshold ({int(max_tolerable * 100)}%)."
            )

        # Conditional staging advice
        if horizon == "short" and annual_vol > 0.30:
            adjustments.append("Short horizon combined with high volatility increases sequence-of-returns risk.")
        elif panic_tendency >= 0.6 or annual_vol > 0.35:
            adjustments.append("Suggesting staggered SIP / staged accumulation rather than lump-sum entry to mitigate volatility shock.")
        else:
            adjustments.append("Lump-sum or systematic entry permitted within volatility budget.")

        # Behavioral score calculation
        base_score = 65
        if risk_level == "conservative":
            base_score -= 15
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
            "behavioral_adjustments": adjustments
        }

    async def analyze_async(self, ticker: str, user_profile: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronous non-blocking interface for parallel agent execution."""
        return await asyncio.to_thread(self.analyze, ticker, user_profile, market_data)


behavioral_agent = BehavioralAgent()
