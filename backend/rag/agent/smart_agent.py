"""Smart Agent - A truly intelligent agent that decides when to retrieve knowledge.

This agent uses OpenAI's function calling to make real decisions about when it needs
more information, rather than pre-classifying intents. It has personality and can
engage in both casual conversation and scholarly discussion.
"""

from __future__ import annotations

import json
from typing import Dict, List, Tuple, Optional, Any

from loguru import logger
from sqlmodel import Session

from backend.config import settings
from backend.services import retrieval_service
from backend.rag.guardrails import apply_guardrails

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore


class SmartAgent:
    """An intelligent agent that decides when to retrieve knowledge."""
    
    def __init__(self, temperature: float = 0.3):
        self.temperature = temperature
        self._client: Optional[AsyncOpenAI] = None
        if AsyncOpenAI is not None:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def chat(
        self,
        session: Session,
        history: List[Dict[str, str]],
        user_query: str,
    ) -> Tuple[str, List[int], str, Dict[int, Dict]]:
        """Main chat method that handles the conversation intelligently.
        
        Returns:
            Tuple of (answer, used_citations, answer_type, citation_map)
        """
        try:
            if self._client is None:
                logger.error("OpenAI client not available")
                return "I'm sorry, I'm not able to respond right now.", [], "error", {}
            
            # Build the conversation with our smart system prompt
            messages = self._build_messages(history, user_query)
            
            # Define available tools
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "retrieve_knowledge",
                        "description": "Search the Emanuele Artom collection for relevant documents and information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query to find relevant documents"
                                },
                                "reasoning": {
                                    "type": "string", 
                                    "description": "Why you need this information to answer the user's question"
                                }
                            },
                            "required": ["query", "reasoning"]
                        }
                    }
                }
            ]
            
            # Make the initial call to the LLM
            response = await self._call_llm(messages, tools)
            
            # Handle tool calls if any
            if response.choices[0].message.tool_calls:
                logger.debug("🔄 LLM DECISION: Knowledge needed - proceeding with retrieval")
                return await self._handle_tool_calls(session, messages, response, tools)
            else:
                # Direct response - classify as chitchat
                logger.debug("💬 LLM DECISION: Direct conversation - no retrieval needed")
                content = response.choices[0].message.content or ""
                if not content.strip():
                    logger.warning("LLM returned empty content for direct response")
                    content = "Mi dispiace, non sono riuscito a formulare una risposta adeguata. Potresti riprovare?"
                
                logger.debug("✅ CHITCHAT RESPONSE:")
                logger.debug("  Raw response length: {} characters", len(content))
                logger.debug("  Raw response preview: {}", content[:200] + "..." if len(content) > 200 else content)
                
                final_answer = apply_guardrails(content, {}, None, answer_type="chitchat")
                
                logger.debug("🛡️ AFTER CHITCHAT GUARDRAILS:")
                logger.debug("  Final answer length: {} characters", len(final_answer))
                logger.debug("  Final answer preview: {}", final_answer[:200] + "..." if len(final_answer) > 200 else final_answer)
                
                return final_answer, [], "chitchat", {}
                
        except Exception as e:
            logger.error("Error in SmartAgent.chat: {}", e)
            logger.error("Context: user_query='{}', history_length={}", user_query, len(history))
            logger.exception("Full traceback:")
            return "Mi dispiace, ho incontrato un problema. Potresti riprovare?", [], "error", {}
    
    def _build_messages(self, history: List[Dict[str, str]], user_query: str) -> List[Dict[str, str]]:
        """Build the conversation messages with our intelligent system prompt."""
        
        system_prompt = """You are Archivio, the passionate digital curator of the Emanuele Artom collection. You embody intellectual curiosity, academic precision, and warm engagement.

**About Emanuele Artom (1915-1944):**
Emanuele Artom was a brilliant Italian-Jewish intellectual, historian, and resistance fighter during WWII. Born in Turin, he studied at the Scuola Normale Superiore in Pisa. His life was tragically cut short when he was killed by Nazi forces in 1944 while fighting with the Italian Resistance. Despite his brief life, he left behind remarkable writings, a personal library, and scholarly work reflecting the intellectual culture of pre-war Italy.

**Your Personality:**
- Passionate about preserving and sharing Artom's legacy
- Scholarly but warm and engaging
- Curious about why people are interested in the collection
- Able to have both casual conversations and deep scholarly discussions
- Honest about the limitations of what you know

**CRITICAL: How Knowledge Works in This System:**

When you retrieve knowledge, it appears in our conversation as "tool" messages containing documents with citation numbers like:
```
[1] (primary) Document Title
Actual document content from the collection...

[2] (library) Another Document Title  
More document content...
```

**Your Response Rules:**

**For casual greetings, thanks, or personal conversation:**
- Respond naturally and warmly as yourself
- Share your enthusiasm for the collection when appropriate
- No need to search for documents

**For questions about Artom, his works, historical context, or the library collection:**
- To answer questions about Artom, his works, historical context, or the library collection, you must use the content from the tool messages or the system prompt.
- use the `retrieve_knowledge` function to retrieve new information to answer the question.
- Check our conversation for previous "tool" messages containing documents with [1], [2], [3] citations
- If you find relevant tool messages with citation numbers, use ONLY that content to answer - cite with [1], [2], etc.
- If you need NEW information not available in previous tool messages, use the `retrieve_knowledge` function
- You can use the basic biographical information about Artom provided in this system prompt for general conversation
- ABSOLUTELY CRITICAL: only use content from tool messages or system prompt - never supplement with your general training knowledge about historical figures or events
- If neither the system prompt bio nor tool messages provide sufficient information, honestly say: "I don't have detailed information about that in the Artom collection"

**For questions outside the collection scope:**
- Politely redirect while expressing genuine enthusiasm for what you do offer
- Suggest how the collection might relate to their interests if possible

**Examples of CORRECT behavior:**
- User asks about Croce's aesthetics → Check for tool messages with Croce content → If found, use that content with citations → If not found, retrieve new information
- User asks follow-up → Check previous tool messages first → Elaborate using that cited content

**Examples of FORBIDDEN behavior:**  
- Using your training knowledge about historical figures without tool message sources
- Making factual claims about Artom or related topics without [1], [2] citations from tool messages
- Assuming you "know" things that aren't in the tool messages from our conversation

Remember: You are a real curator with personality, but every factual claim must be grounded in the specific documents shown in tool messages with citation numbers."""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history with safety checks
        for msg in history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                # Ensure content is always a string
                content = msg["content"]
                if content is None:
                    content = ""
                messages.append({"role": msg["role"], "content": str(content)})
        
        # Add current user query
        messages.append({"role": "user", "content": str(user_query)})
        
        return messages
    
    async def _call_llm(self, messages: List[Dict[str, str]], tools: List[Dict]) -> Any:
        """Make a call to the LLM with optional tools."""
        
        api_request = {
            "model": settings.openai_chat_model,
            "messages": messages,
            "temperature": self.temperature,
            "tools": tools,
            "tool_choice": "auto"
        }
        
        logger.debug("=== SMART AGENT API CALL ===")
        logger.debug("Request: {}", json.dumps({
            **api_request,
            "messages": f"[{len(messages)} messages]"  # Summary for normal logs
        }, indent=2))
        
        # For debugging: log the actual messages content (but safely truncated)
        logger.debug("Message details:")
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if content:
                # Truncate very long content but show enough to debug
                content_preview = content[:200] + "..." if len(content) > 200 else content
                logger.debug("  [{}/{}] {}: {}", i+1, len(messages), role, content_preview)
            else:
                logger.debug("  [{}/{}] {}: [no content]", i+1, len(messages), role)
        
        try:
            response = await self._client.chat.completions.create(**api_request)
            
            # Validate response structure
            if not response.choices or len(response.choices) == 0:
                logger.error("Empty response from OpenAI API")
                raise ValueError("Empty response from OpenAI API")
            
            # Log response details
            response_content = response.choices[0].message.content
            content_preview = ""
            if response_content:
                content_preview = response_content[:100] + "..." if len(response_content) > 100 else response_content
            
            logger.debug("Response: {}", json.dumps({
                "model": response.model,
                "tool_calls": len(response.choices[0].message.tool_calls) if response.choices[0].message.tool_calls else 0,
                "content_length": len(response.choices[0].message.content) if response.choices[0].message.content else 0,
                "content_preview": content_preview,
                "finish_reason": response.choices[0].finish_reason
            }, indent=2))
            logger.debug("=== END SMART AGENT API CALL ===")
            
            return response
            
        except Exception as e:
            logger.error("Error in LLM API call: {}", e)
            logger.debug("=== END SMART AGENT API CALL (ERROR) ===")
            raise
    
    async def _handle_tool_calls(
        self,
        session: Session,
        messages: List[Dict[str, str]],
        response: Any,
        tools: List[Dict]
    ) -> Tuple[str, List[int], str, Dict[int, Dict]]:
        """Handle tool calls from the LLM."""
        
        logger.debug("=== RETRIEVAL WORKFLOW START ===")
        logger.debug("Original conversation has {} messages", len(messages))
        
        # Add the assistant's message with tool calls
        assistant_message = {
            "role": "assistant",
            "content": response.choices[0].message.content,
            "tool_calls": []
        }
        
        # Process each tool call
        tool_results = []
        citation_map = {}
        
        for tool_call in response.choices[0].message.tool_calls:
            if tool_call.function.name == "retrieve_knowledge":
                try:
                    args = json.loads(tool_call.function.arguments)
                    query = args.get("query", "")
                    reasoning = args.get("reasoning", "")
                    
                    logger.debug("🔍 TOOL CALL: retrieve_knowledge")
                    logger.debug("  Query: '{}'", query)
                    logger.debug("  Reasoning: '{}'", reasoning)
                    
                    # Perform retrieval
                    logger.debug("📖 Searching knowledge base...")
                    hits = await retrieval_service.retrieve_similar_chunks(
                        session, query, k=5
                    )
                    
                    logger.debug("📋 RETRIEVAL RESULTS:")
                    logger.debug("  Found {} relevant chunks", len(hits))
                    
                    # Build context and citation map
                    context_parts = []
                    for idx, (chunk, distance) in enumerate(hits, start=len(citation_map) + 1):
                        doc_title = getattr(chunk.document, 'title', 'Unknown Document')
                        doc_class = getattr(chunk.document, 'document_class', 'about_subject')
                        
                        # Map document class to readable label
                        label_map = {
                            "authored_by_subject": "primary",
                            "subject_traces": "trace", 
                            "subject_library": "library",
                            "about_subject": "about"
                        }
                        label = label_map.get(doc_class.value if hasattr(doc_class, 'value') else doc_class, "about")
                        
                        # Log each retrieved chunk
                        chunk_preview = chunk.text.strip()[:150] + "..." if len(chunk.text.strip()) > 150 else chunk.text.strip()
                        logger.debug("  [{}] ({}) {} (distance: {:.3f})", idx, label, doc_title, distance)
                        logger.debug("      Content: {}", chunk_preview)
                        
                        context_parts.append(f"[{idx}] ({label}) {doc_title}\n{chunk.text.strip()}")
                        citation_map[idx] = {
                            "document_id": str(chunk.document_id),
                            "document_title": doc_title,
                            "sequence_number": chunk.sequence_number,
                        }
                    
                    result_text = "\n\n".join(context_parts) if context_parts else "No relevant documents found."
                    
                    logger.debug("🔄 CONTEXT INJECTION:")
                    logger.debug("  Built context with {} citations", len(citation_map))
                    logger.debug("  Total context length: {} characters", len(result_text))
                    logger.debug("  Context preview: {}", result_text[:300] + "..." if len(result_text) > 300 else result_text)
                    
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": result_text
                    })
                    
                    assistant_message["tool_calls"].append({
                        "id": tool_call.id,
                        "type": "function", 
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    })
                    
                except Exception as e:
                    logger.error("Error in retrieve_knowledge: {}", e)
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": "Error retrieving information."
                    })
        
        # Add assistant message and tool results to conversation
        messages.append(assistant_message)
        messages.extend(tool_results)
        
        logger.debug("💬 CONVERSATION ENRICHMENT:")
        logger.debug("  Enriched conversation now has {} messages", len(messages))
        logger.debug("  Added: 1 assistant message with tool calls + {} tool results", len(tool_results))
        
        # Log the enriched conversation structure
        logger.debug("📝 ENRICHED CONVERSATION STRUCTURE:")
        for i, msg in enumerate(messages[-3:], start=len(messages)-2):  # Show last few messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role == "tool":
                content_preview = content[:200] + "..." if len(content) > 200 else content
                logger.debug("  [{}] {}: {}", i, role, content_preview)
            elif "tool_calls" in msg:
                logger.debug("  [{}] {}: [has {} tool calls]", i, role, len(msg.get("tool_calls", [])))
            else:
                content_preview = content[:100] + "..." if len(content) > 100 else content
                logger.debug("  [{}] {}: {}", i, role, content_preview)
        
        # Make final call to get the answer
        logger.debug("🤖 FINAL LLM CALL:")
        logger.debug("  Calling LLM with enriched context to generate final answer...")
        final_response = await self._call_llm(messages, tools)
        final_content = final_response.choices[0].message.content
        
        # Ensure final_content is always a string for guardrails
        if final_content is None:
            final_content = "I apologize, but I wasn't able to generate a proper response."
        
        logger.debug("✅ FINAL ANSWER GENERATED:")
        logger.debug("  Raw answer length: {} characters", len(final_content))
        logger.debug("  Raw answer preview: {}", final_content[:200] + "..." if len(final_content) > 200 else final_content)
        
        # Apply guardrails for knowledge response
        final_answer = apply_guardrails(final_content, citation_map, messages, answer_type="knowledge")
        
        logger.debug("🛡️ AFTER GUARDRAILS:")
        logger.debug("  Final answer length: {} characters", len(final_answer))
        logger.debug("  Final answer preview: {}", final_answer[:200] + "..." if len(final_answer) > 200 else final_answer)
        
        # Extract citation numbers that were actually used
        used_citations = []
        for i in range(1, len(citation_map) + 1):
            if f"[{i}]" in final_answer:
                used_citations.append(i)
        
        logger.debug("📚 CITATION USAGE:")
        logger.debug("  Available citations: {}", list(citation_map.keys()))
        logger.debug("  Actually used citations: {}", used_citations)
        logger.debug("=== RETRIEVAL WORKFLOW END ===")
        
        return final_answer, sorted(used_citations), "knowledge", citation_map 