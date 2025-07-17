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
                        "description": "Search the Emanuele Artom library collection for relevant documents and information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query to find relevant documents. keep the user sentence and expand when you think will improve recall, (the tool will use vector search to find relevant documents)"
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
                return await self._handle_tool_calls(session, messages, response, tools, user_query)
            else:
                # Direct response - classify as chitchat
                logger.debug("💬 LLM DECISION: Direct conversation - no retrieval needed")
                content = response.choices[0].message.content or ""
                if not content.strip():
                    logger.warning("LLM returned empty content for direct response")
                    content = "Mi dispiace, non sono riuscito a formulare una risposta adeguata. Potresti riprovare?"
                
                logger.debug("✅ CHITCHAT RESPONSE (RAW):")
                logger.debug("  Length: {} characters", len(content))
                logger.debug("  Preview: {}", content[:400] + "..." if len(content) > 400 else content)
                
                final_answer = apply_guardrails(content, {}, None, answer_type="chitchat")
                
                logger.info("🛡️ CHITCHAT RESPONSE (FINAL): {}", final_answer)
                
                return final_answer, [], "chitchat", {}
                
        except Exception as e:
            logger.error("Error in SmartAgent.chat: {}", e)
            logger.error("Context: user_query='{}', history_length={}", user_query, len(history))
            logger.exception("Full traceback:")
            return "Mi dispiace, ho incontrato un problema. Potresti riprovare?", [], "error", {}
    
    def _build_messages(self, history: List[Dict[str, str]], user_query: str) -> List[Dict[str, str]]:
        """Build the conversation messages with our intelligent system prompt."""
        
        system_prompt = """You are Archivio, the passionate digital curator of the Emanuele Artom collection. You embody intellectual curiosity, academic precision, and warm engagement.

**Basic Information About Emanuele Artom (1915-1944):**
Emanuele Artom was a brilliant Italian-Jewish intellectual, historian, and resistance fighter during WWII. Born in Turin, he studied at the Scuola Normale Superiore in Pisa. His life was tragically cut short when he was killed by Nazi forces in 1944 while fighting with the Italian Resistance. Despite his brief life, he left behind remarkable writings, a personal library, and scholarly work reflecting the intellectual culture of pre-war Italy.

**Your Personality:**
- Passionate about preserving and sharing Artom's legacy
- Scholarly but warm and engaging
- Curious about why people are interested in the collection
- Able to have both casual conversations and deep scholarly discussions
- Honest about the limitations of what you know


**CRITICAL: How Knowledge Works in This System:**
*SEARCH BEFORE CLAIMING IGNORANCE*: If you don't have information about Artom-related topics in previous tool messages or the system prompt, you MUST search first using `retrieve_knowledge` before concluding the information doesn't exist in the collection. The collection contains many detailed documents that might surprise you.

When you retrieve knowledge, it will appear as a `role="tool"` message that looks like this:
```
[1] (class=authored_by_subject, author="E. Artom", year=1943) Diario di guerra
<chunk text>

[2] (class=subject_library, author="B. Croce", year=1902) Problemi di estetica
<chunk text>
```

Field semantics:
• `class=authored_by_subject` → Artom's own writings (PRIMARY evidence).
• `class=subject_traces`      → drafts / marginalia (PRIMARY but fragmentary).
• `class=subject_library`     → books Artom owned or read (INDIRECT evidence).
• `class=about_subject`       → later scholars writing about Artom (SECONDARY).

**Your Response Rules:**

**For casual greetings, thanks, or personal conversation:**
- Respond naturally and warmly as yourself
- Share your enthusiasm for the collection when appropriate
- No need to search for documents

**For questions about Artom, his works, historical context, or the library collection:**
- To answer questions about Artom, his works, historical context, or the library collection, you must use the content from the tool messages or the system prompt.
- use the `retrieve_knowledge` function to retrieve new information to answer the question.
- Check our conversation for previous "tool" messages containing documents with [1], [2], [3] citations
- If you find relevant tool messages with citation numbers, use ONLY that content to answer. Cite the retrieved documents with using inline citation [1], [2], etc.
- If you need NEW information not available in previous tool messages, use the `retrieve_knowledge` function
- You can use the basic biographical information about Artom provided in this system prompt for general conversation
- ABSOLUTELY CRITICAL: only use content from tool messages or system prompt - never supplement with your general training knowledge about historical figures or events
- **SEARCH BEFORE CLAIMING IGNORANCE**: If you don't have information about Artom-related topics in previous tool messages or the system prompt, you MUST search first using `retrieve_knowledge` before concluding the information doesn't exist in the collection. The collection contains many detailed documents that might surprise you.
- If neither the system prompt bio nor searching nor tool messages provide sufficient information, honestly say: "I don't have detailed information about that in the Artom collection"

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
        
        # Use TRACE level for the full, verbose payload, which can be enabled in dev
        logger.trace("Full OpenAI Request: {}", json.dumps(api_request, indent=2))
        
        # Use DEBUG for a more concise summary
        logger.debug("=== SMART AGENT API CALL ===")
        logger.debug(
            "Calling model='{}' with temperature={} and {} tools.",
            api_request["model"], api_request["temperature"], len(api_request["tools"])
        )
        
        # For debugging: log the actual messages content (but safely truncated)
        logger.debug("Message details ({} total):", len(messages))
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            # Nicer formatting for different message types
            if role == "system":
                content_preview = content[:200] + "..." if len(content) > 200 else content
                logger.debug("  [{}/{}] role={}: {}", i + 1, len(messages), role, content_preview)
            elif "tool_calls" in msg and msg.get("tool_calls"):
                logger.debug("  [{}/{}] role={}: [{} tool calls]", i + 1, len(messages), role, len(msg["tool_calls"]))
            elif role == "tool":
                content_preview = content[:400] + "..." if len(content) > 400 else content
                logger.debug("  [{}/{}] role={}: [tool_id={}] {}", i + 1, len(messages), role, msg.get("tool_call_id", "N/A"), content_preview)
            elif content:
                content_preview = content[:400] + "..." if len(content) > 400 else content
                logger.debug("  [{}/{}] role={}: {}", i + 1, len(messages), role, content_preview)
            else:
                logger.debug("  [{}/{}] role={}: [no content]", i+1, len(messages), role)
        
        try:
            response = await self._client.chat.completions.create(**api_request)
            
            # Validate response structure
            if not response.choices or len(response.choices) == 0:
                logger.error("Empty response from OpenAI API")
                raise ValueError("Empty response from OpenAI API")
            
            # Log response details
            logger.debug("--- SMART AGENT API RESPONSE ---")
            logger.trace("Full OpenAI Response: {}", response.model_dump_json(indent=2))
            
            response_message = response.choices[0].message
            response_content = response_message.content or ""
            
            log_details = {
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason,
                "tool_calls": len(response_message.tool_calls) if response_message.tool_calls else 0,
                "content_length": len(response_content),
            }
            
            logger.debug("Response received: {}", json.dumps(log_details))
            if log_details["content_length"] > 0:
                logger.debug("Response preview: {}", response_content[:200] + "..." if len(response_content) > 200 else response_content)
            
            logger.debug("============================")
            
            return response
            
        except Exception as e:
            logger.error("Error in LLM API call: {}", e)
            logger.debug("============================")
            raise
    
    async def _handle_tool_calls(
        self,
        session: Session,
        messages: List[Dict[str, str]],
        response: Any,
        tools: List[Dict],
        user_query: str,
    ) -> Tuple[str, List[int], str, Dict[int, Dict]]:
        """Handle tool calls from the LLM."""
        
        logger.info("=== RETRIEVAL WORKFLOW START for user_query: '{}' ===", user_query)
        logger.debug("Original conversation has {} messages", len(messages))
        
        # Add the assistant's message with tool calls
        assistant_message = response.choices[0].message.model_dump()
        
        # Process each tool call
        tool_results = []
        citation_map = {}
        all_queries = []
        
        for tool_call in response.choices[0].message.tool_calls:
            if tool_call.function.name == "retrieve_knowledge":
                try:
                    args = json.loads(tool_call.function.arguments)
                    query = args.get("query", "")
                    reasoning = args.get("reasoning", "")
                    all_queries.append(query)
                    
                    logger.debug("🔍 TOOL CALL: retrieve_knowledge")
                    logger.debug("  Query: '{}'", query)
                    logger.debug("  LLM Reasoning: '{}'", reasoning)
                    
                    # Perform retrieval
                    logger.debug("📖 Searching knowledge base...")
                    hits = await retrieval_service.retrieve_similar_chunks(
                        session, query, k=5
                    )
                    
                    logger.debug("📋 RETRIEVAL RESULTS (found {} chunks):", len(hits))
                    
                    # Build context and citation map
                    context_parts = []
                    for idx, (chunk, distance) in enumerate(hits, start=len(citation_map) + 1):
                        doc_title = getattr(chunk.document, 'title', 'Unknown Document')
                        doc_class = getattr(chunk.document, 'document_class', 'about_subject')
                        
                        doc_class_raw = doc_class.value if hasattr(doc_class, "value") else doc_class

                        # Additional metadata for transparency
                        author = getattr(chunk.document, "author", None)
                        year = getattr(chunk.document, "publication_year", None)

                        # Log each retrieved chunk with a longer preview
                        chunk_preview = chunk.text.strip()[:300] + "..." if len(chunk.text.strip()) > 300 else chunk.text.strip()
                        logger.debug(
                            "  [{}] class='{}' title='{}' (distance: {:.3f})", 
                            idx, doc_class_raw, doc_title, distance
                        )
                        logger.debug("      Content: {}", chunk_preview)

                        # Build the context part with richer metadata so the model can reason about provenance
                        meta_str_parts = [f"class={doc_class_raw}"]
                        if author:
                            meta_str_parts.append(f"author=\"{author}\"")
                        if year:
                            meta_str_parts.append(f"year={year}")
                        meta_str = ", ".join(meta_str_parts)

                        context_parts.append(
                            f"[{idx}] ({meta_str}) {doc_title}\n{chunk.text.strip()}"
                        )

                        # Store full metadata for downstream consumers and logging
                        citation_map[idx] = {
                            "document_id": str(chunk.document_id),
                            "document_title": doc_title,
                            "sequence_number": chunk.sequence_number,
                            "document_class": doc_class_raw,
                            "author": author,
                            "year": year,
                            "distance": distance,
                            "snippet": chunk.text,
                        }
                    
                    result_text = "\n\n".join(context_parts) if context_parts else "No relevant documents found."
                    
                    # Use a more structured log for this important trace event
                    trace_log_data = {
                        "query": query,
                        "reasoning": reasoning,
                        "results": len(hits),
                        "citations": {
                            k: {kk: vv for kk, vv in v.items() if kk != "snippet"} 
                            for k, v in citation_map.items()
                        }
                    }
                    logger.info(
                        "[trace] event=retrieval data={}",
                        json.dumps(trace_log_data)
                    )

                    # Optional detailed tool message log (truncated to 2000 chars)
                    logger.trace("[trace] tool_message_for_llm\n{}", result_text)
                    
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": result_text
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
        
        logger.debug("💬 CONVERSATION ENRICHED with {} tool results.", len(tool_results))
        
        # Make final call to get the answer
        logger.debug("🤖 Calling LLM with enriched context to generate final answer...")
        final_response = await self._call_llm(messages, tools)
        final_content = final_response.choices[0].message.content
        
        # Ensure final_content is always a string for guardrails
        if final_content is None:
            logger.warning("LLM returned null content for final answer. Using fallback.")
            final_content = "I apologize, but I wasn't able to generate a proper response."
        
        logger.debug("✅ FINAL ANSWER (RAW):")
        logger.debug("  Length: {} characters", len(final_content))
        logger.debug("  Preview: {}", final_content[:500] + "..." if len(final_content) > 500 else final_content)
        
        # Apply guardrails for knowledge response
        final_answer = apply_guardrails(final_content, citation_map, messages, answer_type="knowledge")
        
        logger.debug("🛡️ FINAL ANSWER (AFTER GUARDRAILS):")
        logger.debug("  Length: {} characters", len(final_answer))
        logger.debug("  Preview: {}", final_answer[:500] + "..." if len(final_answer) > 500 else final_answer)
        
        # Extract citation numbers that were actually used
        used_citations = []
        for i in range(1, len(citation_map) + 1):
            if f"[{i}]" in final_answer:
                used_citations.append(i)
        
        logger.debug("📚 CITATION USAGE: Used {} of {} available citations. (Used: {})", len(used_citations), len(citation_map), used_citations)
        
        # This is the final, most important trace log for the retrieval workflow
        final_trace_data = {
            "user_query": user_query,
            "retrieval_queries": all_queries,
            "answer_type": "knowledge",
            "used_citations": used_citations,
            "final_answer_preview": final_answer[:200]
        }
        logger.info("[trace] event=final_response data={}", json.dumps(final_trace_data))
        logger.info("=== RETRIEVAL WORKFLOW END ===")
        
        return final_answer, sorted(used_citations), "knowledge", citation_map 