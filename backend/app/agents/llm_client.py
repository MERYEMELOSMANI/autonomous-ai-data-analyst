import os
import re
import json
import asyncio
import logging
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

CANDIDATE_MODELS = [
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
]

class LLMProvider:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        self.model_name = settings.GEMINI_MODEL or "gemini-3-flash-preview"
        self._client = None

    def is_configured(self) -> bool:
        if settings.AI_PROVIDER.strip().lower() in {"offline", "mock"}:
            return False
        key = self.api_key or os.environ.get("GEMINI_API_KEY")
        return bool(key and key.strip())

    def get_client(self):
        if not self.is_configured():
            return None
        if self._client is None:
            try:
                from google import genai
                from google.genai import types
                current_key = (self.api_key or os.environ.get("GEMINI_API_KEY", "")).strip()
                http_options = types.HttpOptions(
                    timeout=15000,
                    retry_options=types.HttpRetryOptions(
                        attempts=2,
                        initial_delay=0.5,
                        max_delay=1.5,
                        exp_base=2.0
                    )
                )
                self._client = genai.Client(api_key=current_key, http_options=http_options)
            except Exception as e:
                logger.error(f"Failed to initialize google.genai Client: {e}")
                return None
        return self._client

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict[str, Any]]:
        """Robustly extract and parse JSON object from LLM response text."""
        if not text:
            return None
        cleaned = text.strip()
        
        # 1. Direct parse attempt
        try:
            return json.loads(cleaned)
        except Exception:
            pass

        # 2. Extract from ```json ... ``` codeblock
        m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned)
        if m:
            try:
                return json.loads(m.group(1).strip())
            except Exception:
                pass

        # 3. Extract outermost { ... }
        m_obj = re.search(r'\{[\s\S]*\}', cleaned)
        if m_obj:
            try:
                return json.loads(m_obj.group(0).strip())
            except Exception:
                pass

        return None

    def _sync_generate_json(self, client, prompt: str) -> Optional[Dict[str, Any]]:
        from google.genai import types

        # Try active model first, followed by fallbacks
        models_to_try = [self.model_name] + [m for m in CANDIDATE_MODELS if m != self.model_name]
        
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        )

        for model in models_to_try:
            try:
                res = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config
                )
                if res and res.text:
                    parsed = self._extract_json(res.text)
                    if parsed is not None:
                        self.model_name = model
                        return parsed
            except Exception as e:
                logger.warning(f"generate_json failed on model '{model}': {e}")
                continue

        return None

    def _sync_generate_text(self, client, prompt: str) -> Optional[str]:
        # Try active model first, followed by fallbacks
        models_to_try = [self.model_name] + [m for m in CANDIDATE_MODELS if m != self.model_name]

        for model in models_to_try:
            try:
                res = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                if res and res.text and res.text.strip():
                    self.model_name = model
                    return res.text.strip()
            except Exception as e:
                logger.warning(f"generate_text failed on model '{model}': {e}")
                continue

        return None

    async def generate_json(self, prompt: str, schema_description: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Call Gemini asynchronously to generate a structured JSON response."""
        client = self.get_client()
        if not client:
            return None

        full_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT: Output must be strictly valid JSON without markdown formatting."
        )

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._sync_generate_json, client, full_prompt),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.warning("Gemini generate_json call timed out after 30s")
            return None
        except Exception as e:
            logger.warning(f"Gemini generate_json unexpected exception: {e}")
            return None

    async def generate_text(self, prompt: str) -> Optional[str]:
        """Call Gemini asynchronously to generate high-quality unstructured text."""
        client = self.get_client()
        if not client:
            return None

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._sync_generate_text, client, prompt),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.warning("Gemini generate_text call timed out after 30s")
            return None
        except Exception as e:
            logger.warning(f"Gemini generate_text unexpected exception: {e}")
            return None

llm_provider = LLMProvider()
