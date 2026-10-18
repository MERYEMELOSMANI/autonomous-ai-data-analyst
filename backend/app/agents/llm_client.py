import os
import json
import logging
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMProvider:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        self.model_name = settings.GEMINI_MODEL
        self._client = None

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def get_client(self):
        if not self.is_configured():
            return None
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model_name)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                return None
        return self._client

    async def generate_json(self, prompt: str, schema_description: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Call Gemini to generate a structured JSON response."""
        client = self.get_client()
        if not client:
            return None

        full_prompt = f"{prompt}\n\nIMPORTANT: Return ONLY a valid JSON object matching the requested schema. Do not enclose in markdown blocks if possible, or use standard ```json ``` formatting."
        try:
            response = client.generate_content(full_prompt)
            text = response.text.strip()
            # Clean markdown codeblocks if present
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            return json.loads(text)
        except Exception as e:
            logger.warning(f"Gemini API call or JSON parsing failed: {e}")
            return None

    async def generate_text(self, prompt: str) -> Optional[str]:
        """Call Gemini to generate unstructured text."""
        client = self.get_client()
        if not client:
            return None

        try:
            response = client.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}")
            return None

llm_provider = LLMProvider()
