"""Intent classification for chat messages using zero-shot LLM."""

from __future__ import annotations

import json
from loguru import logger

from backend.config import settings

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore


async def classify_intent(text: str) -> str:
    """Classify user intent using zero-shot LLM.
    
    Returns:
        "knowledge" for factual questions about the Emanuele Artom collection
        "chitchat" for greetings, thanks, farewells
    """
    if AsyncOpenAI is None:
        logger.warning("OpenAI client not available – defaulting to knowledge intent")
        return "knowledge"
    
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    prompt = (
        "You are an intent classifier for an archive assistant.\n"
        "Return exactly 'knowledge' if the message asks for factual "
        "information about the Emanuele Artom collection.\n"
        "Return exactly 'chitchat' for greetings, thanks, farewells, or casual conversation.\n"
        f"Message: {text!r}"
    )
    
    # Prepare API request
    api_request = {
        "model": settings.openai_chat_model,
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    logger.debug("=== INTENT CLASSIFICATION API CALL ===")
    logger.debug("Request: {}", json.dumps(api_request, indent=2))
    
    try:
        resp = await client.chat.completions.create(**api_request)
        
        # Log the full response
        response_content = resp.choices[0].message.content
        logger.debug("Response: {}", json.dumps({
            "model": resp.model,
            "choices": [{
                "message": {
                    "role": resp.choices[0].message.role,
                    "content": response_content
                },
                "finish_reason": resp.choices[0].finish_reason
            }],
            "usage": {
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else None,
                "completion_tokens": resp.usage.completion_tokens if resp.usage else None,
                "total_tokens": resp.usage.total_tokens if resp.usage else None
            }
        }, indent=2))
        logger.debug("=== END INTENT CLASSIFICATION API CALL ===")
        
        result = response_content.strip().lower()
        
        # Validate result
        if result in ("knowledge", "chitchat"):
            logger.debug("[intent] Classified '{}' as '{}'", text[:50], result)
            return result
        else:
            logger.warning("[intent] Unexpected classification '{}' for '{}' – defaulting to knowledge", 
                         result, text[:50])
            return "knowledge"
            
    except Exception as e:
        logger.error("[intent] Classification failed for '{}': {} – defaulting to knowledge", 
                    text[:50], e)
        return "knowledge" 