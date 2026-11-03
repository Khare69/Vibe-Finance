import math
import re
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional


# Standard financial and common English stopwords
ENGLISH_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", "himself", "his",
    "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more", "most", "my",
    "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so", "some", "such",
    "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "we", "were",
    "what", "when", "where", "which", "while", "who", "whom", "why", "with", "would", "you", "your",
    "yours", "yourself", "yourselves"
}


def tokenize_financial_text(text: str) -> List[str]:
    """
    Financial text tokenizer preserving acronyms, compound terms, percentages, and financial metrics.
    Converts to lowercase and filters stopwords.
    """
    if not text:
        return []
    
    # Normalize unicode quotes and dashes
    cleaned = text.lower().replace("’", "'").replace("“", '"').replace("”", '"')
    
    # Extract terms: words with hyphens (e.g. debt-to-equity, cost-to-income),
    # percentages (e.g. 16.8%), currency amounts, or alphanumeric tokens
    tokens = re.findall(r"\b\d+(?:\.\d+)?(?:%|\b)|\b[a-z0-9]+(?:-[a-z0-9]+)*\b", cleaned)
    
    result = []
    for tok in tokens:
        clean_tok = tok.strip()
        if len(clean_tok) > 1 and clean_tok not in ENGLISH_STOPWORDS:
            result.append(clean_tok)
            # If compound hyphenated word, also add sub-tokens for flexible matching
            if "-" in clean_tok:
                for sub in clean_tok.split("-"):
                    if len(sub) > 1 and sub not in ENGLISH_STOPWORDS:
                        result.append(sub)
    return result


class BM25Okapi:
    """
    Production-grade, zero-dependency BM25 Okapi lexical ranking engine.
    Implements Robertson-Spärck Jones IDF with document length normalization.
    
    Formula:
      IDF(q) = ln(1 + (N - n(q) + 0.5) / (n(q) + 0.5))
      Score(D, Q) = Sum[ IDF(q) * (f(q, D) * (k1 + 1)) / (f(q, D) + k1 * (1 - b + b * (|D| / avgdl))) ]
    """

    def __init__(self, corpus_tokens: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus_tokens)
        self.doc_lens = [len(doc) for doc in corpus_tokens]
        self.avgdl = sum(self.doc_lens) / max(self.corpus_size, 1) if self.corpus_size > 0 else 0.0

        # Term frequencies per document
        self.doc_term_freqs: List[Counter] = [Counter(doc) for doc in corpus_tokens]

        # Inverted document frequency table: n(q) = count of docs containing term q
        self.doc_freqs: Dict[str, int] = Counter()
        for dtc in self.doc_term_freqs:
            for term in dtc.keys():
                self.doc_freqs[term] += 1

        # Calculate Robertson-Spärck Jones IDF for all observed terms
        self.idf: Dict[str, float] = {}
        for term, freq in self.doc_freqs.items():
            # Standard smoothed RSJ IDF (always positive)
            self.idf[term] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query_tokens: List[str]) -> List[float]:
        """
        Computes BM25 Okapi relevance score for all indexed documents against a query token list.
        """
        if self.corpus_size == 0 or not query_tokens:
            return [0.0] * self.corpus_size

        scores = [0.0] * self.corpus_size
        for q in query_tokens:
            if q not in self.idf:
                continue
            q_idf = self.idf[q]

            for i in range(self.corpus_size):
                tf = self.doc_term_freqs[i].get(q, 0)
                if tf <= 0:
                    continue
                doc_len = self.doc_lens[i]
                norm_len = (1.0 - self.b) + self.b * (doc_len / max(self.avgdl, 1e-6))
                term_score = q_idf * ((tf * (self.k1 + 1.0)) / (tf + self.k1 * norm_len))
                scores[i] += term_score

        return scores


class ReciprocalRankFusion:
    """
    Reciprocal Rank Fusion (RRF) combiner for hybrid multi-stage retrieval.
    Merges BM25 lexical ranking and Dense Vector ranking into a single consensus ranking.
    
    Formula:
      RRF_Score(d) = Sum[ 1.0 / (k_rrf + rank_m(d)) ]
    """

    @staticmethod
    def fuse(
        bm25_ranked_indices: List[int],
        dense_ranked_indices: List[int],
        k_rrf: int = 60
    ) -> List[Tuple[int, float]]:
        """
        Calculates RRF score for all candidates given the rank order from each retriever.
        Returns sorted list of (candidate_idx, rrf_score) descending.
        """
        rrf_scores: Dict[int, float] = {}

        # BM25 rank contribution (1-based rank)
        for rank_1b, idx in enumerate(bm25_ranked_indices, start=1):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (1.0 / (k_rrf + rank_1b))

        # Dense vector rank contribution (1-based rank)
        for rank_1b, idx in enumerate(dense_ranked_indices, start=1):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (1.0 / (k_rrf + rank_1b))

        # Sort by RRF score descending
        sorted_candidates = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)
        return sorted_candidates


def compute_convex_hybrid_score(
    bm25_score: float,
    dense_score: float,
    max_bm25_in_batch: float,
    alpha: float = 0.5
) -> float:
    """
    Combines normalized BM25 score and Dense cosine similarity score via convex linear weighting.
    alpha = 0.5 weights lexical keywords and dense semantics equally.
    Returns normalized score in [0.0, 1.0].
    """
    norm_bm25 = (bm25_score / max_bm25_in_batch) if max_bm25_in_batch > 0 else 0.0
    norm_bm25 = min(1.0, max(0.0, norm_bm25))
    norm_dense = min(1.0, max(0.0, dense_score))
    
    return float(alpha * norm_bm25 + (1.0 - alpha) * norm_dense)
