import os
import json
import httpx
import asyncio
from typing import Dict, Any, List, Optional


class LLMAgentClient:
    """
    Hybrid LLM Client supporting Google Gemini API with strict structured JSON schemas,
    secure header authentication, non-blocking asynchronous network I/O,
    and graceful deterministic fallback templates.
    """

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        # Default to modern Gemini 2.5 Flash, configurable via environment
        self.model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self._async_client: Optional[httpx.AsyncClient] = None

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    async def get_async_client(self) -> httpx.AsyncClient:
        """Retrieves or initializes a shared persistent AsyncClient."""
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(timeout=10.0)
        return self._async_client

    async def close(self):
        """Cleanly terminates the underlying connection pool."""
        if self._async_client is not None and not self._async_client.is_closed:
            await self._async_client.aclose()
            self._async_client = None

    async def _post_gemini_async(self, prompt: str, timeout: float = 4.5) -> Optional[str]:
        """Executes non-blocking asynchronous Gemini API call with secure header auth."""
        if not self.is_available():
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key.strip()
        }
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }

        try:
            client = await self.get_async_client()
            res = await client.post(url, headers=headers, json=payload, timeout=timeout)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
        except Exception:
            pass
        return None

    def _post_gemini(self, prompt: str, timeout: float = 4.5) -> Optional[str]:
        """Executes synchronous Gemini API call with secure header auth (for sync callers)."""
        if not self.is_available():
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key.strip()
        }
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
        except Exception:
            pass
        return None

    # --- Evidence Extraction (Async & Sync) ---

    def _build_evidence_prompt(self, ticker: str, citations: List[Dict[str, Any]]) -> str:
        citation_text = ""
        for i, c in enumerate(citations, 1):
            citation_text += f"\n[Citation {i}] Document: {c.get('document_title')} | Section: {c.get('section')}\nExcerpt: \"{c.get('excerpt')}\"\n"

        return f"""
You are a senior fundamental equity research analyst evaluating corporate disclosures for {ticker}.
Evaluate the following filing excerpts objectively:

<corporate_filing_evidence>
{citation_text}
</corporate_filing_evidence>

Evaluate the balance sheet health, operating margins, capex requirements, debt servicing, and revenue trends.
Output a strict JSON object with:
{{
  "score": <integer between 10 and 95 representing business quality and financial health>,
  "stance": "<BULLISH | BEARISH | NEUTRAL>",
  "key_findings": [
    "<Concise finding 1 citing specific metrics or facts from the excerpts>",
    "<Concise finding 2 citing specific metrics or facts from the excerpts>",
    "<Concise finding 3 citing specific metrics or facts from the excerpts>"
  ]
}}
"""

    def _parse_evidence_response(self, raw_json: Optional[str]) -> Optional[Dict[str, Any]]:
        if not raw_json:
            return None
        try:
            parsed = json.loads(raw_json)
            if "score" in parsed and "stance" in parsed and "key_findings" in parsed:
                score = int(max(10, min(95, parsed["score"])))
                stance = str(parsed["stance"]).upper()
                if stance not in ["BULLISH", "BEARISH", "NEUTRAL"]:
                    stance = "BULLISH" if score >= 65 else ("BEARISH" if score <= 42 else "NEUTRAL")
                return {
                    "score": score,
                    "stance": stance,
                    "key_findings": list(parsed["key_findings"])[:3]
                }
        except Exception:
            pass
        return None

    async def extract_fundamental_evidence_async(
        self,
        ticker: str,
        citations: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Asynchronously extracts fundamental health scores and findings from filings."""
        if not citations:
            return None
        prompt = self._build_evidence_prompt(ticker, citations)
        raw_json = await self._post_gemini_async(prompt, timeout=5.0)
        return self._parse_evidence_response(raw_json)

    def extract_fundamental_evidence(
        self,
        ticker: str,
        citations: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Synchronously extracts fundamental health scores and findings from filings."""
        if not citations:
            return None
        prompt = self._build_evidence_prompt(ticker, citations)
        raw_json = self._post_gemini(prompt, timeout=5.0)
        return self._parse_evidence_response(raw_json)

    # --- Multi-Agent Debate Dialogue (Async & Sync) ---

    def _build_debate_prompt(
        self,
        ticker: str,
        quant_result: Dict[str, Any],
        rag_result: Dict[str, Any],
        behavioral_result: Dict[str, Any],
        user_risk_profile: str
    ) -> str:
        return f"""
You are arbitrating an adversarial investment debate on {ticker} between three specialized agents:
1. Quantitative Analyst: Stance={quant_result.get('stance')}, Score={quant_result.get('score')}/100, Signals={quant_result.get('signals')}
2. Fundamental RAG Agent: Stance={rag_result.get('stance')}, Score={rag_result.get('score')}/100, Findings={rag_result.get('key_findings')}
3. Behavioral Risk Manager: User Risk Profile={user_risk_profile}, Stance={behavioral_result.get('stance')}, Rules={behavioral_result.get('behavioral_adjustments')}

Output a JSON array of exactly 3 objects:
[
  {{"speaker": "Quant Agent", "text": "..."}},
  {{"speaker": "Fundamental RAG Agent", "text": "..."}},
  {{"speaker": "Behavioral Risk Manager", "text": "..."}}
]
"""

    def _parse_debate_response(self, raw_json: Optional[str]) -> Optional[List[Dict[str, str]]]:
        if not raw_json:
            return None
        try:
            dialogue = json.loads(raw_json)
            if isinstance(dialogue, list) and len(dialogue) == 3:
                return dialogue
        except Exception:
            pass
        return None

    async def generate_debate_dialogue_async(
        self,
        ticker: str,
        quant_result: Dict[str, Any],
        rag_result: Dict[str, Any],
        behavioral_result: Dict[str, Any],
        user_risk_profile: str
    ) -> Optional[List[Dict[str, str]]]:
        """Asynchronously generates 3-turn multi-agent adversarial debate."""
        prompt = self._build_debate_prompt(ticker, quant_result, rag_result, behavioral_result, user_risk_profile)
        raw_json = await self._post_gemini_async(prompt, timeout=4.5)
        return self._parse_debate_response(raw_json)

    def generate_debate_dialogue(
        self,
        ticker: str,
        quant_result: Dict[str, Any],
        rag_result: Dict[str, Any],
        behavioral_result: Dict[str, Any],
        user_risk_profile: str
    ) -> Optional[List[Dict[str, str]]]:
        """Synchronously generates 3-turn multi-agent adversarial debate."""
        prompt = self._build_debate_prompt(ticker, quant_result, rag_result, behavioral_result, user_risk_profile)
        raw_json = self._post_gemini(prompt, timeout=4.5)
        return self._parse_debate_response(raw_json)

    # --- Synthesis Explanations (Async & Sync) ---

    def _build_synthesis_prompt(
        self,
        ticker: str,
        final_action: str,
        quant_score: int,
        rag_score: int,
        user_risk: str
    ) -> str:
        return f"""
Write an investment synthesis for {ticker} (Action: {final_action}, Quant: {quant_score}/100, RAG: {rag_score}/100, Risk Mandate: {user_risk}).
Return a JSON object:
{{
  "beginner": "2-3 sentences plain English everyday analogy for a retail beginner (ELI5)",
  "expert": "2-3 sentences institutional quantitative macro summary"
}}
"""

    def _parse_synthesis_response(self, raw_json: Optional[str]) -> Optional[Dict[str, str]]:
        if not raw_json:
            return None
        try:
            exp = json.loads(raw_json)
            if "beginner" in exp and "expert" in exp:
                return exp
        except Exception:
            pass
        return None

    async def generate_synthesis_explanations_async(
        self,
        ticker: str,
        final_action: str,
        quant_score: int,
        rag_score: int,
        user_risk: str
    ) -> Optional[Dict[str, str]]:
        """Asynchronously generates Beginner (ELI5) and Expert institutional summaries."""
        prompt = self._build_synthesis_prompt(ticker, final_action, quant_score, rag_score, user_risk)
        raw_json = await self._post_gemini_async(prompt, timeout=4.5)
        return self._parse_synthesis_response(raw_json)

    def generate_synthesis_explanations(
        self,
        ticker: str,
        final_action: str,
        quant_score: int,
        rag_score: int,
        user_risk: str
    ) -> Optional[Dict[str, str]]:
        """Synchronously generates Beginner (ELI5) and Expert institutional summaries."""
        prompt = self._build_synthesis_prompt(ticker, final_action, quant_score, rag_score, user_risk)
        raw_json = self._post_gemini(prompt, timeout=4.5)
        return self._parse_synthesis_response(raw_json)


llm_client = LLMAgentClient()
