import json
import logging
from typing import Optional, Type, TypeVar
from pydantic import BaseModel
try:
    from groq import Groq, APIError, APITimeoutError, RateLimitError
except ImportError:  # Allows offline tests and UI startup before dependencies are installed.
    Groq = None
    class APIError(Exception): pass
    class APITimeoutError(Exception): pass
    class RateLimitError(Exception): pass
from ..config import settings
import asyncio

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _get_client() -> Optional[Groq]:
    """Get Groq client. Returns None if not configured."""
    if Groq is None:
        return None
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your-groq-api-key-here":
        return None
    return Groq(api_key=settings.GROQ_API_KEY, timeout=120.0)


async def generate_structured(
    prompt: str,
    system_prompt: str = "You are an expert advertising strategist.",
    response_model: Optional[Type[T]] = None,
    max_retries: int = 3,
    temperature: float = 0.7,
) -> dict:
    """
    Generate a structured JSON response from Groq.
    
    Args:
        prompt: The user prompt
        system_prompt: System instructions
        response_model: Optional Pydantic model to validate response
        max_retries: Number of retries for transient failures
        temperature: LLM temperature
    
    Returns:
        Parsed JSON dict (validated against response_model if provided)
    """
    client = _get_client()
    if not client:
        raise RuntimeError("Groq API key not configured. Set GROQ_API_KEY in .env")
    
    model = settings.GROQ_MODEL
    
    # Add JSON instruction to system prompt
    json_system = (
        f"{system_prompt}\n\n"
        "IMPORTANT: You must respond with valid JSON only. No markdown, no code fences, no explanation outside the JSON."
    )
    
    if response_model:
        schema = response_model.model_json_schema()
        json_system += f"\n\nRespond with JSON matching this schema:\n{json.dumps(schema, indent=2)}"
    
    last_error = None
    for attempt in range(max_retries):
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": json_system},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            parsed = json.loads(content)
            
            # Validate with Pydantic if model provided
            if response_model:
                validated = response_model.model_validate(parsed)
                return validated.model_dump()
            
            return parsed
            
        except (APITimeoutError, RateLimitError) as e:
            last_error = e
            logger.warning(f"Groq transient error (attempt {attempt + 1}/{max_retries}): {type(e).__name__}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        except APIError as e:
            logger.error(f"Groq API error: {e}")
            raise RuntimeError(f"Groq API error: {e.message}")
        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(f"Invalid JSON from Groq (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
    
    raise RuntimeError(f"Groq generation failed after {max_retries} attempts: {last_error}")


async def generate_text(
    prompt: str,
    system_prompt: str = "You are an expert advertising strategist.",
    max_retries: int = 3,
    temperature: float = 0.7,
) -> str:
    """Generate unstructured text from Groq."""
    client = _get_client()
    if not client:
        raise RuntimeError("Groq API key not configured. Set GROQ_API_KEY in .env")
    
    last_error = None
    for attempt in range(max_retries):
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=2048,
            )
            return response.choices[0].message.content
        except (APITimeoutError, RateLimitError) as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        except APIError as e:
            raise RuntimeError(f"Groq API error: {e.message}")
    
    raise RuntimeError(f"Groq text generation failed after {max_retries} attempts: {last_error}")
