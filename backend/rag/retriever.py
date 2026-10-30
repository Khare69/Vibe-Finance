import time
from typing import List, Dict, Any, Optional

from backend.rag.vector_store import vector_store


class RAGRetriever:
    """
    RAG Retriever for financial filings and earnings transcripts.
    Delegates to the persistent VectorStore using n-gram TF-IDF vector embeddings
    and cosine similarity ranking.
    """

    def __init__(self):
        self.store = vector_store

    @property
    def documents(self):
        return self.store.documents

    def search(self, ticker: str, query: str = "", top_k: int = 3) -> Dict[str, Any]:
        """
        Retrieves matching documents for a ticker with vector relevance scoring and extracted quotes.
        """
        return self.store.search(ticker=ticker, query=query, top_k=top_k)

    def add_document(
        self,
        ticker: str,
        document_title: str,
        section: str,
        content: str,
        source_type: str = "USER_UPLOAD"
    ) -> Dict[str, Any]:
        """
        Ingests user-uploaded documents into the persistent vector store.
        """
        return self.store.add_document(
            ticker=ticker,
            document_title=document_title,
            section=section,
            content=content,
            source_type=source_type
        )

    def ingest_document(
        self,
        ticker: str,
        document_title: str,
        section: str,
        content: str,
        source_type: str = "USER_UPLOAD"
    ) -> List[Dict[str, Any]]:
        """
        Chunks and ingests a text document into the vector store.
        """
        sanitized = self.store.sanitize_text(content)
        # If content is longer than 500 characters, chunk it into 400-char pieces
        chunks_created = []
        if len(sanitized) > 500:
            step = 350
            for i in range(0, len(sanitized), step):
                chunk_slice = sanitized[i:i + 450]
                chunk_section = f"{section} (Part {len(chunks_created) + 1})"
                res = self.store.add_document(
                    ticker=ticker,
                    document_title=document_title,
                    section=chunk_section,
                    content=chunk_slice,
                    source_type=source_type
                )
                chunks_created.append(res)
        else:
            res = self.store.add_document(
                ticker=ticker,
                document_title=document_title,
                section=section,
                content=sanitized,
                source_type=source_type
            )
            chunks_created.append(res)

        return chunks_created

    def ingest_pdf(
        self,
        pdf_bytes: bytes,
        ticker: str,
        document_title: str = "Corporate Filing PDF"
    ) -> List[Dict[str, Any]]:
        """Ingests a PDF file via PyMuPDF page-by-page."""
        return self.store.ingest_pdf_bytes(
            pdf_bytes=pdf_bytes,
            ticker=ticker,
            document_title=document_title
        )

    def get_sentiment_timeline(self, ticker: str) -> Dict[str, Any]:
        """
        Retrieves historical sentiment trajectory for a ticker.
        """
        return self.store.get_sentiment_timeline(ticker)


rag_retriever = RAGRetriever()
