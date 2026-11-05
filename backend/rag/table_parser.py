import re
from typing import List, Dict, Any, Optional, Tuple


class FinancialTableParser:
    """
    Parser and structural normalizer for 2D financial tables (Balance Sheets,
    Income Statements, Footnote disclosures).
    Extracts structured tables from markdown, text, or PDF pages, preserving
    column headers and row metrics to prevent RAG chunking blindness.
    """

    @staticmethod
    def extract_markdown_table(text: str) -> Optional[Dict[str, Any]]:
        """
        Detects and parses Markdown-formatted tables from financial document excerpts.
        Returns a structured dictionary with headers and rows.
        """
        if not text or "|" not in text:
            return None

        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        table_lines = [l for l in lines if l.startswith("|") and l.endswith("|")]
        if len(table_lines) < 3:
            return None

        # Line 0: headers
        raw_headers = [c.strip() for c in table_lines[0].split("|")[1:-1]]
        # Line 1: delimiter separator (e.g. |---|---|)
        if not all(re.match(r"^:?-+:?$", c.strip()) for c in table_lines[1].split("|")[1:-1]):
            return None

        headers = raw_headers
        rows = []
        for line in table_lines[2:]:
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) == len(headers):
                rows.append(cols)

        if not rows:
            return None

        return {
            "title": "Extracted Financial Statement Table",
            "headers": headers,
            "rows": rows
        }

    @staticmethod
    def linearize_table_for_indexing(table: Dict[str, Any]) -> str:
        """
        Linearizes a 2D financial table into contextualized text representations
        that preserve row-metric and column-value bindings for BM25 and vector search.
        E.g. "Net Interest Margin (NIM) Q3 FY26: 3.45% YoY Change: +11 bps"
        """
        if not table or "headers" not in table or "rows" not in table:
            return ""

        headers = table["headers"]
        rows = table["rows"]
        linear_statements = []

        for row in rows:
            if not row:
                continue
            metric_name = row[0]
            tokens = [metric_name]
            for col_idx in range(1, min(len(row), len(headers))):
                header = headers[col_idx]
                val = row[col_idx]
                tokens.append(f"{header}: {val}")
            linear_statements.append(" ".join(tokens))

        return " | ".join(linear_statements)

    @staticmethod
    def extract_pdf_tables(page: Any) -> List[Dict[str, Any]]:
        """
        Extracts structured tables from a PyMuPDF page object via page.find_tables().
        Falls back gracefully if find_tables() is not supported on older versions.
        """
        tables_found = []
        try:
            if hasattr(page, "find_tables"):
                tabs = page.find_tables()
                for tab in tabs:
                    extracted = tab.extract()
                    if extracted and len(extracted) >= 2:
                        headers = [str(c or "").strip() for c in extracted[0]]
                        rows = []
                        for r in extracted[1:]:
                            clean_row = [str(c or "").strip() for c in r]
                            if any(clean_row):
                                rows.append(clean_row)
                        if rows:
                            tables_found.append({
                                "title": "Filing PDF Extracted Table",
                                "headers": headers,
                                "rows": rows
                            })
        except Exception:
            pass
        return tables_found


table_parser = FinancialTableParser()
