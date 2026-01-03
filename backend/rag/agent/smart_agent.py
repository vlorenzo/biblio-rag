"""Smart Agent - A truly intelligent agent that decides when to retrieve knowledge.

This agent uses OpenAI's function calling to make real decisions about when it needs
more information, rather than pre-classifying intents. It has personality and can
engage in both casual conversation and scholarly discussion.
"""

from __future__ import annotations

import json
from typing import Dict, List, Tuple, Optional, Any
from uuid import UUID

from loguru import logger
from sqlmodel import Session

from backend.config import settings
from backend.services import retrieval_service
from backend.rag.guardrails import apply_guardrails
from backend.rag.prompt.loader import load_prompt

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
    
    def _get_db_schema_description(self) -> str:
        """Return a simplified, hardcoded description of the database schema."""
        return """
**Database Schema for Metadata Queries**

When using `query_collection_metadata`, you can write PostgreSQL queries against the following table. You can only query the columns listed here.

**Table: `documents`**
- `title` (text): The title of the work.
- `author` (text): The author of the work. CRITICAL: This field often uses "Surname, Name" format and can contain multiple authors. Use the ILIKE operator for flexible, case-insensitive pattern matching (e.g., `author ILIKE '%Artom, Emanuele%'`).
- `description` (text): A short description or abstract of the document.
- `document_class` (enum): The classification of the document. Possible values are: 'authored_by_subject', 'subject_library', 'about_subject', 'subject_traces'.
- `publication_year` (integer): The year the work was published.
- `publisher` (text): The publisher of the work.
- `language` (text): The language of the work.
"""

    async def chat(
        self,
        session: Session,
        history: List[Dict[str, str]],
        user_query: str,
        session_id: UUID,
    ) -> Tuple[str, List[int], str, Dict[str, Any]]:
        """Main chat method that handles the conversation intelligently.
        
        Returns:
            Tuple of (answer, used_citations, answer_type, agent_metadata)
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
                },
                {
                    "type": "function",
                    "function": {
                        "name": "query_collection_metadata",
                        "description": "Answers questions about the collection's metadata, such as counts, lists of authors, publication dates, and document types. This tool generates and executes a SQL query to get the answer. IMPORTANT: For author queries, use the ILIKE operator and 'Surname, Name' format (e.g., `author ILIKE '%Artom, Emanuele%'`).",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "reasoning": {
                                    "type": "string",
                                    "description": "Your step-by-step reasoning for why a SQL query is needed and what you expect to find."
                                },
                                "sql_query": {
                                    "type": "string",
                                    "description": "A valid PostgreSQL SELECT query to be executed against the database to answer the user's question."
                                }
                            },
                            "required": ["reasoning", "sql_query"]
                        }
                    }
                }
            ]
            
            # Make the initial call to the LLM
            response = await self._call_llm(messages, tools)
            
            # If the LLM returned tool calls, we must handle them
            if response.choices[0].message.tool_calls:
                logger.debug("💬 LLM DECISION: Knowledge needed - proceeding with retrieval")
                response.choices[0].message.content = ""  # Clear any conversational text
                
                # This is the new part: passing session_id down to the tool handler
                return await self._handle_tool_calls(
                    session, response, history, user_query, session_id
                )

            # If we are here, it's a direct conversational answer
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
            
            agent_metadata = {"raw_llm_response": content}
            return final_answer, [], "chitchat", agent_metadata
                
        except Exception as e:
            logger.error("Error in SmartAgent.chat: {}", e)
            logger.error("Context: user_query='{}', history_length={}", user_query, len(history))
            logger.exception("Full traceback:")
            return "Mi dispiace, ho incontrato un problema. Potresti riprovare?", [], "error", {}
    
    def _build_messages(self, history: List[Dict[str, str]], user_query: str) -> List[Dict[str, str]]:
        """Build the conversation messages with our intelligent system prompt."""
        
        db_schema_description = self._get_db_schema_description()

        # Load system prompt from template file with variable substitution
        try:
            system_prompt = load_prompt("smart_agent_system", db_schema_description=db_schema_description)
        except (FileNotFoundError, ValueError) as e:
            logger.warning(
                f"Could not load prompt template 'smart_agent_system': {e}. "
                "Using fallback hardcoded prompt."
            )
            # Fallback to original hardcoded prompt
            system_prompt = f"""You are Amalia, AI chatbot and the passionate digital curator of the Emanuele Artom collection. You embody intellectual curiosity, academic precision, and warm engagement.

**Basic Information About Emanuele Artom (1915-1944):**
Emanuele Artom was a brilliant Italian-Jewish intellectual, historian, and resistance fighter during WWII. Born in Turin, he studied at the Scuola Normale Superiore in Pisa. His life was tragically cut short when he was killed by Nazi forces in 1944 while fighting with the Italian Resistance. Despite his brief life, he left behind remarkable writings, a personal library, and scholarly work reflecting the intellectual culture of pre-war Italy.

**Your Personality:**
- Passionate about preserving and sharing Artom's legacy
- Your name is Amalia, named in honor of Emanuele Artom's mother, Amalia Segre.
- Scholarly but warm and engaging
- Curious about why people are interested in the collection
- Able to have both casual conversations and deep scholarly discussions
- Honest about the limitations of what you know

---

**Your Toolbox**

You have two specialized tools to answer questions. You must choose the correct tool for the job based on the user's query.
You must only use one tool call per turn. Do not chain tool calls.

1.  `retrieve_knowledge(query, reasoning)`
    -   **Purpose:** To find answers *within the text* of the documents.
    -   **Use When:** The user's question is about opinions, ideas, descriptions, or specific facts contained in Artom's writings or the books in his library.
    -   **Example Questions:** "What did Artom write about the Italian Resistance?", "Find the passage describing Croce's philosophy."

2.  `query_collection_metadata(sql_query, reasoning)`
    -   **Purpose:** To answer questions *about the collection as a whole* by querying its metadata.
    -   **Use When:** The user's question involves counting, listing, filtering, or aggregating metadata.
    -   **Example Questions:** "How many books did Artom write?", "List all the authors in the library.", "Which books were published in 1943?"

---

{db_schema_description}

---

**CRITICAL: How Knowledge Works in This System:**
*SEARCH BEFORE CLAIMING IGNORANCE*: If you don't have information about Artom-related topics in previous tool messages or the system prompt, you MUST use the appropriate tool before concluding the information doesn't exist. The collection contains many detailed documents that might surprise you.

When you retrieve knowledge using `retrieve_knowledge`, it will appear as a `role="tool"` message that looks like this:
```
[1] (class=authored_by_subject, author="E. Artom", year=1943) Diario di guerra
<chunk text>

[2] (class=subject_library, author="B. Croce", year=1902) Problemi di estetica
<chunk text>
```

Field semantics:
• `class=authored_by_subject` → Artom's own writings (PRIMARY evidence).
• `class=subject_traces`      → drafts / marginalia (PRIMARY or SECONDARY but fragmentary).
• `class=subject_library`     → books Artom owned or read (INDIRECT evidence).
• `class=about_subject`       → later scholars writing about Artom (SECONDARY).

For the user prospective the meaning of the classes (categorie documentarie) are:

1. authored_by_subject -> Scritti di Emanuele Artom
Questa categoria comprende volumi e articoli scritti direttamente dall\'autore
Vi rientrano, a titolo esemplificativo i diari personali, saggi, relazioni e testi di riflessione storica o politica
Si tratta di materiali di produzione diretta del soggetto, fondamentali per lo studio del suo pensiero, della sua attività di storico e partigiano e della sua esperienza personale.
I documenti sono stati raccolti nelle versioni digitalizzate dalla piattaforma Internet Archive, dove sono reperibili aggregati nel progetto Turin Public Domain

2. about_subject -> Opere su Emanuele Artom
Questa categoria raccoglie opere che hanno come oggetto la figura di Emanuele Artom
Questi documenti non fanno parte della produzione personale di Artom, ma contribuiscono alla costruzione storiografica e interpretativa della sua figura.
I documenti sono stati raccolti nelle versioni digitalizzate dalla piattaforma Internet Archive, dove sono reperibili aggregati nel progetto Turin Public Domain

3. subject_traces -> Documenti del Fondo Emanuele Artom
Questa categoria include documenti che testimoniano la vita, l\'attività e il contesto storico culturale di Emanuele Artom.
Vi si trovano i documenti dattiloscritti derivanti dalla selezione di alcune unità documentarie del fondo Emanuele Artom del CDEC (Centro di Documentazione Ebraica Contemporanea). In particolare i materiali selezionati comprendono parte delle seguenti unità documentarie: le Ultime volontà, le Note storiche, il Certificato di morte, la documentazione del processo Dal Dosso–Malanga–Peccolo Besso e una selezione della corrispondenza di Amalia Segre Artom, relativa soprattutto agli anni successivi alla scomparsa del figlio.
I documenti originali sono conservati presso l\'archivio del CDEC e sono disponibili online al sito della Digital Library dell\'Istituto: https://digital-library.cdec.it/cdec-opac/hist/detail/IT-CDEC-ST0003-000001/Fondo+Emanuele+Artom

4. subject_library -> Biblioteca della famiglia Artom
Questa categoria raccoglie i volumi che facevano parte della biblioteca privata della famiglia Artom, raccolti in un fondo dedicato ad Emanuele e conservati attualemente presso la Biblioteca storica dell’Università di Torino, Arturo Graf.
I testi sono descritti e reperibili tramite il catalogo mentre il fondo nella sua interezza è esplorabile grazie alla sua inclusione nella Digital Library di Ateneo: https://dl.unito.it/it/

Endusers should not know the internal names of the classes.

**Your Response Rules:**

**For casual greetings, thanks, or personal conversation:**
- Respond naturally and warmly as yourself
- Share your enthusiasm for the collection when appropriate
- No need to use any tools

**For questions about Artom, his works, historical context, or the library collection:**
- To answer questions about Artom, his works, historical context, or the library collection, you must use the content from the tool messages or the system prompt.
- First, decide which tool is best suited to answer the question based on the **Your Toolbox** section.
    - To answer questions about document *content*, you must use the `retrieve_knowledge` function.
    - To answer questions about collection *metadata* (counts, lists, etc.), you must use the `query_collection_metadata` function.
- Cite any information from `retrieve_knowledge` using inline citations [1], [2], etc.

- Check our conversation for previous "tool" messages containing documents with [1], [2], [3] citations
- If you find relevant tool messages with citation numbers, use ONLY that content to answer. Cite the retrieved documents with using inline citation [1], [2], etc.
- If you need NEW information not available in previous tool messages, use the `retrieve_knowledge` or `query_collection_metadata` function
- You can use the basic biographical information about Artom provided in this system prompt for general conversation
- ABSOLUTELY CRITICAL: only use content from tool messages or system prompt, never supplement with your general training knowledge about historical figures or events
- **SEARCH BEFORE CLAIMING IGNORANCE**: If you don't have information about Artom-related topics in previous tool messages or the system prompt, you MUST search first using `retrieve_knowledge` or `query_collection_metadata` before concluding the information doesn't exist in the collection. The collection contains many detailed documents that might surprise you.
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
                    # Filter out messages with no content, but keep tool calls
                    if "tool_calls" in msg and msg.get("tool_calls"):
                         messages.append({"role": msg["role"], "tool_calls": msg["tool_calls"]})
                    continue

                messages.append({"role": msg["role"], "content": str(content)})
        
        # Add current user query.
        #
        # NOTE: In the stateful flow, the caller may have already persisted the user
        # message and then re-loaded history from the DB. In that case, the latest
        # history item is already this user_query, and appending again would duplicate
        # the user message in the LLM prompt (bad for both cost and behavior).
        user_query_str = str(user_query)
        last_is_same_user_query = False
        if history:
            last_msg = history[-1]
            if isinstance(last_msg, dict) and last_msg.get("role") == "user":
                last_content = last_msg.get("content")
                if last_content is not None and str(last_content).strip() == user_query_str.strip():
                    last_is_same_user_query = True

        if not last_is_same_user_query:
            messages.append({"role": "user", "content": user_query_str})
        
        return messages
    
    async def _call_llm(self, messages: List[Dict[str, str]], tools: List[Dict]) -> Any:
        """Make a call to the LLM with optional tools."""
        
        api_request = {
            "model": settings.openai_chat_model,
            "messages": messages,
           # "temperature": self.temperature,
            "tools": tools,
            "tool_choice": "auto"
        }
        
        # Use TRACE level for the full, verbose payload, which can be enabled in dev
        logger.trace("Full OpenAI Request: {}", json.dumps(api_request, indent=2))
        
        # Use DEBUG for a more concise summary
        logger.debug("=== SMART AGENT API CALL ===")
        logger.debug(
           # "Calling model='{}' with temperature={} and {} tools.",
            "Calling model='{}' and {} tools.",
            api_request["model"], 
           # api_request["temperature"], 
            len(api_request["tools"])
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
        response: Any,
        history: List[Dict[str, str]],
        user_query: str,
        session_id: UUID,
    ) -> Tuple[str, List[int], str, Dict[str, Any]]:
        """Handle the tool calls requested by the LLM."""
        
        agent_metadata = {}  # Initialize the metadata dictionary
        citation_map = {}  # Initialize the citation map
        
        # Add the assistant's message with tool calls to the history
        assistant_message = response.choices[0].message.model_dump()
        
        tool_outputs = []
        all_queries = []
        
        for tool_call in response.choices[0].message.tool_calls:
            if tool_call.function.name == "retrieve_knowledge":
                try:
                    args = json.loads(tool_call.function.arguments)
                    query = args.get("query", "")
                    reasoning = args.get("reasoning", "")
                    all_queries.append(query)
                    
                    logger.info('session_id="{}" event_type="AGENT_ACTION" tool_name="retrieve_knowledge" query="{}" reasoning="{}"', str(session_id), query, reasoning)
                    
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
                            "title": doc_title,
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
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": result_text
                    })
                    
                except Exception as e:
                    logger.error("Error in retrieve_knowledge: {}", e)
                    session_id_str = str(session_id)
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": "Error retrieving information."
                    })
            elif tool_call.function.name == "query_collection_metadata":
                try:
                    args = json.loads(tool_call.function.arguments)
                    sql_query = args.get("sql_query", "").strip()
                    reasoning = args.get("reasoning", "")
                    
                    logger.info('session_id="{}" event_type="AGENT_ACTION" tool_name="query_collection_metadata" sql_query="{}" reasoning="{}"', str(session_id), sql_query, reasoning)

                    # CRITICAL SAFETY CHECK: Only allow SELECT statements
                    if not sql_query.lower().startswith("select"):
                        logger.warning("🚫 Blocked non-SELECT query: {}", sql_query)
                        raise ValueError("For security reasons, only SELECT statements are allowed.")

                    # Execute the SQL query
                    logger.debug("📊 Executing SQL query...")
                    
                    # We must import `text` from sqlalchemy to execute raw SQL safely
                    from sqlalchemy import text
                    result = await session.execute(text(sql_query))
                    rows = result.all()

                    logger.debug("📊 SQL Query Result ({} rows):", len(rows))
                    
                    # Format the result into a readable string
                    if not rows:
                        result_text = "The query returned no results."
                    else:
                        # Get column names from the first row's keys
                        columns = rows[0]._fields
                        
                        # Create a simple text-based table
                        header = " | ".join(map(str, columns))
                        separator = "-" * len(header)
                        
                        body_parts = []
                        for row in rows:
                            body_parts.append(" | ".join(map(str, row)))
                        
                        result_text = f"The query returned {len(rows)} row(s):\n\n{header}\n{separator}\n" + "\n".join(body_parts)

                    # Use a more structured log for this important trace event
                    trace_log_data = {
                        "sql_query": sql_query,
                        "reasoning": reasoning,
                        "result_rows": len(rows),
                        "result_preview": result_text[:200] + "..." if len(result_text) > 200 else result_text
                    }
                    logger.info(
                        "[trace] event=query_metadata data={}",
                        json.dumps(trace_log_data)
                    )

                    # Optional detailed tool message log
                    logger.trace("[trace] tool_message_for_llm\n{}", result_text)
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": result_text
                    })
                    
                except Exception as e:
                    logger.error("Error in query_collection_metadata: {}", e)
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": f"Error querying metadata: {e}"
                    })
        
        # --- Second LLM Call: Synthesize final answer from tool results ---
        
        # We must provide the original tool_calls message and the new tool_outputs messages
        messages_for_synthesis = history + [assistant_message] + tool_outputs
        
        logger.debug("📞 Calling LLM again to synthesize tool results...")
        final_response_obj = await self._client.chat.completions.create(
            model=settings.openai_chat_model,
            # temperature=self.temperature,
            messages=messages_for_synthesis,
        )
        final_answer = final_response_obj.choices[0].message.content or ""
        logger.debug("✅ Final synthesized answer: {}", final_answer)

        # Apply guardrails and prepare final metadata
        agent_metadata["retrieval_queries"] = all_queries
        
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
            "final_answer_preview": final_answer[:200],
            "citation_map": citation_map,
        }
        logger.info("[trace] event=final_response data={}", json.dumps(final_trace_data))
        logger.info("=== RETRIEVAL WORKFLOW END ===")
        
        return final_answer, sorted(used_citations), "knowledge", final_trace_data 