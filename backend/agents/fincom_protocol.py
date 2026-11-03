"""
FinCom Disagree-or-Commit Protocol & Behavioral Risk Hard Veto System.
Implements institutional governance for multi-agent financial consensus:
1. Formal divergence measurement between quantitative technicals and fundamental RAG disclosures.
2. Structured dissension tracking with verifiable risk-threshold conditions.
3. Dynamic Behavioral Risk Hard Veto enforcing single-position allocation caps.
4. Mathematically calibrated confidence decay based on cross-agent divergence.
5. Formal Safe Abstention ('ABSTAIN' / 'INCONCLUSIVE_DEBATE') when evidence is irreconcilably contradictory.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class StructuredDissension(BaseModel):
    """Formal audit record of an agent's dissension during committee debate."""
    dissenting_agent: str
    opposing_agent: str
    divergence_score: float
    dissent_rationale: str
    risk_threshold_condition: str
    veto_triggered: bool = False


class RiskVetoResult(BaseModel):
    """Enforces behavioral risk bounds, overriding actions and capping allocation."""
    veto_applied: bool = False
    rule_name: Optional[str] = None
    original_action: Optional[str] = None
    override_action: Optional[str] = None
    max_position_cap_pct: Optional[float] = None
    rationale: Optional[str] = None


class FinComEvaluation(BaseModel):
    """Comprehensive evaluation payload produced by the FinCom protocol."""
    divergence_score: float
    has_disagreement: bool
    dissensions: List[StructuredDissension] = Field(default_factory=list)
    calibrated_confidence: int
    confidence_penalties: Dict[str, float] = Field(default_factory=dict)
    risk_veto: RiskVetoResult = Field(default_factory=RiskVetoResult)
    safe_abstention: bool = False
    abstention_rationale: Optional[str] = None
    recommended_action: Optional[str] = None


class FinComProtocol:
    """
    Financial Committee Protocol Engine.
    Ensures that agent conflicts are resolved via disciplined institutional rules,
    eliminating synthetic confidence inflation and enforcing capital preservation.
    """

    DIVERGENCE_DISSENSION_THRESHOLD = 25.0
    DIVERGENCE_ABSTENTION_THRESHOLD = 40.0
    BASE_CONFIDENCE = 85.0

    @classmethod
    def calculate_divergence(cls, quant_score: float, rag_score: float) -> float:
        """Computes the absolute divergence between quantitative and fundamental signals."""
        return round(abs(float(quant_score) - float(rag_score)), 2)

    @classmethod
    def calibrate_confidence(
        cls,
        divergence: float,
        rag_timed_out: bool = False,
        stale_data: bool = False,
        rebuttal_converged: bool = False,
        rebuttal_cycle: int = 0
    ) -> Dict[str, Any]:
        """
        Calibrates confidence mathematically.
        Divergence degrades confidence monotonically; circuit-breaker timeouts
        and stale data impose explicit penalties.
        """
        penalties: Dict[str, float] = {}

        # Divergence penalty: 0.8 points per point of divergence above 10
        if divergence > 10.0:
            div_penalty = round((divergence - 10.0) * 0.8, 1)
            penalties["divergence_penalty"] = min(45.0, div_penalty)
        else:
            penalties["divergence_penalty"] = 0.0

        if rag_timed_out:
            penalties["rag_timeout_penalty"] = 25.0

        if stale_data:
            penalties["stale_feed_penalty"] = 20.0

        # Positive adjustment ONLY if cross-examination successfully converged opposing arguments
        rebuttal_adjustment = 0.0
        if rebuttal_converged and rebuttal_cycle > 0 and not rag_timed_out:
            # Rebuttal resolution offers a modest bonus for structured consensus
            rebuttal_adjustment = min(8.0, rebuttal_cycle * 3.0)

        total_penalty = sum(v for k, v in penalties.items() if "penalty" in k)
        raw_score = cls.BASE_CONFIDENCE - total_penalty + rebuttal_adjustment
        final_confidence = int(round(max(20.0, min(95.0, raw_score))))

        return {
            "score": final_confidence,
            "penalties": penalties,
            "rebuttal_adjustment": rebuttal_adjustment,
            "base_confidence": cls.BASE_CONFIDENCE
        }

    @classmethod
    def evaluate_behavioral_risk_veto(
        cls,
        proposed_action: str,
        user_profile: Dict[str, Any],
        market_data: Dict[str, Any],
        behavioral_result: Dict[str, Any]
    ) -> RiskVetoResult:
        """
        Evaluates dynamic behavioral constraints and triggers hard vetoes when
        volatility or drawdown risks exceed the investor's risk mandate.
        """
        risk_level = user_profile.get("risk_level", "moderate").lower()
        panic_tendency = float(user_profile.get("panic_tendency", 0.4))
        weekly_var = float(behavioral_result.get("weekly_95_var", 0.0))
        annual_vol = float(behavioral_result.get("annualized_volatility", 25.0))

        # Check conservative constraints
        if risk_level == "conservative":
            if weekly_var > 8.0 or annual_vol > 35.0:
                if proposed_action in ["STRONG_BUY", "BUY"]:
                    return RiskVetoResult(
                        veto_applied=True,
                        rule_name="CONSERVATIVE_DRAWDOWN_HARD_VETO",
                        original_action=proposed_action,
                        override_action="CAUTIOUS_ACCUMULATE",
                        max_position_cap_pct=5.0,
                        rationale=(
                            f"Conservative risk mandate exceeded: Asset 1-week 95% VaR ({weekly_var}%) "
                            f"and annual volatility ({annual_vol}%) breach the 8.0% weekly threshold. "
                            f"Overriding {proposed_action} to CAUTIOUS_ACCUMULATE with a 5% allocation ceiling."
                        )
                    )

        # Check moderate constraints
        elif risk_level == "moderate":
            if weekly_var > 14.0 or annual_vol > 45.0:
                if proposed_action == "STRONG_BUY":
                    return RiskVetoResult(
                        veto_applied=True,
                        rule_name="MODERATE_VOLATILITY_CAP_VETO",
                        original_action="STRONG_BUY",
                        override_action="BUY",
                        max_position_cap_pct=10.0,
                        rationale=(
                            f"Moderate risk mandate constraint: Volatility profile ({annual_vol}% annual, "
                            f"{weekly_var}% weekly VaR) requires position cap at 10.0% of portfolio."
                        )
                    )

        # High retail panic sensitivity hard veto
        if panic_tendency >= 0.65 and proposed_action in ["STRONG_BUY", "BUY"] and weekly_var > 10.0:
            return RiskVetoResult(
                veto_applied=True,
                rule_name="PANIC_SENSITIVITY_STAGGERED_VETO",
                original_action=proposed_action,
                override_action="CAUTIOUS_ACCUMULATE",
                max_position_cap_pct=6.0,
                rationale=(
                    f"Elevated retail panic sensitivity ({int(panic_tendency * 100)}%) detected alongside "
                    f"elevated weekly VaR ({weekly_var}%). Forcing staggered limit-order accumulation."
                )
            )

        return RiskVetoResult(veto_applied=False)

    @classmethod
    def evaluate_committee(
        cls,
        quant_result: Dict[str, Any],
        rag_result: Dict[str, Any],
        behavioral_result: Dict[str, Any],
        market_data: Dict[str, Any],
        user_profile: Dict[str, Any],
        proposed_action: str = "HOLD",
        rebuttal_cycle: int = 0,
        rebuttal_converged: bool = False,
        stale_data: bool = False
    ) -> FinComEvaluation:
        """
        Executes complete FinCom protocol evaluation across all agents.
        Returns formal dissensions, calibrated confidence, risk veto, and abstention flags.
        """
        quant_score = float(quant_result.get("score", 50.0))
        rag_score = float(rag_result.get("score", 50.0))
        quant_stance = quant_result.get("stance", "NEUTRAL")
        rag_stance = rag_result.get("stance", "NEUTRAL")
        rag_timed_out = rag_result.get("timed_out", False)

        divergence = cls.calculate_divergence(quant_score, rag_score)
        has_disagreement = divergence >= cls.DIVERGENCE_DISSENSION_THRESHOLD or (
            quant_stance in ["BULLISH", "BEARISH"] and rag_stance in ["BULLISH", "BEARISH"] and quant_stance != rag_stance
        )

        dissensions: List[StructuredDissension] = []
        if has_disagreement and not rag_timed_out:
            if quant_score > rag_score:
                dissensions.append(
                    StructuredDissension(
                        dissenting_agent="Fundamental Researcher",
                        opposing_agent="Quantitative Analyst",
                        divergence_score=divergence,
                        dissent_rationale=(
                            f"Fundamental RAG flags valuation/operational risks (score: {rag_score}/100) "
                            f"countering quantitative momentum exuberance (score: {quant_score}/100)."
                        ),
                        risk_threshold_condition=f"Divergence {divergence} >= {cls.DIVERGENCE_DISSENSION_THRESHOLD}",
                        veto_triggered=divergence >= cls.DIVERGENCE_ABSTENTION_THRESHOLD
                    )
                )
            else:
                dissensions.append(
                    StructuredDissension(
                        dissenting_agent="Quantitative Analyst",
                        opposing_agent="Fundamental Researcher",
                        divergence_score=divergence,
                        dissent_rationale=(
                            f"Quantitative indicators signal momentum breakdown/divergence (score: {quant_score}/100) "
                            f"countering fundamental narrative optimism (score: {rag_score}/100)."
                        ),
                        risk_threshold_condition=f"Divergence {divergence} >= {cls.DIVERGENCE_DISSENSION_THRESHOLD}",
                        veto_triggered=divergence >= cls.DIVERGENCE_ABSTENTION_THRESHOLD
                    )
                )

        # Calibrated confidence calculation
        conf_data = cls.calibrate_confidence(
            divergence=divergence,
            rag_timed_out=rag_timed_out,
            stale_data=stale_data,
            rebuttal_converged=rebuttal_converged,
            rebuttal_cycle=rebuttal_cycle
        )

        # Safe Abstention logic
        safe_abstention = False
        abstention_rationale = None
        recommended_action = proposed_action

        # Trigger safe abstention if divergence is severe (>= 40) with polar opposing stances
        polar_conflict = (quant_stance == "BULLISH" and rag_stance == "BEARISH") or (quant_stance == "BEARISH" and rag_stance == "BULLISH")
        if not rag_timed_out and divergence >= cls.DIVERGENCE_ABSTENTION_THRESHOLD and polar_conflict:
            safe_abstention = True
            recommended_action = "ABSTAIN"
            abstention_rationale = (
                f"Financial Committee Safe Abstention declared: Severe cross-agent contradiction between "
                f"Quantitative signals ({quant_stance}, score: {quant_score}) and Fundamental filings "
                f"({rag_stance}, score: {rag_score}). Signal divergence ({divergence}) exceeds the institutional "
                f"safety limit ({cls.DIVERGENCE_ABSTENTION_THRESHOLD}). Safe abstention enforced until catalyst resolution."
            )

        # Behavioral Risk Hard Veto check
        veto_result = cls.evaluate_behavioral_risk_veto(
            proposed_action=recommended_action,
            user_profile=user_profile,
            market_data=market_data,
            behavioral_result=behavioral_result
        )

        if veto_result.veto_applied and not safe_abstention:
            recommended_action = veto_result.override_action

        return FinComEvaluation(
            divergence_score=divergence,
            has_disagreement=has_disagreement,
            dissensions=dissensions,
            calibrated_confidence=conf_data["score"],
            confidence_penalties=conf_data["penalties"],
            risk_veto=veto_result,
            safe_abstention=safe_abstention,
            abstention_rationale=abstention_rationale,
            recommended_action=recommended_action
        )


fincom_protocol = FinComProtocol()
