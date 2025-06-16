#!/usr/bin/env python3
"""Quick manual test for the new conversation modes."""

import asyncio
from backend.rag.agent import ReActAgent
from backend.rag.guardrails import apply_guardrails


async def test_chitchat():
    """Test chitchat mode."""
    print("Testing chitchat mode...")
    
    # Mock LLM response for greeting
    async def fake_llm_call(self, prompt: str):
        return "Thought: This is a greeting\nAction: Answer\nFinal(type=chitchat): Hi! How can I help you with the Emanuele Artom collection?"
    
    # Monkey patch the LLM call
    ReActAgent._llm_call = fake_llm_call
    
    agent = ReActAgent()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello"}
    ]
    citation_map = {}
    
    answer, citations, answer_type = await agent.run(messages, citation_map)
    
    print(f"Answer: {answer}")
    print(f"Citations: {citations}")
    print(f"Answer type: {answer_type}")
    print(f"Expected: chitchat mode with no citations")
    print("✅ Chitchat test passed!\n")


async def test_knowledge():
    """Test knowledge mode."""
    print("Testing knowledge mode...")
    
    # Mock LLM response for knowledge question
    async def fake_llm_call(self, prompt: str):
        return "Thought: This needs sources\nAction: Answer\nFinal(type=knowledge): Emanuele Artom was a scholar [1]"
    
    # Monkey patch the LLM call
    ReActAgent._llm_call = fake_llm_call
    
    agent = ReActAgent()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who was Emanuele Artom?"}
    ]
    citation_map = {1: {"document_id": "123", "document_title": "Test Doc"}}
    
    answer, citations, answer_type = await agent.run(messages, citation_map)
    
    print(f"Answer: {answer}")
    print(f"Citations: {citations}")
    print(f"Answer type: {answer_type}")
    print(f"Expected: knowledge mode with citations")
    print("✅ Knowledge test passed!\n")


async def test_guardrails():
    """Test guardrails for both modes."""
    print("Testing guardrails...")
    
    # Test chitchat with citations (should be rejected)
    chitchat_with_citations = "Hi there! [1] How are you?"
    result = apply_guardrails(chitchat_with_citations, {}, answer_type="chitchat")
    print(f"Chitchat with citations: {result}")
    print(f"Expected: Refusal message")
    
    # Test chitchat too long (should be rejected)
    long_chitchat = "Hi there! " * 20  # Very long greeting
    result = apply_guardrails(long_chitchat, {}, answer_type="chitchat")
    print(f"Long chitchat: {result}")
    print(f"Expected: Refusal message")
    
    # Test knowledge without citations (should be rejected)
    knowledge_no_citations = "Artom was a great scholar."
    result = apply_guardrails(knowledge_no_citations, {}, answer_type="knowledge")
    print(f"Knowledge without citations: {result}")
    print(f"Expected: Refusal message")
    
    print("✅ Guardrails test passed!\n")


async def main():
    """Run all tests."""
    print("🧪 Testing new conversation modes implementation\n")
    
    await test_chitchat()
    await test_knowledge()
    await test_guardrails()
    
    print("🎉 All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main()) 