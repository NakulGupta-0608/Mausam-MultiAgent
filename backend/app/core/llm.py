import os
from typing import Dict, Any, Optional
import httpx
from backend.app.core.config import settings
from backend.app.monitoring.logger import logger


class LLMService:
    """Hybrid LLM service for natural language interpretation, synthesis, and critique reasoning.
    
    Guarantees data integrity: Never fabricates or alters underlying meteorological measurements.
    Uses external LLM providers (Gemini/OpenAI) when API keys are available, and robust structured
    NLP heuristics when offline.
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.gemini_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.openai_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")

    async def generate_reasoning(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2
    ) -> Optional[str]:
        """Attempts to invoke external LLM if configured; otherwise returns None to trigger local reasoning."""
        if self.gemini_key and self.provider == "gemini":
            try:
                return await self._call_gemini(system_prompt, user_prompt, temperature)
            except Exception as e:
                logger.warning(f"Gemini LLM call failed: {e}. Falling back to deterministic reasoning engine.")

        elif self.openai_key and self.provider == "openai":
            try:
                return await self._call_openai(system_prompt, user_prompt, temperature)
            except Exception as e:
                logger.warning(f"OpenAI LLM call failed: {e}. Falling back to deterministic reasoning engine.")

        return None

    async def _call_gemini(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"SYSTEM INSTRUCTION: {system_prompt}\n\nUSER PROMPT: {user_prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 800,
            }
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        raise RuntimeError(f"Gemini API returned status {resp.status_code}")

    async def _call_openai(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": 800,
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
        raise RuntimeError(f"OpenAI API returned status {resp.status_code}")


llm_service = LLMService()
