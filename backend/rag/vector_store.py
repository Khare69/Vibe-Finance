import os
import json
import re
import time
import threading
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    import pymupdf
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

from backend.rag.corpus import RAG_DOCUMENTS, SENTIMENT_TIMELINES
from backend.rag.bm25 import (
    BM25Okapi,
    tokenize_financial_text,
    ReciprocalRankFusion,
    compute_convex_hybrid_score
)
from backend.rag.table_parser import table_parser


# Additional initial regulatory filing records (including HDFCBANK & Structured Financial Tables)
ADDITIONAL_CORPUS: List[Dict[str, Any]] = [
    {
        "id": "hdfc-cite-1",
        "ticker": "HDFCBANK",
        "document_title": "Q3 FY26 Earnings Conference Call Transcript",
        "source_type": "SEBI_TRANSCRIPT",
        "section": "Management Discussion - NIM & Margin Guidance - Page 7",
        "excerpt": "Net Interest Margin (NIM) stabilized at 3.45% post-merger integration. Deposit mobilization accelerated 16.8% YoY, aiding gradual recovery in our credit-to-deposit ratio.",
        "sentiment": "positive",
        "keywords": ["nim", "deposits", "credit deposit ratio", "merger synergies", "margins"],
        "relevance_base": 0.93,
        "filing_date": "2026-01-18",
        "structured_table": {
            "title": "HDFC Bank Q3 FY26 Key Financial Metrics",
            "headers": ["Financial Metric", "Q3 FY26", "Q3 FY25", "YoY Variance"],
            "rows": [
                ["Net Interest Margin (NIM)", "3.45%", "3.34%", "+11 bps"],
                ["Total Deposits", "₹25.68 lakh cr", "₹21.98 lakh cr", "+16.8%"],
                ["Credit-to-Deposit Ratio", "84.2%", "89.5%", "-530 bps"],
                ["Cost-to-Income Ratio", "40.3%", "39.2%", "+110 bps"]
            ]
        }
    },
    {
        "id": "hdfc-cite-2",
        "ticker": "HDFCBANK",
        "document_title": "Audited Financial Results & SEBI Regulatory Filing",
        "source_type": "SEBI_FILING",
        "section": "Asset Quality & Provisioning Schedule - Page 28",
        "excerpt": "Gross Non-Performing Assets (GNPA) stood robust at 1.28% against 1.34% sequentially. Slippages were well contained across commercial banking and retail portfolios.",
        "sentiment": "positive",
        "keywords": ["asset quality", "gnpa", "provisions", "credit quality", "balance sheet strength"],
        "relevance_base": 0.91,
        "filing_date": "2026-01-18",
        "structured_table": {
            "title": "Asset Quality & NPA Movement Schedule",
            "headers": ["Asset Classification", "Current Quarter", "Previous Quarter", "Variance"],
            "rows": [
                ["Gross NPA Ratio (GNPA)", "1.28%", "1.34%", "-6 bps"],
                ["Net NPA Ratio (NNPA)", "0.35%", "0.37%", "-2 bps"],
                ["Provision Coverage Ratio (PCR)", "74.8%", "73.2%", "+160 bps"],
                ["Annualized Slippage Ratio", "1.15%", "1.22%", "-7 bps"]
            ]
        }
    },
    {
        "id": "hdfc-cite-3",
        "ticker": "HDFCBANK",
        "document_title": "Investor Presentation Q3 FY26",
        "source_type": "SEBI_FILING",
        "section": "Branch Productivity & Digital Banking Highlights - Page 16",
        "excerpt": "Operating expenses rose 11.2% YoY due to ongoing branch network expansion and IT platform modernization, slightly compressing cost-to-income efficiency ratios.",
        "sentiment": "negative",
        "keywords": ["operating expenses", "opex", "cost to income", "headwinds"],
        "relevance_base": 0.85,
        "filing_date": "2026-01-18"
    }
]


class VectorStore:
    """
    Hybrid Knowledge Base Engine for corporate filings and earnings transcripts.
    Combines BM25 Okapi lexical scoring and Dense TF-IDF vector embeddings
    via Reciprocal Rank Fusion (RRF) and convex linear weighting.
    Enforces strict point-in-time isolation (zero future look-ahead),
    2D table structural preservation, ticker pre-filtering,
    thread-safe atomic document persistence, and anti-DoS chunk/size caps.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), "vector_db.json"
        )
        self.documents: List[Dict[str, Any]] = []
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._document_vectors: Optional[np.ndarray] = None
        self._tokenized_corpus: Optional[List[List[str]]] = None
        self.sentiment_timelines = SENTIMENT_TIMELINES
        self._write_lock = threading.Lock()

        self._initialize_corpus()

    def _initialize_corpus(self):
        """Loads corpus from disk if exists, else initializes with baseline filings."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
                # Ensure additional corpus (e.g. HDFCBANK) is merged if missing
                existing_ids = {d.get("id") for d in self.documents if d.get("id")}
                missing = [d for d in ADDITIONAL_CORPUS if d.get("id") not in existing_ids]
                if missing:
                    self.documents.extend(missing)
                # Sync structured tables for existing items
                for d in self.documents:
                    for add_d in ADDITIONAL_CORPUS:
                        if d.get("id") == add_d.get("id") and "structured_table" in add_d:
                            d["structured_table"] = add_d["structured_table"]
                self._save_to_disk()
            except Exception:
                self.documents = list(RAG_DOCUMENTS) + list(ADDITIONAL_CORPUS)
        else:
            self.documents = list(RAG_DOCUMENTS) + list(ADDITIONAL_CORPUS)
            self._save_to_disk()

        self._fit_vectorizer()

    def _save_to_disk(self):
        """Thread-safe persistence of document store to disk."""
        with self._write_lock:
            try:
                temp_path = f"{self.storage_path}.tmp"
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(self.documents, f, indent=2, ensure_ascii=False)
                # Atomic file replacement
                if os.path.exists(temp_path):
                    os.replace(temp_path, self.storage_path)
            except Exception:
                pass

    def _fit_vectorizer(self):
        """Re-fits the TF-IDF vectorizer and tokenized index over all document texts in the corpus under thread lock."""
        with self._write_lock:
            if not self.documents:
                self._vectorizer = None
                self._document_vectors = None
                self._tokenized_corpus = None
                return

            corpus_texts = []
            for d in self.documents:
                title = d.get("document_title", "")
                section = d.get("section", "")
                excerpt = d.get("excerpt", "")
                keywords = " ".join(d.get("keywords", []))
                table_text = ""
                if d.get("structured_table"):
                    table_text = table_parser.linearize_table_for_indexing(d["structured_table"])
                corpus_texts.append(f"{title} {section} {excerpt} {keywords} {table_text}")

            self._vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                max_features=2500,
                sublinear_tf=True
            )
            self._document_vectors = self._vectorizer.fit_transform(corpus_texts)
            self._tokenized_corpus = [tokenize_financial_text(t) for t in corpus_texts]

    def sanitize_text(self, text: str) -> str:
        """
        Sanitizes text inputs to prevent prompt injection and control character attacks.
        Enforces maximum character boundary to prevent quadratic regex/vector denial-of-service.
        """
        if not text:
            return ""
        # Cap text at 500k characters
        capped = text[:500000]
        # Remove null bytes and non-printable control characters (except newline, tab, cr)
        cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", capped)
        # Neutralize common prompt-injection delimiters
        cleaned = re.sub(r"(?i)<\s*(system|prompt|instruction|context)\s*>", "[filtered_tag]", cleaned)
        cleaned = re.sub(r"(?i)<\s*/\s*(system|prompt|instruction|context)\s*>", "[/filtered_tag]", cleaned)
        return cleaned.strip()

    def search_hybrid(
        self,
        ticker: str,
        query: str = "",
        top_k: int = 3,
        as_of_date: Optional[str] = None,
        alpha: float = 0.5,
        mode: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        Hybrid retrieval engine combining BM25 Okapi lexical scoring and Dense TF-IDF vector embeddings
        via Reciprocal Rank Fusion (RRF) and convex linear combination.
        Supports strict point-in-time filtering via `as_of_date` (YYYY-MM-DD) to prevent look-ahead bias.
        """
        start_time = time.perf_counter()
        ticker_up = ticker.upper()

        # Step 1: Pre-filter by ticker and point-in-time date constraint
        candidate_indices = []
        for i, d in enumerate(self.documents):
            if d.get("ticker") == ticker_up:
                if as_of_date:
                    doc_date = d.get("filing_date") or d.get("date") or "2026-01-19"
                    if doc_date > as_of_date:
                        continue  # strictly eliminate forward corporate filing leaks!
                candidate_indices.append(i)

        if not candidate_indices:
            elapsed_ms = max(int((time.perf_counter() - start_time) * 1000), 1)
            return {
                "citations": [],
                "documents_scanned": 0,
                "retrieval_ms": elapsed_ms,
                "status": "UNCATALOGED_CORPUS" if not as_of_date else "NO_POINT_IN_TIME_FILINGS",
                "retrieval_mode": mode.upper()
            }

        if self._vectorizer is None or self._document_vectors is None or self._tokenized_corpus is None:
            self._fit_vectorizer()

        search_query = query if query.strip() else f"{ticker_up} financial results earnings revenue margin debt capex cash flow"

        # Step 2: Dense Vector Retrieval (TF-IDF Cosine Similarity)
        query_vec = self._vectorizer.transform([search_query])
        sub_vectors = self._document_vectors[candidate_indices]
        dense_similarities = cosine_similarity(query_vec, sub_vectors)[0]

        # Step 3: BM25 Lexical Retrieval
        candidate_tokens = [self._tokenized_corpus[idx] for idx in candidate_indices]
        bm25_model = BM25Okapi(candidate_tokens, k1=1.5, b=0.75)
        q_tokens = tokenize_financial_text(query if query.strip() else search_query)
        bm25_raw_scores = bm25_model.get_scores(q_tokens)
        max_bm25 = max(bm25_raw_scores) if bm25_raw_scores and max(bm25_raw_scores) > 0 else 1.0

        # Step 4: Rank ordering for Reciprocal Rank Fusion (RRF)
        dense_order = np.argsort(-dense_similarities).tolist()
        bm25_order = np.argsort(-np.array(bm25_raw_scores)).tolist()

        dense_rank_map = {local_idx: rank_1b for rank_1b, local_idx in enumerate(dense_order, 1)}
        bm25_rank_map = {local_idx: rank_1b for rank_1b, local_idx in enumerate(bm25_order, 1)}

        rrf_fused = ReciprocalRankFusion.fuse(bm25_order, dense_order, k_rrf=60)
        rrf_map = dict(rrf_fused)

        scored_results = []
        for local_idx in range(len(candidate_indices)):
            doc = self.documents[candidate_indices[local_idx]]
            sim_score = float(dense_similarities[local_idx])
            bm_score = float(bm25_raw_scores[local_idx])
            norm_bm = (bm_score / max_bm25) if max_bm25 > 0 else 0.0
            rrf_score = round(float(rrf_map.get(local_idx, 0.0)), 4)
            base_score = doc.get("relevance_base", 0.75)

            # Continuous combined relevance score
            if max_bm25 > 0 and bm_score > 0:
                combined_relevance = round(float(alpha * norm_bm + (1.0 - alpha) * sim_score * 0.8 + 0.2 * base_score), 2)
            else:
                combined_relevance = round(float(0.6 * sim_score + 0.4 * base_score), 2)
            combined_relevance = max(0.50, min(0.98, combined_relevance))

            fiscal = doc.get("fiscal_period")
            if not fiscal:
                for fp in ["Q1 FY26", "Q2 FY26", "Q3 FY26", "Q4 FY26", "Q1 FY25", "Q2 FY25", "Q3 FY25", "Q4 FY25", "FY26", "FY25"]:
                    if fp.lower() in doc.get("document_title", "").lower() or fp.lower() in doc.get("section", "").lower():
                        fiscal = fp
                        break
            if not fiscal:
                fiscal = "FY25/26"

            page = doc.get("page_number")
            if not page:
                sec_text = doc.get("section", "")
                if "page" in sec_text.lower():
                    match = re.search(r"page\s*(\d+)", sec_text, re.IGNORECASE)
                    if match:
                        page = int(match.group(1))
            if not page:
                page = 1

            scored_results.append({
                "id": doc.get("id", f"cite-{candidate_indices[local_idx]}"),
                "ticker": doc.get("ticker", ticker_up),
                "document_title": doc.get("document_title", "Corporate Filing"),
                "source_type": doc.get("source_type", "REGULATORY_FILING"),
                "section": doc.get("section", "General Section"),
                "excerpt": doc.get("excerpt", ""),
                "full_context": doc.get("full_context") or doc.get("excerpt", ""),
                "structured_table": doc.get("structured_table"),
                "relevance_score": combined_relevance,
                "similarity_cosine": round(sim_score, 3),
                "bm25_score": round(bm_score, 3),
                "hybrid_score": combined_relevance,
                "rrf_score": rrf_score,
                "retrieval_method": "HYBRID_BM25_DENSE",
                "rank_bm25": bm25_rank_map[local_idx],
                "rank_dense": dense_rank_map[local_idx],
                "sentiment": doc.get("sentiment", "neutral"),
                "fiscal_period": fiscal,
                "filing_date": doc.get("filing_date") or doc.get("date", "2025-10-24"),
                "page_number": page,
                "keywords": doc.get("keywords", [])
            })

        # Rank ordering by retrieval mode
        if mode == "hybrid":
            scored_results.sort(key=lambda x: (x["rrf_score"], x["relevance_score"]), reverse=True)
        elif mode == "bm25":
            scored_results.sort(key=lambda x: (x["bm25_score"], x["similarity_cosine"]), reverse=True)
        elif mode == "dense":
            scored_results.sort(key=lambda x: (x["similarity_cosine"], x["relevance_score"]), reverse=True)
        else:
            scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)

        top_results = scored_results[:top_k]
        elapsed_ms = max(int((time.perf_counter() - start_time) * 1000), 1)

        return {
            "citations": top_results,
            "documents_scanned": len(candidate_indices),
            "retrieval_ms": elapsed_ms,
            "status": "SUCCESS",
            "as_of_date_applied": as_of_date,
            "retrieval_mode": f"HYBRID_BM25_DENSE_{mode.upper()}"
        }

    def search(
        self,
        ticker: str,
        query: str = "",
        top_k: int = 3,
        as_of_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves matching documents for a ticker with hybrid relevance scoring (BM25 + Dense RRF).
        Supports strict point-in-time filtering via `as_of_date` (YYYY-MM-DD) to prevent look-ahead bias.
        """
        return self.search_hybrid(
            ticker=ticker,
            query=query,
            top_k=top_k,
            as_of_date=as_of_date,
            alpha=0.5,
            mode="hybrid"
        )

    def add_document(
        self,
        ticker: str,
        document_title: str,
        section: str,
        content: str,
        source_type: str = "USER_UPLOAD",
        fiscal_period: str = "FY26",
        filing_date: Optional[str] = None,
        structured_table: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Thread-safely ingests a new document excerpt into the vector store.
        Automatically parses markdown tables to preserve 2D structural integrity.
        """
        sanitized = self.sanitize_text(content)
        if not sanitized:
            raise ValueError("Document content cannot be empty")

        ticker_up = ticker.strip().upper()

        # Auto-extract markdown table if not provided
        if structured_table is None:
            structured_table = table_parser.extract_markdown_table(sanitized)

        # Heuristic polarity classification
        pos_words = ["growth", "record", "expansion", "profit", "surpassed", "strong", "cash", "dividend", "revival"]
        neg_words = ["debt", "contraction", "headwind", "headwinds", "decline", "pressure", "drop", "cut", "drain", "loss"]
        lower = sanitized.lower()
        pos_count = sum(1 for w in pos_words if w in lower)
        neg_count = sum(1 for w in neg_words if w in lower)

        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        doc_id = f"{ticker_up.lower()}-upload-{int(time.time())}-{len(self.documents)}"
        actual_date = filing_date or time.strftime("%Y-%m-%d")

        new_doc = {
            "id": doc_id,
            "ticker": ticker_up,
            "document_title": document_title.strip() or "User Uploaded Corporate Filing",
            "source_type": source_type,
            "fiscal_period": fiscal_period,
            "filing_date": actual_date,
            "section": section.strip() or "Uploaded Excerpt",
            "excerpt": sanitized,
            "structured_table": structured_table,
            "sentiment": sentiment,
            "relevance_base": 0.88,
            "keywords": [w for w in (pos_words + neg_words) if w in lower][:5]
        }

        self.documents.append(new_doc)
        self._save_to_disk()
        self._fit_vectorizer()

        return {
            "id": doc_id,
            "ticker": ticker_up,
            "document_title": new_doc["document_title"],
            "sentiment": sentiment,
            "filing_date": actual_date,
            "has_structured_table": structured_table is not None,
            "status": "INDEXED"
        }

    def ingest_pdf_bytes(
        self,
        pdf_bytes: bytes,
        ticker: str,
        document_title: str = "Corporate Filing PDF"
    ) -> List[Dict[str, Any]]:
        """
        Extracts pages from uploaded PDF bytes via PyMuPDF, chunks text,
        extracts embedded 2D tables, and adds them as indexed citations under safe limits.
        """
        if not HAS_PYMUPDF:
            raise RuntimeError("PyMuPDF (fitz) is not installed for PDF ingestion.")

        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        added_chunks = []

        # Cap at 25 pages to avoid memory/CPU exhaustion
        for page_num in range(min(len(doc), 25)):
            page = doc[page_num]
            text = page.get_text()
            extracted_tables = table_parser.extract_pdf_tables(page)
            structured_table = extracted_tables[0] if extracted_tables else None

            if len(text.strip()) > 50:
                section_name = f"Item/Page {page_num + 1}"
                res = self.add_document(
                    ticker=ticker,
                    document_title=document_title,
                    section=section_name,
                    content=text[:1500],
                    source_type="PDF_UPLOAD",
                    structured_table=structured_table
                )
                added_chunks.append(res)

        return added_chunks

    def get_sentiment_timeline(self, ticker: str) -> Dict[str, Any]:
        """Returns sentiment trajectory across quarters for the UI timeline."""
        ticker_up = ticker.upper()
        if ticker_up in self.sentiment_timelines:
            return self.sentiment_timelines[ticker_up]

        matched = [d for d in self.documents if d.get("ticker") == ticker_up]
        if matched:
            pos = sum(1 for d in matched if d.get("sentiment") == "positive")
            neg = sum(1 for d in matched if d.get("sentiment") == "negative")
            score = round((pos - neg) / len(matched), 2)
            return {
                "ticker": ticker_up,
                "current_quarter": "Q3 FY26",
                "previous_quarter": "Q2 FY26",
                "overall_sentiment_score_current": score,
                "overall_sentiment_score_previous": 0.0,
                "keyword_frequencies": [
                    {"word": "filings scanned", "current_count": len(matched), "previous_count": 0}
                ]
            }

        return {
            "ticker": ticker_up,
            "current_quarter": "Q3 FY26",
            "previous_quarter": "Q2 FY26",
            "overall_sentiment_score_current": 0.0,
            "overall_sentiment_score_previous": 0.0,
            "keyword_frequencies": []
        }


vector_store = VectorStore()
