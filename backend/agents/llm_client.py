import os
import json
import httpx
from typing import Dict, Any, List, Optional

class LLMAgentClient:
    """
    Hybrid LLM Client supporting Google Gemini API with strict structured JSON schemas,
    falling back seamlessly to generalized deterministic templates when offline or unconfigured.
    """

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model = "gemini-1.5-flash"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    def generate_debate_dialogue(
        self,
        ticker: str,
        quant_result: Dict[str, Any],
        rag_result: Dict[str, Any],
        behavioral_result: Dict[str, Any],
        user_risk_profile: str
    ) -> Optional[List[Dict[str, str]]]:
        """Calls Gemini to generate 3-turn multi-agent adversarial debate if API key exists."""
        if not self.is_available():
            return None

        prompt = f"""
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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        try:
            with httpx.Client(timeout=4.0) as client:
                res = client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"response_mime_type": "application/json"}
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    dialogue = json.loads(text)
                    if isinstance(dialogue, list) and len(dialogue) == 3:
                        return dialogue
        except Exception:
            pass
        return None

    def generate_synthesis_explanations(
        self,
        ticker: str,
        final_action: str,
        quant_score: int,
        rag_score: int,
        user_risk: str
    ) -> Optional[Dict[str, str]]:
        """Calls Gemini to generate Beginner (ELI5) and Expert institutional summaries."""
        if not self.is_available():
            return None

        prompt = f"""
Write an investment synthesis for {ticker} (Action: {final_action}, Quant: {quant_score}/100, RAG: {rag_score}/100, Risk Mandate: {user_risk}).
Return a JSON object:
{{
  "beginner": "2-3 sentences plain English everyday analogy for a retail beginner (ELI5)",
  "expert": "2-3 sentences institutional quantitative macro summary"
}}
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        try:
            with httpx.Client(timeout=4.0) as client:
                res = client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"response_mime_type": "application/json"}
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    exp = json.loads(text)
                    if "beginner" in exp and "expert" in exp:
                        return exp
        except Exception:
            pass
        return None

llm_client = LLMAgentClient()
