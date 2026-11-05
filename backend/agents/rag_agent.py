import time
import asyncio
from typing import Dict, Any, List

from backend.rag.retriever import rag_retriever
from backend.agents.llm_client import llm_client


class RAGAgent:
    """
    Fundamental Researcher Agent.
    Retrieves evidence from indexed corporate regulatory filings (SEC 10-K, 10-Q,
    SEBI disclosures, earnings transcripts) using Hybrid Retrieval (BM25 lexical
    + Dense Vector RRF) and extracts grounded financial findings using the Gemini
    LLM client with a deterministic financial lexicon fallback.
    """

    @staticmethod
    def _format_citation_items(citations: List[Dict[str, Any]], ticker_up: str) -> List[Dict[str, Any]]:
        """Encapsulates citation normalization for Evidence Explorer and audit logs."""
        formatted = []
        for c in citations:
            formatted.append({
                "id": c.get("id", ""),
                "ticker": c.get("ticker", ticker_up),
                "document_title": c.get("document_title", "Corporate Filing"),
                "source_type": c.get("source_type", "REGULATORY_FILING"),
                "section": c.get("section", "General Section"),
                "excerpt": c.get("excerpt", ""),
                "full_context": c.get("full_context") or c.get("excerpt", ""),
                "structured_table": c.get("structured_table"),
                "relevance_score": c.get("relevance_score", 0.85),
                "similarity_cosine": c.get("similarity_cosine", 0.80),
                "bm25_score": c.get("bm25_score", 0.0),
                "hybrid_score": c.get("hybrid_score", c.get("relevance_score", 0.85)),
                "rrf_score": c.get("rrf_score", 0.0),
                "retrieval_method": c.get("retrieval_method", "HYBRID_BM25_DENSE"),
                "rank_bm25": c.get("rank_bm25", 1),
                "rank_dense": c.get("rank_dense", 1),
                "sentiment": c.get("sentiment", "neutral"),
                "fiscal_period": c.get("fiscal_period", "Q3 FY26"),
                "filing_date": c.get("filing_date", "2026-01-19"),
                "page_number": c.get("page_number", 1),
                "keywords": c.get("keywords", [])
            })
        return formatted

    def analyze(self, ticker: str, simulated_rag_timeout: bool = False) -> Dict[str, Any]:
        """
        Synchronous interface for fundamental analysis.
        Retrieves top hybrid citations and performs deterministic extraction.
        """
        start_time = time.perf_counter()
        ticker_up = ticker.upper()

        if simulated_rag_timeout:
            return {
                "name": "Fundamental Researcher",
                "stance": "NEUTRAL",
                "score": 50,
                "latency_ms": 5000,
                "timed_out": True,
                "key_findings": [
                    "Fundamental RAG retrieval timed out after 5000ms threshold; fundamental analysis pending.",
                    "Proceeding with technical momentum and risk constraints only."
                ],
                "citations": [],
                "provenance": {
                    "source": "CIRCUIT_BREAKER_TIMEOUT",
                    "corpus_citations": 0,
                    "method": "circuit_breaker_abstention"
                }
            }

        # Search Vector Knowledge Base synchronously via Hybrid Retrieval
        search_query = f"{ticker_up} revenue operating margins debt capex cash flow guidance risks order book"
        search_res = rag_retriever.search(ticker=ticker_up, query=search_query, top_k=3)
        citations = search_res.get("citations", [])

        if not citations:
            elapsed_ms = max(int((time.perf_counter() - start_time) * 1000) + search_res.get("retrieval_ms", 1), 1)
            return {
                "name": "Fundamental Researcher",
                "stance": "NEUTRAL",
                "score": 50,
                "latency_ms": elapsed_ms,
                "timed_out": False,
                "key_findings": [
                    f"No regulatory filings or earnings transcripts currently indexed for {ticker_up}.",
                    "Fundamental score defaulted to neutral baseline pending corporate filing upload.",
                    "Upload 10-K/10-Q or earnings transcripts via the Ingestion panel to enable grounded research."
                ],
                "citations": [],
                "provenance": {
                    "source": "UNINDEXED_TICKER_BASELINE",
                    "corpus_citations": 0,
                    "method": "neutral_fallback"
                }
            }

        # Deterministic extraction for synchronous calls
        score, stance, key_findings = self._extract_deterministic_evidence(ticker_up, citations)
        elapsed_ms = max(int((time.perf_counter() - start_time) * 1000) + search_res.get("retrieval_ms", 1), 1)

        formatted_citations = self._format_citation_items(citations, ticker_up)

        return {
            "name": "Fundamental Researcher",
            "stance": stance,
            "score": score,
            "latency_ms": elapsed_ms,
            "timed_out": False,
            "key_findings": key_findings,
            "citations": formatted_citations,
            "provenance": {
                "source": "VECTOR_STORE_FILINGS",
                "corpus_citations": len(formatted_citations),
                "method": "hybrid_bm25_dense_rrf"
            }
        }

    async def analyze_async(self, ticker: str, simulated_rag_timeout: bool = False) -> Dict[str, Any]:
        """
        Asynchronously retrieves vector citations and extracts fundamental evidence
        via non-blocking LLM networking and worker threads.
        """
        start_time = time.perf_counter()
        ticker_up = ticker.upper()

        if simulated_rag_timeout:
            return {
                "name": "Fundamental Researcher",
                "stance": "NEUTRAL",
                "score": 50,
                "latency_ms": 5000,
                "timed_out": True,
                "key_findings": [
                    "Fundamental RAG retrieval timed out after 5000ms threshold; fundamental analysis pending.",
                    "Proceeding with technical momentum and risk constraints only."
                ],
                "citations": [],
                "provenance": {
                    "source": "CIRCUIT_BREAKER_TIMEOUT",
                    "corpus_citations": 0,
                    "method": "circuit_breaker_abstention"
                }
            }

        # 1. Search Vector Knowledge Base non-blockingly via worker thread (Hybrid Retrieval)
        search_query = f"{ticker_up} revenue operating margins debt capex cash flow guidance risks order book"
        search_res = await asyncio.to_thread(rag_retriever.search, ticker=ticker_up, query=search_query, top_k=3)
        citations = search_res.get("citations", [])

        # If ticker is uncataloged and has no documents
        if not citations:
            elapsed_ms = max(int((time.perf_counter() - start_time) * 1000) + search_res.get("retrieval_ms", 1), 1)
            return {
                "name": "Fundamental Researcher",
                "stance": "NEUTRAL",
                "score": 50,
                "latency_ms": elapsed_ms,
                "timed_out": False,
                "key_findings": [
                    f"No regulatory filings or earnings transcripts currently indexed for {ticker_up}.",
                    "Fundamental score defaulted to neutral baseline pending corporate filing upload.",
                    "Upload 10-K/10-Q or earnings transcripts via the Ingestion panel to enable grounded research."
                ],
                "citations": [],
                "provenance": {
                    "source": "UNINDEXED_TICKER_BASELINE",
                    "corpus_citations": 0,
                    "method": "neutral_fallback"
                }
            }

        # 2. Asynchronous non-blocking LLM-driven evidence extraction
        llm_analysis = await llm_client.extract_fundamental_evidence_async(ticker=ticker_up, citations=citations)

        if llm_analysis:
            score = llm_analysis["score"]
            stance = llm_analysis["stance"]
            key_findings = llm_analysis["key_findings"]
            extraction_method = "llm_with_hybrid_bm25_dense"
        else:
            # 3. Deterministic Evidence Extraction Engine (Offline Fallback)
            score, stance, key_findings = self._extract_deterministic_evidence(ticker_up, citations)
            extraction_method = "hybrid_bm25_dense_rrf"

        elapsed_ms = max(int((time.perf_counter() - start_time) * 1000) + search_res.get("retrieval_ms", 1), 1)
        formatted_citations = self._format_citation_items(citations, ticker_up)

        return {
            "name": "Fundamental Researcher",
            "stance": stance,
            "score": score,
            "latency_ms": elapsed_ms,
            "timed_out": False,
            "key_findings": key_findings,
            "citations": formatted_citations,
            "provenance": {
                "source": "VECTOR_STORE_FILINGS",
                "corpus_citations": len(formatted_citations),
                "method": extraction_method
            }
        }

    def _extract_deterministic_evidence(
        self,
        ticker: str,
        citations: List[Dict[str, Any]]
    ) -> (int, str, List[str]):
        """
        Derives fundamental score and key findings directly from citation excerpts
        when the external LLM is offline.
        """
        base_score = 50.0
        findings = []

        pos_terms = [
            "growth", "record", "expansion", "profit", "surpassed", "surpassing",
            "strong", "cash", "dividend", "revival", "rose", "climbing", "climb",
            "robust", "increase", "operating income", "accelerated", "healthy"
        ]
        neg_terms = [
            "debt", "contraction", "headwind", "headwinds", "decline", "pressure",
            "drop", "cut", "drain", "loss", "fell", "decrease", "compress", "compression"
        ]

        for c in citations:
            excerpt = c.get("excerpt", "")
            section = c.get("section", "Filing")
            doc_title = c.get("document_title", "Disclosure")
            relevance = c.get("relevance_score", 0.8)
            sentiment = c.get("sentiment", "neutral")

            lower = excerpt.lower()
            pos_hits = sum(1 for term in pos_terms if term in lower)
            neg_hits = sum(1 for term in neg_terms if term in lower)

            if sentiment == "positive" or pos_hits > neg_hits:
                delta = 16.0 * relevance + (pos_hits * 3.5)
                base_score += delta
            elif sentiment == "negative" or neg_hits > pos_hits:
                delta = 16.0 * relevance + (neg_hits * 3.5)
                base_score -= delta

            # Formulate grounded finding directly from document excerpt
            short_excerpt = excerpt[:140] + "..." if len(excerpt) > 140 else excerpt
            findings.append(f"{doc_title} ({section}): \"{short_excerpt}\"")

        final_score = int(max(15, min(95, round(base_score))))

        if final_score >= 60:
            stance = "BULLISH"
        elif final_score <= 42:
            stance = "BEARISH"
        else:
            stance = "NEUTRAL"

        return final_score, stance, findings[:3]


rag_agent = RAGAgent()
