from typing import Dict, Any, List

from backend.agents.llm_client import llm_client


class DebateEngine:
    """
    Synthesizes and arbitrates debates between the Quantitative Agent, Fundamental RAG Agent,
    and Behavioral Risk Manager. Calibrates overall confidence score based on consensus vs conflict.
    Features hybrid LLM support with dynamic algorithmic templates and non-blocking async execution.
    """

    def _assess_conflict(
        self,
        ticker: str,
        quant_result: Dict[str, Any],
        rag_result: Dict[str, Any],
        behavioral_result: Dict[str, Any],
        stale_data: bool
    ) -> Dict[str, Any]:
        quant_stance = quant_result.get("stance", "NEUTRAL")
        quant_score = quant_result.get("score", 50)
        rag_stance = rag_result.get("stance", "NEUTRAL")
        rag_score = rag_result.get("score", 50)
        rag_timed_out = rag_result.get("timed_out", False)
        user_profile_name = behavioral_result.get("user_risk_profile", "moderate")

        has_disagreement = False
        conflict_msg = "Agents are in general alignment on market signals."

        if not rag_timed_out and (
            (quant_stance == "BULLISH" and rag_stance == "BEARISH") or
            (quant_stance == "BEARISH" and rag_stance == "BULLISH") or
            abs(quant_score - rag_score) >= 25
        ):
            has_disagreement = True
            if quant_stance == "BULLISH" and rag_stance == "BEARISH":
                conflict_msg = (
                    f"Quant sees technical breakout and strong momentum ({quant_score}/100), "
                    f"while Fundamental RAG flags corporate headwinds and margin pressure ({rag_score}/100)."
                )
            elif quant_stance == "BEARISH" and rag_stance == "BULLISH":
                conflict_msg = (
                    f"Quant warns of negative momentum and technical breakdown ({quant_score}/100), "
                    f"whereas Fundamental RAG highlights solid balance sheet cash flows and earnings beats ({rag_score}/100)."
                )
            else:
                conflict_msg = (
                    f"Moderate variance between quantitative momentum ({quant_score}) "
                    f"and fundamental valuation signals ({rag_score})."
                )

        if rag_timed_out:
            base_confidence = 58
        elif has_disagreement:
            base_confidence = 63
        else:
            base_confidence = 84

        if stale_data:
            base_confidence = max(40, base_confidence - 20)

        # Resolution summary
        if has_disagreement:
            if quant_stance == "BULLISH" and rag_stance == "BEARISH":
                resolution_summary = (
                    f"The technical breakout on {ticker} is tempered by fundamental debt/margin headwinds. For this {user_profile_name} user, "
                    f"technical bullishness is restrained, producing a Cautious Hold / Accumulate on Dips stance."
                )
            else:
                resolution_summary = (
                    f"Disagreement between technical indicators and fundamental filings for {ticker} resolved by prioritizing "
                    f"capital preservation and risk-adjusted positioning for the {user_profile_name} investor."
                )
        else:
            resolution_summary = (
                f"Convergence of technical indicators and fundamental signals supports a coherent "
                f"strategy on {ticker} aligned with the investor's {user_profile_name} risk profile."
            )

        return {
            "has_disagreement": has_disagreement,
            "quant_vs_rag_conflict": conflict_msg,
            "confidence_calibration_score": base_confidence,
            "resolution_summary": resolution_summary,
            "user_profile_name": user_profile_name,
            "quant_stance": quant_stance,
            "rag_stance": rag_stance,
            "rag_timed_out": rag_timed_out
        }

    def _build_algorithmic_dialogue(
        self,
        ticker: str,
        quant_result: Dict[str, Any],
        rag_result: Dict[str, Any],
        assessment: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        dialogue_steps: List[Dict[str, str]] = []
        quant_stance = assessment["quant_stance"]
        rag_stance = assessment["rag_stance"]
        rag_timed_out = assessment["rag_timed_out"]
        user_profile_name = assessment["user_profile_name"]

        # 1. Quant Agent
        if quant_stance == "BULLISH":
            q_text = (
                f"{ticker} has formed a strong momentum pattern above its key moving averages. "
                f"Technical probabilities and volume acceleration favor an upside continuation."
            )
        elif quant_stance == "BEARISH":
            q_text = (
                f"{ticker} exhibits technical exhaustion with bearish momentum divergences and "
                f"downward volume pressure. Downside support is vulnerable."
            )
        else:
            q_text = (
                f"{ticker} is consolidating in a neutral technical range between 50-SMA and 200-SMA. "
                f"No decisive directional breakout is evident yet."
            )
        dialogue_steps.append({"speaker": "Quant Agent", "text": q_text})

        # 2. Fundamental RAG Agent
        findings = rag_result.get("key_findings", [])
        primary_finding = findings[0] if findings else "filing metrics are currently balanced"

        if rag_timed_out:
            r_text = (
                f"Notice: Regulatory filing retrieval for {ticker} timed out. Proceeding strictly on technical data "
                "with an alert for fundamental uncertainty."
            )
        elif rag_stance == "BEARISH":
            r_text = (
                f"Caution: Corporate filing analysis indicates fundamental headwinds for {ticker}: {primary_finding}. "
                "This rally lacks free cash flow support."
            )
        elif rag_stance == "BULLISH":
            r_text = (
                f"Confirmed: Disclosures reflect robust operational health for {ticker}: {primary_finding}. "
                "Balance sheet liquidity provides downside defense."
            )
        else:
            r_text = (
                f"Fundamental metrics for {ticker} are balanced: {primary_finding}. "
                "Near-term guidance is steady without major negative catalysts."
            )
        dialogue_steps.append({"speaker": "Fundamental RAG Agent", "text": r_text})

        # 3. Behavioral Risk Manager
        if user_profile_name == "conservative":
            b_text = (
                f"Given the user's conservative risk profile and panic-selling sensitivity, a volatile false breakout on {ticker} "
                f"could trigger emotional liquidation. I am vetoing the aggressive Buy and capping maximum allocation to 4%."
            )
        elif user_profile_name == "aggressive":
            b_text = (
                f"User possesses high risk tolerance and an aggressive mandate. We can afford volatility exposure on {ticker}, "
                f"but recommend staged entries to manage downside risk."
            )
        else:
            b_text = (
                f"For this moderate investor, we balance upside participation in {ticker} with capital preservation. "
                f"A disciplined accumulate-on-dips strategy is optimal."
            )
        dialogue_steps.append({"speaker": "Behavioral Risk Manager", "text": b_text})

        return dialogue_steps

    async def conduct_debate_async(
        self,
        ticker: str,
        quant_result: Dict[str, Any],
        rag_result: Dict[str, Any],
        behavioral_result: Dict[str, Any],
        stale_data: bool = False
    ) -> Dict[str, Any]:
        """Asynchronous debate arbitration with non-blocking LLM networking."""
        assessment = self._assess_conflict(ticker, quant_result, rag_result, behavioral_result, stale_data)
        user_profile_name = assessment["user_profile_name"]

        # Attempt non-blocking LLM debate dialogue
        llm_dialogue = await llm_client.generate_debate_dialogue_async(
            ticker=ticker,
            quant_result=quant_result,
            rag_result=rag_result,
            behavioral_result=behavioral_result,
            user_risk_profile=user_profile_name
        )

        dialogue_steps = llm_dialogue if llm_dialogue else self._build_algorithmic_dialogue(
            ticker, quant_result, rag_result, assessment
        )

        return {
            "has_disagreement": assessment["has_disagreement"],
            "quant_vs_rag_conflict": assessment["quant_vs_rag_conflict"],
            "confidence_calibration_score": assessment["confidence_calibration_score"],
            "resolution_summary": assessment["resolution_summary"],
            "dialogue_steps": dialogue_steps
        }

    def conduct_debate(
        self,
        ticker: str,
        quant_result: Dict[str, Any],
        rag_result: Dict[str, Any],
        behavioral_result: Dict[str, Any],
        stale_data: bool = False
    ) -> Dict[str, Any]:
        """Synchronous debate arbitration for legacy or unit test callers."""
        assessment = self._assess_conflict(ticker, quant_result, rag_result, behavioral_result, stale_data)
        user_profile_name = assessment["user_profile_name"]

        llm_dialogue = llm_client.generate_debate_dialogue(
            ticker=ticker,
            quant_result=quant_result,
            rag_result=rag_result,
            behavioral_result=behavioral_result,
            user_risk_profile=user_profile_name
        )

        dialogue_steps = llm_dialogue if llm_dialogue else self._build_algorithmic_dialogue(
            ticker, quant_result, rag_result, assessment
        )

        return {
            "has_disagreement": assessment["has_disagreement"],
            "quant_vs_rag_conflict": assessment["quant_vs_rag_conflict"],
            "confidence_calibration_score": assessment["confidence_calibration_score"],
            "resolution_summary": assessment["resolution_summary"],
            "dialogue_steps": dialogue_steps
        }


debate_engine = DebateEngine()
