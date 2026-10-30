import time
import re
import asyncio
from typing import Dict, Any, List, Optional

from backend.rag.retriever import rag_retriever
from backend.agents.llm_client import llm_client


class RAGAgent:
    """
    Fundamental Researcher RAG Agent.
    Retrieves vector citations from corporate filings and SEBI/SEC earnings call transcripts.
    Dynamically extracts scores, stance, and grounded findings via LLM synthesis
    or deterministic evidence weighting without hardcoded profile dictionaries.
    """

    def analyze(self, ticker: str, simulated_rag_timeout: bool = False) -> Dict[str, Any]:
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
                "citations": []
            }

        # 1. Search Vector Knowledge Base for filings
        search_query = f"{ticker_up} revenue operating margins debt capex cash flow guidance risks order book"
        search_res = rag_retriever.search(ticker=ticker_up, query=search_query, top_k=3)
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
                "citations": []
            }

        # 2. Attempt LLM-driven evidence extraction if Gemini is active
        llm_analysis = llm_client.extract_fundamental_evidence(ticker=ticker_up, citations=citations)

        if llm_analysis:
            score = llm_analysis["score"]
            stance = llm_analysis["stance"]
            key_findings = llm_analysis["key_findings"]
        else:
            # 3. Deterministic Evidence Extraction Engine (Offline Fallback)
            score, stance, key_findings = self._extract_deterministic_evidence(ticker_up, citations)

        elapsed_ms = max(int((time.perf_counter() - start_time) * 1000) + search_res.get("retrieval_ms", 1), 1)

        # Format citations to adhere strictly to API_CONTRACTS
        formatted_citations = []
        for c in citations:
            formatted_citations.append({
                "id": c["id"],
                "document_title": c["document_title"],
                "source_type": c["source_type"],
                "section": c["section"],
                "excerpt": c["excerpt"],
                "relevance_score": c["relevance_score"]
            })

        return {
            "name": "Fundamental Researcher",
            "stance": stance,
            "score": score,
            "latency_ms": elapsed_ms,
            "timed_out": False,
            "key_findings": key_findings,
            "citations": formatted_citations
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
                "citations": []
            }

        # 1. Search Vector Knowledge Base non-blockingly via worker thread
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
                "citations": []
            }

        # 2. Asynchronous non-blocking LLM-driven evidence extraction
        llm_analysis = await llm_client.extract_fundamental_evidence_async(ticker=ticker_up, citations=citations)

        if llm_analysis:
            score = llm_analysis["score"]
            stance = llm_analysis["stance"]
            key_findings = llm_analysis["key_findings"]
        else:
            # 3. Deterministic Evidence Extraction Engine (Offline Fallback)
            score, stance, key_findings = self._extract_deterministic_evidence(ticker_up, citations)

        elapsed_ms = max(int((time.perf_counter() - start_time) * 1000) + search_res.get("retrieval_ms", 1), 1)

        # Format citations
        formatted_citations = []
        for c in citations:
            formatted_citations.append({
                "id": c["id"],
                "document_title": c["document_title"],
                "source_type": c["source_type"],
                "section": c["section"],
                "excerpt": c["excerpt"],
                "relevance_score": c["relevance_score"]
            })

        return {
            "name": "Fundamental Researcher",
            "stance": stance,
            "score": score,
            "latency_ms": elapsed_ms,
            "timed_out": False,
            "key_findings": key_findings,
            "citations": formatted_citations
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
