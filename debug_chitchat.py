#!/usr/bin/env python3
"""Debug script to test chitchat functionality."""

import asyncio
import os
from backend.rag.intent import classify_intent
from backend.rag.agent import ReActAgent
from backend.rag.prompt import PromptBuilder
from backend.rag.schemas import ChatMessage, Role

async def debug_chitchat():
    """Debug chitchat flow."""
    user_query = "Hello!"
    
    print(f"🔍 Testing query: '{user_query}'")
    
    # Test intent classification
    print("\n1. Intent Classification:")
    intent = await classify_intent(user_query)
    print(f"   Intent: {intent}")
    
    # Test prompt building (no retrieval for chitchat)
    print("\n2. Prompt Building:")
    pb = PromptBuilder()
    history = []
    hits = []  # No retrieval for chitchat
    system_prompt, messages, citation_map = pb.build(history, user_query, hits)
    
    print(f"   Messages count: {len(messages)}")
    print(f"   System prompt (first 200 chars): {system_prompt[:200]}...")
    print(f"   Last message: {messages[-1] if messages else 'None'}")
    
    # Test ReAct agent
    print("\n3. ReAct Agent:")
    agent = ReActAgent()
    answer, used_citations, answer_type = await agent.run(messages, citation_map)
    
    print(f"   Answer: {answer}")
    print(f"   Citations: {used_citations}")
    print(f"   Answer type: {answer_type}")

if __name__ == "__main__":
    asyncio.run(debug_chitchat()) 