from datetime import datetime, timezone
from typing import Dict, Any

from backend.agents.llm_client import llm_client


class SynthesisAgent:
    """
    Synthesis Agent responsible for calculating weighted action recommendations,
    generating headlines, and formulating multi-tiered explanations (Beginner & Expert).
    Supports Gemini LLM reasoning with generalized deterministic fallback templates and async networking.
    """

    def _calculate_action_and_weights(
        self,
        ticker: str,
        quant_result: Dict[str, Any],
        rag_result: Dict[str, Any],
        behavioral_result: Dict[str, Any],
        debate_result: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        quant_score = quant_result.get("score", 50)
        rag_score = rag_result.get("score", 50)
        behavioral_score = behavioral_result.get("score", 50)
        rag_timed_out = rag_result.get("timed_out", False)
        has_disagreement = debate_result.get("has_disagreement", False)
        user_risk = behavioral_result.get("user_risk_profile", "moderate")
        price = market_data.get("current_price", 100.0)
        symbol = market_data.get("symbol", "₹" if ticker.upper() in ["RELIANCE", "TCS", "INFY", "HDFCBANK"] else "$")

        # Dynamic weighting
        if rag_timed_out:
            weight_breakdown = {
                "technicals": 60,
                "fundamentals": 0,
                "risk_profile": 40
            }
            weighted_score = (quant_score * 0.60) + (behavioral_score * 0.40)
            asset_conviction_score = float(quant_score)
        else:
            weight_breakdown = {
                "technicals": 35,
                "fundamentals": 40,
                "risk_profile": 25
            }
            weighted_score = (quant_score * 0.35) + (rag_score * 0.40) + (behavioral_score * 0.25)
            asset_conviction_score = (quant_score * 0.45) + (rag_score * 0.55)

        # Enforce mathematical invariance: attribution weights must strictly sum to 100%
        total_weight = sum(weight_breakdown.values())
        if total_weight != 100:
            scale = 100.0 / total_weight
            weight_breakdown = {k: int(round(v * scale)) for k, v in weight_breakdown.items()}
            discrepancy = 100 - sum(weight_breakdown.values())
            if discrepancy != 0:
                highest_k = max(weight_breakdown, key=weight_breakdown.get)
                weight_breakdown[highest_k] += discrepancy

        total_check = sum(weight_breakdown.values())
        if total_check != 100:
            raise ValueError(f"Attribution weights sum ({total_check}) must equal 100")

        # Action determination
        if rag_timed_out:
            headline = "Recommendation based on Technicals only; Fundamental analysis pending"
            if quant_score >= 75:
                final_action = "BUY"
            elif quant_score <= 40:
                final_action = "SELL"
            else:
                final_action = "HOLD"
        elif has_disagreement and quant_score >= 68 and rag_score <= 45 and user_risk == "conservative":
            final_action = "CAUTIOUS_ACCUMULATE"
            dip_price = round(price * 0.98, 1)
            headline = f"Wait for Pullback near {symbol}{dip_price:,.1f}: Strong Momentum Restrained by Fundamental Headwinds & Risk Limit"
        elif weighted_score >= 80:
            final_action = "STRONG_BUY"
            headline = f"High Conviction Buy on {ticker}: Strong Fundamentals & Technical Alignment"
        elif weighted_score >= 65:
            final_action = "BUY"
            headline = f"Favorable Risk/Reward on {ticker}: Momentum Supported by Operational Metrics"
        elif weighted_score >= 52:
            final_action = "CAUTIOUS_ACCUMULATE"
            headline = f"Accumulate on Pullbacks: Moderate Valuation Headwinds Temper Momentum"
        elif weighted_score >= 42:
            final_action = "HOLD"
            headline = f"Neutral Hold on {ticker}: Wait for Clarity in Earnings or Price Consolidation"
        elif weighted_score >= 30:
            final_action = "TRIM"
            headline = f"Trim Exposure on {ticker}: Deteriorating Fundamentals and Weak Technical Structure"
        else:
            final_action = "SELL"
            headline = f"De-risk Position in {ticker}: Elevated Downside Volatility and High Risk Penalties"

        # Dynamically compute macro regime attributes from live computed metrics
        beta = float(market_data.get("beta", 1.0))
        annual_vol = float(market_data.get("annualized_volatility", 0.25))

        if annual_vol > 0.35 or beta > 1.3:
            vol_env = f"High Beta ({beta:.2f}x) / High Volatility ({int(annual_vol * 100)}% ann.)"
        elif annual_vol < 0.20 and beta < 0.9:
            vol_env = f"Defensive Low Beta ({beta:.2f}x) / Low Volatility ({int(annual_vol * 100)}% ann.)"
        else:
            vol_env = f"Market-Aligned Beta ({beta:.2f}x) / Moderate Volatility ({int(annual_vol * 100)}% ann.)"

        if quant_score >= 65 and rag_score >= 60:
            regime_title = "Expansionary Growth & Momentum Regime"
        elif quant_score <= 40 and rag_score <= 45:
            regime_title = "Capital Preservation & De-risking Regime"
        elif has_disagreement:
            regime_title = "Dialectic Cross-Current Regime (Quant/Fundamental Divergence)"
        elif rag_timed_out:
            regime_title = "Technical Momentum-Only Regime (RAG Degraded)"
        else:
            regime_title = "Consolidation & Range-Bound Regime"

        bias_explanation = (
            f"Consensus weights: {weight_breakdown.get('technicals', 0)}% technicals, "
            f"{weight_breakdown.get('fundamentals', 0)}% fundamentals, "
            f"{weight_breakdown.get('risk_profile', 0)}% risk constraints."
        )

        active_regime = {
            "regime_title": regime_title,
            "volatility_environment": vol_env,
            "bias_explanation": bias_explanation,
            "provenance": {
                "source": market_data.get("feed_status", "LIVE_YAHOO"),
                "as_of": market_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "method": "computed_dynamic_factors"
            }
        }

        return {
            "final_action": final_action,
            "headline": headline,
            "weight_breakdown": weight_breakdown,
            "macro_regime": active_regime,
            "quant_score": quant_score,
            "rag_score": rag_score,
            "behavioral_score": behavioral_score,
            "asset_conviction_score": round(asset_conviction_score, 1),
            "rag_timed_out": rag_timed_out,
            "has_disagreement": has_disagreement,
            "user_risk": user_risk
        }

    def _build_algorithmic_explanations(self, ticker: str, meta: Dict[str, Any]) -> Dict[str, str]:
        quant_score = meta["quant_score"]
        rag_score = meta["rag_score"]
        behavioral_score = meta["behavioral_score"]
        user_risk = meta["user_risk"]

        if meta["rag_timed_out"]:
            expert_exp = (
                f"Evaluation for {ticker} conducted exclusively via technical momentum indicators (score: {quant_score}/100) "
                f"due to upstream filing RAG retrieval timeout. Fundamental weight zeroed out and confidence bounds discounted."
            )
            beginner_exp = (
                f"Our system could only review {ticker}'s price chart today because corporate filings were temporarily unavailable. "
                f"This signal is based on market trend speed only—proceed with extra caution."
            )
        elif meta["has_disagreement"]:
            expert_exp = (
                f"Consensus reflects a cross-agent divergence on {ticker}: Quantitative momentum ({quant_score}/100) conflicts "
                f"with fundamental filing disclosures ({rag_score}/100). Behavioral risk filters ({behavioral_score}/100) enforce "
                f"capital preservation under a {user_risk} mandate."
            )
            beginner_exp = (
                f"There is a tug-of-war on {ticker}: the stock price has strong momentum, but the company's financial documents "
                f"show warning signs. Because of your {user_risk} investment preference, we recommend a cautious, risk-managed approach."
            )
        else:
            expert_exp = (
                f"Synthesized recommendation for {ticker} balances quantitative trend indicators ({quant_score}/100) against "
                f"fundamental disclosures ({rag_score}/100), calibrated through a {user_risk} risk budget ({behavioral_score}/100)."
            )
            beginner_exp = (
                f"We evaluated {ticker}'s market momentum alongside its business health from regulatory filings. "
                f"The final signal aligns with your {user_risk} risk comfort zone."
            )

        return {"expert": expert_exp, "beginner": beginner_exp}

    async def synthesize_async(
        self,
        ticker: str,
        quant_result: Dict[str, Any],
        rag_result: Dict[str, Any],
        behavioral_result: Dict[str, Any],
        debate_result: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Asynchronously synthesizes signals with non-blocking LLM explanation generation."""
        meta = self._calculate_action_and_weights(
            ticker, quant_result, rag_result, behavioral_result, debate_result, market_data
        )

        llm_exp = await llm_client.generate_synthesis_explanations_async(
            ticker=ticker,
            final_action=meta["final_action"],
            quant_score=meta["quant_score"],
            rag_score=meta["rag_score"],
            user_risk=meta["user_risk"]
        )

        explain_modes = llm_exp if llm_exp else self._build_algorithmic_explanations(ticker, meta)

        return {
            "final_action": meta["final_action"],
            "headline": meta["headline"],
            "weight_breakdown": meta["weight_breakdown"],
            "macro_regime": meta["macro_regime"],
            "asset_conviction_score": meta.get("asset_conviction_score"),
            "explain_modes": explain_modes
        }

    def synthesize(
        self,
        ticker: str,
        quant_result: Dict[str, Any],
        rag_result: Dict[str, Any],
        behavioral_result: Dict[str, Any],
        debate_result: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synchronously synthesizes signals for legacy or test callers."""
        meta = self._calculate_action_and_weights(
            ticker, quant_result, rag_result, behavioral_result, debate_result, market_data
        )

        llm_exp = llm_client.generate_synthesis_explanations(
            ticker=ticker,
            final_action=meta["final_action"],
            quant_score=meta["quant_score"],
            rag_score=meta["rag_score"],
            user_risk=meta["user_risk"]
        )

        explain_modes = llm_exp if llm_exp else self._build_algorithmic_explanations(ticker, meta)

        return {
            "final_action": meta["final_action"],
            "headline": meta["headline"],
            "weight_breakdown": meta["weight_breakdown"],
            "macro_regime": meta["macro_regime"],
            "asset_conviction_score": meta.get("asset_conviction_score"),
            "explain_modes": explain_modes
        }


synthesis_agent = SynthesisAgent()
