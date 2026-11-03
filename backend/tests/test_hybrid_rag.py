import os
import sys
import math

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.rag.bm25 import (
    BM25Okapi,
    tokenize_financial_text,
    ReciprocalRankFusion,
    compute_convex_hybrid_score
)
from backend.rag.vector_store import vector_store
from backend.rag.retriever import rag_retriever
from backend.agents.rag_agent import rag_agent


def test_bm25_tokenization_and_scoring():
    """Verifies that financial tokenizer preserves acronyms, compounds, and percentages."""
    text = "Net Interest Margin (NIM) stabilized at 3.45% post-merger integration. Credit-to-deposit ratio improved."
    tokens = tokenize_financial_text(text)
    
    assert "nim" in tokens
    assert "3.45%" in tokens
    assert "credit-to-deposit" in tokens
    assert "credit" in tokens
    assert "deposit" in tokens
    assert "the" not in tokens
    assert "at" not in tokens

    # Test scoring with miniature corpus
    corpus = [
        ["net", "interest", "margin", "nim", "stabilized", "credit-to-deposit"],
        ["gross", "non-performing", "assets", "gnpa", "provisions", "credit", "quality"],
        ["operating", "expenses", "opex", "cost-to-income", "headwinds"]
    ]
    bm25 = BM25Okapi(corpus, k1=1.5, b=0.75)
    
    # Query matching doc 0
    scores_0 = bm25.get_scores(["nim", "margin"])
    assert scores_0[0] > scores_0[1]
    assert scores_0[0] > scores_0[2]

    # Query matching doc 1
    scores_1 = bm25.get_scores(["gnpa", "assets"])
    assert scores_1[1] > scores_1[0]
    assert scores_1[1] > scores_1[2]


def test_reciprocal_rank_fusion():
    """Verifies RRF mathematically combines discordant rank orders."""
    # Candidates 0, 1, 2
    # BM25 order: 0 > 1 > 2
    # Dense order: 1 > 0 > 2
    bm25_ranks = [0, 1, 2]
    dense_ranks = [1, 0, 2]

    fused = ReciprocalRankFusion.fuse(bm25_ranks, dense_ranks, k_rrf=60)
    fused_dict = dict(fused)

    # Candidate 0: 1/(60+1) + 1/(60+2) = 1/61 + 1/62 = 0.016393 + 0.016129 = 0.032522
    # Candidate 1: 1/(60+2) + 1/(60+1) = 0.032522
    # Candidate 2: 1/(60+3) + 1/(60+3) = 2/63 = 0.031746
    assert abs(fused_dict[0] - fused_dict[1]) < 1e-5
    assert fused_dict[0] > fused_dict[2]

    # Convex hybrid score
    h_score = compute_convex_hybrid_score(bm25_score=2.5, dense_score=0.8, max_bm25_in_batch=5.0, alpha=0.5)
    # norm_bm25 = 0.5, norm_dense = 0.8 -> 0.5 * 0.5 + 0.5 * 0.8 = 0.65
    assert abs(h_score - 0.65) < 1e-3


def test_exact_financial_term_retrieval():
    """Verifies that BM25 retrieves exact financial jargon (GNPA) ahead of general documents."""
    res = vector_store.search_hybrid(
        ticker="HDFCBANK",
        query="Gross Non-Performing Assets GNPA provisions",
        top_k=3,
        mode="hybrid"
    )
    assert res["status"] == "SUCCESS"
    citations = res["citations"]
    assert len(citations) >= 1

    top_cite = citations[0]
    # The GNPA document should be ranked #1
    assert "gnpa" in top_cite["keywords"] or "GNPA" in top_cite["excerpt"]
    assert top_cite["bm25_score"] > 0
    assert top_cite["retrieval_method"] == "HYBRID_BM25_DENSE"
    assert "rank_bm25" in top_cite
    assert "rank_dense" in top_cite
    assert "rrf_score" in top_cite


def test_point_in_time_hybrid_isolation():
    """Verifies strict as_of_date boundary enforcement in hybrid search."""
    # HDFCBANK filings are dated 2026-01-18.
    # Searching as of 2025-12-31 must return zero citations
    res_past = vector_store.search_hybrid(
        ticker="HDFCBANK",
        query="NIM margin deposits",
        as_of_date="2025-12-31"
    )
    assert res_past["status"] == "NO_POINT_IN_TIME_FILINGS"
    assert len(res_past["citations"]) == 0

    # Searching as of 2026-02-01 must retrieve valid citations
    res_future = vector_store.search_hybrid(
        ticker="HDFCBANK",
        query="NIM margin deposits",
        as_of_date="2026-02-01"
    )
    assert res_future["status"] == "SUCCESS"
    assert len(res_future["citations"]) >= 1


def test_retrieval_modes_comparison():
    """Verifies that mode switching between bm25, dense, and hybrid works seamlessly."""
    res_bm25 = vector_store.search_hybrid(ticker="HDFCBANK", query="credit-to-deposit NIM", mode="bm25")
    res_dense = vector_store.search_hybrid(ticker="HDFCBANK", query="credit-to-deposit NIM", mode="dense")
    res_hybrid = vector_store.search_hybrid(ticker="HDFCBANK", query="credit-to-deposit NIM", mode="hybrid")

    assert res_bm25["status"] == "SUCCESS"
    assert res_dense["status"] == "SUCCESS"
    assert res_hybrid["status"] == "SUCCESS"

    # All citations must contain complete diagnostic scoring breakdown
    for cite in res_hybrid["citations"]:
        assert 0.50 <= cite["relevance_score"] <= 0.98
        assert "similarity_cosine" in cite
        assert "bm25_score" in cite
        assert "rrf_score" in cite
        assert cite["retrieval_method"] == "HYBRID_BM25_DENSE"


def test_rag_agent_hybrid_provenance():
    """Verifies that RAGAgent analyze reflects hybrid retrieval and provenance."""
    analysis = rag_agent.analyze("HDFCBANK")
    assert analysis["timed_out"] is False
    assert len(analysis["citations"]) >= 1
    assert analysis["provenance"]["method"] == "hybrid_bm25_dense_rrf"
    assert analysis["citations"][0]["retrieval_method"] == "HYBRID_BM25_DENSE"


if __name__ == "__main__":
    test_bm25_tokenization_and_scoring()
    test_reciprocal_rank_fusion()
    test_exact_financial_term_retrieval()
    test_point_in_time_hybrid_isolation()
    test_retrieval_modes_comparison()
    test_rag_agent_hybrid_provenance()
    print("All Hybrid Search unit tests passed successfully!")
