"""
LLM service for Azure OpenAI integration with rate limiting and error handling
"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any, cast
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.client_mini = None
        self.client_full = None
        self._setup_clients()

    def _setup_clients(self):
        """Initialize Azure OpenAI clients"""
        try:
            # Mini client (gpt-4o-mini)
            if settings.AZURE_OPENAI_API_KEY_mini and settings.AZURE_OPENAI_ENDPOINT_mini:
                self.client_mini = openai.AsyncAzureOpenAI(
                    api_key=settings.AZURE_OPENAI_API_KEY_mini,
                    api_version="2024-02-01",
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT_mini
                )

            # Full client (gpt-4o)
            if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
                self.client_full = openai.AsyncAzureOpenAI(
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    api_version="2024-02-01",
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
                )

        except Exception as e:
            logger.error(f"Failed to initialize LLM clients: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(
            (openai.RateLimitError, openai.APITimeoutError))
    )
    async def call_mini_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> Optional[Dict[Any, Any]]:
        """Call gpt-4o-mini for fast, cheap operations like NLU parsing"""
        if not self.client_mini:
            raise ValueError(
                "Mini LLM client not configured. Check AZURE_OPENAI_*_mini settings.")

        try:
            response = await self.client_mini.chat.completions.create(
                model=cast(str, settings.AZURE_OPENAI_DEPLOYMENT_mini),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            return json.loads(cast(str, content))

        except openai.RateLimitError as e:
            logger.warning(f"Rate limit hit for mini LLM: {e}")
            raise
        except openai.APITimeoutError as e:
            logger.warning(f"Timeout for mini LLM: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse mini LLM JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Mini LLM call failed: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(
            (openai.RateLimitError, openai.APITimeoutError))
    )
    async def call_full_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 1000) -> Optional[Dict[Any, Any]]:
        """Call gpt-4o for complex reasoning like decision engine"""
        if not self.client_full:
            raise ValueError(
                "Full LLM client not configured. Check AZURE_OPENAI_* settings.")

        try:
            response = await self.client_full.chat.completions.create(
                model=cast(str, settings.AZURE_OPENAI_DEPLOYMENT),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            return json.loads(cast(str, content))

        except openai.RateLimitError as e:
            logger.warning(f"Rate limit hit for full LLM: {e}")
            raise
        except openai.APITimeoutError as e:
            logger.warning(f"Timeout for full LLM: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse full LLM JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Full LLM call failed: {e}")
            return None


# Global LLM service instance
llm_service = LLMService()
