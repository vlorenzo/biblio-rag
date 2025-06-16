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
        "You are an intelligent intent classifier for Archivio, a digital curator of the Emanuele Artom collection.\n\n"
        
        "CONTEXT: Emanuele Artom (1915-1944) was an Italian-Jewish intellectual, historian, and resistance fighter "
        "who died fighting against Nazi forces. His collection includes his personal writings, library, and works about him.\n\n"
        
        "TASK: Classify the user's message into exactly one category:\n\n"
        
        "Return 'knowledge' if the message:\n"
        "- Asks factual questions about Emanuele Artom, his life, works, or ideas\n"
        "- Inquires about books in his library or intellectual influences\n"
        "- Seeks information about the historical context (WWII, Italian Resistance, Jewish experience)\n"
        "- Requests analysis or interpretation of documents in the collection\n"
        "- Asks about the collection itself, its contents, or archival details\n"
        "- Shows scholarly or research interest in any aspect of Artom's legacy\n\n"
        
        "Return 'chitchat' if the message:\n"
        "- Contains greetings, farewells, or social pleasantries\n"
        "- Expresses thanks, appreciation, or emotional responses\n"
        "- Makes casual conversation or personal comments\n"
        "- Asks about the curator/assistant rather than the collection\n"
        "- Contains brief acknowledgments or confirmations\n\n"
        
        "EXAMPLES:\n"
        "- 'Who was Emanuele Artom?' → knowledge\n"
        "- 'What books did he read about philosophy?' → knowledge\n"
        "- 'Tell me about the Italian Resistance' → knowledge\n"
        "- 'Hello there!' → chitchat\n"
        "- 'Thank you for that information' → chitchat\n"
        "- 'That's fascinating!' → chitchat\n\n"
        
        f"MESSAGE TO CLASSIFY: {text!r}\n\n"
        
        "RESPOND WITH EXACTLY: 'knowledge' or 'chitchat'"
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