import os
import sys
from fastapi.testclient import TestClient

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.main import app
from backend.rag.evaluator import rag_evaluator


def test_numerical_entity_extraction():
    print("\n--- 1. Testing Numerical Entity Extraction for Faithfulness ---")
    sample_text = (
        "Operating cash flow conversion ratio stood at 104% of net profit. "
        "Debt servicing on capex expanded 18% YoY with refining margins stabilized at $9.80/bbl "
        "and retail EBITDA margin contracted by 140 basis points."
    )
    entities = rag_evaluator.extract_numerical_entities(sample_text)
    print(f"  Extracted Entities: {entities}")
    assert any("104%" in e for e in entities)
    assert any("18%" in e for e in entities)
    assert any("140" in e for e in entities)
    assert any("9.80" in e for e in entities)
    print("[PASSED] Numerical entity extraction verified.")


def test_rag_abstention_negative_controls():
    print("\n--- 2. Testing Negative Control Abstention (Anti-Hallucination) ---")
    neg_tickers = ["CUSTOMTECH", "NONEXISTENT_CORP_99"]
    for ticker in neg_tickers:
        res = rag_evaluator.evaluate_abstention(ticker)
        print(f"  Abstention evaluation for {ticker}: Passed={res['passed']}, Citations={res['citations_count']}")
        assert res["passed"] is True, f"Abstention failed for negative control {ticker}"
        assert res["has_zero_citations"] is True
        assert res["is_neutral_score"] is True
        assert res["refusal_reason_logged"] is True
    print("[PASSED] Negative control abstention verified (0 citations, 50 neutral score, refusal notice).")


def test_rag_benchmark_suite():
    print("\n--- 3. Testing RAG Benchmark Evaluation Suite ---")
    bench = rag_evaluator.run_benchmark_suite()
    print(f"  Benchmark Status: {bench['benchmark_status']}")
    print(f"  Average Faithfulness Score: {bench['average_faithfulness']}")
    print(f"  Hallucination Rate: {bench['hallucination_rate']}")
    print(f"  All Negative Controls Abstention Passed: {bench['all_abstentions_passed']}")

    assert bench["benchmark_status"] == "PASSED"
    assert bench["average_faithfulness"] >= 0.90, f"Average faithfulness below 0.90 threshold: {bench['average_faithfulness']}"
    assert bench["hallucination_rate"] <= 0.05, f"Hallucination rate exceeds 0.05 threshold: {bench['hallucination_rate']}"
    assert bench["all_abstentions_passed"] is True
    assert len(bench["cataloged_evaluations"]) == 4
    print("[PASSED] RAG Benchmark Suite passed all faithfulness and precision thresholds.")


def test_api_rag_evaluate_endpoint():
    print("\n--- 4. Testing GET /api/rag/evaluate REST API Endpoint ---")
    with TestClient(app) as client:
        res = client.get("/api/rag/evaluate")
        assert res.status_code == 200
        data = res.json()
        assert data["benchmark_status"] == "PASSED"
        assert "average_faithfulness" in data
        assert "hallucination_rate" in data
        assert "cataloged_evaluations" in data
        print(f"[PASSED] GET /api/rag/evaluate returned HTTP 200 with Faithfulness={data['average_faithfulness']}.")


def main():
    print("=== Testing Sub-phase 6.2: RAG Faithfulness & Citation Evaluation ===")
    test_numerical_entity_extraction()
    test_rag_abstention_negative_controls()
    test_rag_benchmark_suite()
    test_api_rag_evaluate_endpoint()
    print("\n[SUCCESS] Sub-phase 6.2 RAG Faithfulness & Citation Evaluation verified with 100% accuracy!")


if __name__ == "__main__":
    main()
