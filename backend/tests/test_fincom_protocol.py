"""
Unit and Property Tests for FinCom Disagree-or-Commit Protocol & FinMAN Formula Sandbox.
Verifies mathematical calibration, AST security isolation, behavioral risk hard vetoes,
and safe abstention logic.
"""

import os
import sys
import math
from contextlib import contextmanager

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.sandbox.formula_evaluator import (
    SafeFormulaEvaluator,
    FormulaSecurityError,
    FormulaEvaluationError,
    evaluate_formula
)
from backend.agents.fincom_protocol import (
    FinComProtocol,
    fincom_protocol,
    RiskVetoResult,
    StructuredDissension
)


@contextmanager
def assert_raises(exc_type, match=None):
    """Zero-dependency context manager matching pytest.raises."""
    try:
        yield
    except exc_type as e:
        if match and match not in str(e):
            raise AssertionError(f"Expected '{match}' in '{str(e)}'")
    except Exception as other_e:
        raise AssertionError(f"Expected {exc_type.__name__}, got {type(other_e).__name__}: {other_e}")
    else:
        raise AssertionError(f"Expected {exc_type.__name__} was not raised")



# ==============================================================================
# 1. FinMAN Formula Sandbox Security & Evaluation Tests
# ==============================================================================

def test_formula_sandbox_valid_arithmetic():
    """Validates standard arithmetic formulas with context variables."""
    ctx = {"rsi": 30.0, "sma_50": 150.0, "sma_200": 140.0}
    res = evaluate_formula("(sma_50 - sma_200) / sma_200 * 100", ctx)
    expected = (150.0 - 140.0) / 140.0 * 100.0
    assert abs(res - expected) < 1e-6

    # Test math builtins
    res_min = evaluate_formula("min(rsi, 50.0)", ctx)
    assert res_min == 30.0

    res_round = evaluate_formula("round(sqrt(rsi), 2)", ctx)
    assert res_round == round(math.sqrt(30.0), 2)


def test_formula_sandbox_comparisons():
    """Validates comparison operators yielding 1.0 (True) or 0.0 (False)."""
    ctx = {"rsi": 25.0}
    assert evaluate_formula("rsi < 30", ctx) == 1.0
    assert evaluate_formula("rsi >= 30", ctx) == 0.0
    assert evaluate_formula("rsi == 25", ctx) == 1.0


def test_formula_sandbox_security_rejection_of_attributes():
    """Ensures arbitrary attribute access is strictly rejected."""
    with assert_raises(FormulaSecurityError):
        SafeFormulaEvaluator("().__class__.__bases__[0]")


def test_formula_sandbox_security_rejection_of_imports():
    """Ensures imports and dunder calls are blocked."""
    with assert_raises(FormulaSecurityError):
        SafeFormulaEvaluator("__import__('os').system('ls')")


def test_formula_sandbox_security_rejection_of_eval():
    """Ensures eval/exec/open are disallowed."""
    with assert_raises(FormulaSecurityError, match="not in the approved safe list"):
        SafeFormulaEvaluator("eval('2 + 2')")


def test_formula_sandbox_power_dos_protection():
    """Ensures exponential power bombs are stopped before execution."""
    with assert_raises(FormulaSecurityError, match="exceeds safe sandbox limit"):
        evaluate_formula("2 ** 500", {})


def test_formula_sandbox_division_by_zero():
    """Ensures division by zero raises FormulaEvaluationError instead of crashing."""
    with assert_raises(FormulaEvaluationError, match="Division by zero"):
        evaluate_formula("100 / 0", {})


def test_formula_sandbox_missing_variable():
    """Ensures undeclared context variables raise FormulaEvaluationError."""
    with assert_raises(FormulaEvaluationError, match="Undefined variable"):
        evaluate_formula("rsi + 10", {"macd": 1.5})


# ==============================================================================
# 2. FinCom Disagree-or-Commit Protocol Tests
# ==============================================================================

def test_fincom_divergence_calculation():
    """Tests divergence delta calculation between Quant and Fundamental RAG."""
    div1 = FinComProtocol.calculate_divergence(85, 45)
    assert div1 == 40.0

    div2 = FinComProtocol.calculate_divergence(55, 55)
    assert div2 == 0.0


def test_fincom_calibrated_confidence_decay():
    """
    Tests that confidence decays monotonically as divergence increases,
    and timeout/stale penalties apply without synthetic inflation.
    """
    # Low divergence: high confidence
    conf_aligned = FinComProtocol.calibrate_confidence(divergence=5.0)
    assert conf_aligned["score"] == 85

    # Moderate divergence (25 points): penalty = (25-10)*0.8 = 12 points -> 73%
    conf_mod = FinComProtocol.calibrate_confidence(divergence=25.0)
    assert conf_mod["score"] == 73

    # High divergence (40 points): penalty = (40-10)*0.8 = 24 points -> 61%
    conf_high = FinComProtocol.calibrate_confidence(divergence=40.0)
    assert conf_high["score"] == 61
    assert conf_high["score"] < conf_mod["score"]

    # Timeout penalty
    conf_timeout = FinComProtocol.calibrate_confidence(divergence=5.0, rag_timed_out=True)
    assert conf_timeout["score"] == 60  # 85 - 25

    # Stale data penalty
    conf_stale = FinComProtocol.calibrate_confidence(divergence=5.0, stale_data=True)
    assert conf_stale["score"] == 65  # 85 - 20


def test_fincom_dissension_recording():
    """Tests that formal dissensions are filed when divergence >= 25."""
    eval_res = FinComProtocol.evaluate_committee(
        quant_result={"score": 88, "stance": "BULLISH"},
        rag_result={"score": 38, "stance": "BEARISH"},
        behavioral_result={"weekly_95_var": 5.0, "annualized_volatility": 20.0},
        market_data={},
        user_profile={"risk_level": "moderate"},
        proposed_action="BUY"
    )
    assert eval_res.has_disagreement is True
    assert eval_res.divergence_score == 50.0
    assert len(eval_res.dissensions) >= 1
    assert eval_res.dissensions[0].dissenting_agent == "Fundamental Researcher"
    assert "valuation/operational risks" in eval_res.dissensions[0].dissent_rationale


def test_fincom_behavioral_risk_hard_veto_conservative():
    """
    Tests that Conservative investor triggers a hard veto when asset VaR exceeds 8.0%,
    capping position to 5% and downgrading BUY to CAUTIOUS_ACCUMULATE.
    """
    eval_res = FinComProtocol.evaluate_committee(
        quant_result={"score": 75, "stance": "BULLISH"},
        rag_result={"score": 70, "stance": "BULLISH"},
        behavioral_result={"weekly_95_var": 11.2, "annualized_volatility": 48.0},
        market_data={"current_price": 200.0},
        user_profile={"risk_level": "conservative"},
        proposed_action="BUY"
    )
    assert eval_res.risk_veto.veto_applied is True
    assert eval_res.risk_veto.rule_name == "CONSERVATIVE_DRAWDOWN_HARD_VETO"
    assert eval_res.risk_veto.override_action == "CAUTIOUS_ACCUMULATE"
    assert eval_res.risk_veto.max_position_cap_pct == 5.0
    assert eval_res.recommended_action == "CAUTIOUS_ACCUMULATE"


def test_fincom_behavioral_risk_hard_veto_moderate():
    """
    Tests that Moderate investor triggers position cap at 10% on extreme volatility (>45% annual).
    """
    eval_res = FinComProtocol.evaluate_committee(
        quant_result={"score": 85, "stance": "BULLISH"},
        rag_result={"score": 82, "stance": "BULLISH"},
        behavioral_result={"weekly_95_var": 15.5, "annualized_volatility": 52.0},
        market_data={"current_price": 100.0},
        user_profile={"risk_level": "moderate"},
        proposed_action="STRONG_BUY"
    )
    assert eval_res.risk_veto.veto_applied is True
    assert eval_res.risk_veto.rule_name == "MODERATE_VOLATILITY_CAP_VETO"
    assert eval_res.risk_veto.override_action == "BUY"
    assert eval_res.risk_veto.max_position_cap_pct == 10.0


def test_fincom_safe_abstention_on_irreconcilable_divergence():
    """
    Tests that when Quant is strongly BULLISH (score 90) and Fundamental RAG is strongly BEARISH (score 40),
    divergence (50 pts >= 40) triggers Safe Abstention (final_action = 'ABSTAIN').
    """
    eval_res = FinComProtocol.evaluate_committee(
        quant_result={"score": 90, "stance": "BULLISH"},
        rag_result={"score": 40, "stance": "BEARISH"},
        behavioral_result={"weekly_95_var": 6.0, "annualized_volatility": 22.0},
        market_data={},
        user_profile={"risk_level": "moderate"},
        proposed_action="BUY"
    )
    assert eval_res.safe_abstention is True
    assert eval_res.recommended_action == "ABSTAIN"
    assert "Severe cross-agent contradiction" in eval_res.abstention_rationale
    assert eval_res.calibrated_confidence <= 60


if __name__ == "__main__":
    print("Running FinMAN and FinCom Protocol Test Suite...")
    test_formula_sandbox_valid_arithmetic()
    test_formula_sandbox_comparisons()
    test_formula_sandbox_security_rejection_of_attributes()
    test_formula_sandbox_security_rejection_of_imports()
    test_formula_sandbox_security_rejection_of_eval()
    test_formula_sandbox_power_dos_protection()
    test_formula_sandbox_division_by_zero()
    test_formula_sandbox_missing_variable()
    test_fincom_divergence_calculation()
    test_fincom_calibrated_confidence_decay()
    test_fincom_dissension_recording()
    test_fincom_behavioral_risk_hard_veto_conservative()
    test_fincom_behavioral_risk_hard_veto_moderate()
    test_fincom_safe_abstention_on_irreconcilable_divergence()
    print("ALL FINCOM PROTOCOL AND FORMULA SANDBOX TESTS PASSED!")
