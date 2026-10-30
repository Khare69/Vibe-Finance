import os
import sys
import asyncio

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.rag.retriever import rag_retriever
from backend.agents.rag_agent import rag_agent


def test_vector_citations_schema():
    print("\n--- 1. Testing RAG Vector Store Citations Metadata Schema ---")
    results = rag_retriever.search("RELIANCE", query="debt capex headwinds margins", top_k=3)
    citations = results["citations"]
    assert len(citations) >= 1, "Expected at least 1 citation for RELIANCE"

    required_fields = [
        "id", "ticker", "document_title", "source_type", "section",
        "excerpt", "full_context", "relevance_score", "sentiment",
        "fiscal_period", "filing_date", "page_number"
    ]

    for cite in citations:
        print(f"  [CITATION] {cite['document_title']} | Section: {cite['section']} | {cite['fiscal_period']} | Page {cite['page_number']}")
        for f in required_fields:
            assert f in cite, f"Missing required citation field: {f}"
        assert cite["ticker"] == "RELIANCE"
        assert 0.50 <= cite["relevance_score"] <= 1.0
        assert cite["sentiment"] in ["positive", "negative", "neutral"]
        assert cite["page_number"] >= 1
        assert len(cite["excerpt"]) > 10

    print("[PASSED] Citations metadata schema validated.")


def test_rag_agent_citations_integration():
    print("\n--- 2. Testing Fundamental RAG Agent Citations Integration ---")
    res = rag_agent.analyze("NVDA")
    assert res["stance"] in ["BULLISH", "BEARISH", "NEUTRAL"]
    assert "citations" in res
    assert len(res["citations"]) >= 1

    top_cite = res["citations"][0]
    assert top_cite["ticker"] == "NVDA"
    assert "fiscal_period" in top_cite
    assert "filing_date" in top_cite
    assert "page_number" in top_cite
    print(f"  NVDA Top Citation: {top_cite['document_title']} (Relevance: {top_cite['relevance_score']})")
    print("[PASSED] RAG Agent Citations Integration validated.")


def main():
    print("=== Testing Sub-phase 5.2: Evidence Explorer UI & Citation Metadata ===")
    test_vector_citations_schema()
    test_rag_agent_citations_integration()
    print("\n[SUCCESS] Sub-phase 5.2 Evidence Explorer verified with 100% accuracy!")


if __name__ == "__main__":
    main()
