import os
import json
import re
import time
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


# Additional initial regulatory filing records (including HDFCBANK)
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
        "relevance_base": 0.93
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
        "relevance_base": 0.91
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
        "relevance_base": 0.85
    }
]


class VectorStore:
    """
    Vector Knowledge Base Engine for corporate filings and earnings transcripts.
    Implements TF-IDF n-gram vectorization, normalized cosine similarity search,
    ticker pre-filtering, document persistence, and prompt-injection sanitization.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), "vector_db.json"
        )
        self.documents: List[Dict[str, Any]] = []
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._document_vectors: Optional[np.ndarray] = None
        self.sentiment_timelines = SENTIMENT_TIMELINES

        self._initialize_corpus()

    def _initialize_corpus(self):
        """Loads corpus from disk if exists, else initializes with baseline filings."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
            except Exception:
                self.documents = list(RAG_DOCUMENTS) + list(ADDITIONAL_CORPUS)
        else:
            self.documents = list(RAG_DOCUMENTS) + list(ADDITIONAL_CORPUS)
            self._save_to_disk()

        self._fit_vectorizer()

    def _save_to_disk(self):
        """Persists document store to disk so user uploads survive restarts."""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _fit_vectorizer(self):
        """Re-fits the TF-IDF vectorizer over all document texts in the corpus."""
        if not self.documents:
            self._vectorizer = None
            self._document_vectors = None
            return

        corpus_texts = []
        for doc in self.documents:
            text = f"{doc.get('document_title', '')} {doc.get('section', '')} {doc.get('excerpt', '')}"
            if doc.get("keywords"):
                text += " " + " ".join(doc["keywords"])
            corpus_texts.append(text)

        self._vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=5000,
            token_pattern=r'(?u)\b\w+\b'
        )
        self._document_vectors = self._vectorizer.fit_transform(corpus_texts)

    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Sanitizes text against prompt-injection attacks and control characters.
        Treats corporate filing content as untrusted data.
        """
        if not text:
            return ""
        # Remove null bytes and non-printable control characters (keep newlines/tabs)
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        # Neutralize common prompt-injection attempts
        injection_patterns = [
            r'(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions?',
            r'(?i)you\s+are\s+now\s+(a|an)?\s+',
            r'(?i)system\s*prompt\s*:',
            r'(?i)disregard\s+(above|all)\s+',
            r'(?i)new\s+rule\s*:'
        ]
        for pattern in injection_patterns:
            sanitized = re.sub(pattern, '[FILTERED_INSTRUCTION]', sanitized)
        return sanitized.strip()

    def search(
        self,
        ticker: str,
        query: str = "",
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Vector similarity search filtered by ticker.
        Prevents look-ahead cross-ticker contamination by isolating candidates strictly to ticker.
        """
        start_time = time.perf_counter()
        ticker_up = ticker.upper()

        # Step 1: Pre-filter by ticker (eliminates cross-company leakage)
        candidate_indices = [
            i for i, d in enumerate(self.documents) if d.get("ticker") == ticker_up
        ]

        if not candidate_indices:
            elapsed_ms = max(int((time.perf_counter() - start_time) * 1000), 1)
            return {
                "citations": [],
                "documents_scanned": 0,
                "retrieval_ms": elapsed_ms,
                "status": "UNCATALOGED_CORPUS"
            }

        if self._vectorizer is None or self._document_vectors is None:
            self._fit_vectorizer()

        # Step 2: Compute vector similarity
        search_query = query if query.strip() else f"{ticker_up} financial results earnings revenue margin debt capex cash flow"
        query_vec = self._vectorizer.transform([search_query])

        # Slice candidate vectors
        sub_vectors = self._document_vectors[candidate_indices]
        similarities = cosine_similarity(query_vec, sub_vectors)[0]

        scored_results = []
        for local_idx, sim_score in enumerate(similarities):
            doc = self.documents[candidate_indices[local_idx]]
            base_score = doc.get("relevance_base", 0.75)
            # Combine vector cosine similarity with base quality weighting
            combined_relevance = round(float(0.6 * sim_score + 0.4 * base_score), 2)
            # Ensure between 0.50 and 0.98
            combined_relevance = max(0.50, min(0.98, combined_relevance))

            scored_results.append({
                "id": doc.get("id", f"cite-{candidate_indices[local_idx]}"),
                "document_title": doc.get("document_title", "Corporate Filing"),
                "source_type": doc.get("source_type", "REGULATORY_FILING"),
                "section": doc.get("section", "General Section"),
                "excerpt": doc.get("excerpt", ""),
                "relevance_score": combined_relevance,
                "sentiment": doc.get("sentiment", "neutral")
            })

        # Rank by score descending
        scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_results = scored_results[:top_k]

        elapsed_ms = max(int((time.perf_counter() - start_time) * 1000), 1)

        return {
            "citations": top_results,
            "documents_scanned": len(candidate_indices),
            "retrieval_ms": elapsed_ms,
            "status": "CATALOGED"
        }

    def add_document(
        self,
        ticker: str,
        document_title: str,
        section: str,
        content: str,
        source_type: str = "USER_UPLOAD",
        fiscal_period: str = "Q3 FY26"
    ) -> Dict[str, Any]:
        """
        Ingests user-uploaded or dynamically parsed documents into the vector store.
        Sanitizes text, creates chunk embeddings, and persists to disk.
        """
        sanitized = self.sanitize_text(content)
        ticker_up = ticker.upper()

        # Semantic sentiment detection for financial chunk
        lower = sanitized.lower()
        pos_words = [
            "growth", "record", "expansion", "profit", "surpassed", "surpassing",
            "strong", "cash", "dividend", "revival", "rose", "climbing", "climb",
            "robust", "increase", "operating income", "accelerated", "healthy"
        ]
        neg_words = [
            "debt", "contraction", "headwind", "headwinds", "decline", "pressure",
            "drop", "cut", "drain", "loss", "fell", "decrease", "compress", "compression"
        ]

        pos_count = sum(1 for w in pos_words if w in lower)
        neg_count = sum(1 for w in neg_words if w in lower)

        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        doc_id = f"{ticker_up.lower()}-upload-{int(time.time())}-{len(self.documents)}"

        new_doc = {
            "id": doc_id,
            "ticker": ticker_up,
            "document_title": document_title.strip() or "User Uploaded Corporate Filing",
            "source_type": source_type,
            "fiscal_period": fiscal_period,
            "section": section.strip() or "Uploaded Excerpt",
            "excerpt": sanitized,
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
        and adds them as indexed citations.
        """
        if not HAS_PYMUPDF:
            raise RuntimeError("PyMuPDF (fitz) is not installed for PDF ingestion.")

        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        added_chunks = []

        for page_num in range(min(len(doc), 20)):  # Cap at 20 pages
            page = doc[page_num]
            text = page.get_text()
            if len(text.strip()) > 50:
                # Chunk into sections if long
                section_name = f"Item/Page {page_num + 1}"
                res = self.add_document(
                    ticker=ticker,
                    document_title=document_title,
                    section=section_name,
                    content=text[:1200],  # first 1200 chars per page
                    source_type="PDF_UPLOAD"
                )
                added_chunks.append(res)

        return added_chunks

    def get_sentiment_timeline(self, ticker: str) -> Dict[str, Any]:
        """Returns sentiment trajectory across quarters for the UI timeline."""
        ticker_up = ticker.upper()
        if ticker_up in self.sentiment_timelines:
            return self.sentiment_timelines[ticker_up]

        # Calculate dynamic timeline from ingested documents
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
