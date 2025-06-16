#!/usr/bin/env python3
"""Test script for the new SmartAgent."""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock
from backend.rag.agent import SmartAgent


async def test_chitchat():
    """Test chitchat functionality."""
    print("🗣️  Testing chitchat...")
    
    # Create a mock LLM response that doesn't call tools
    class MockResponse:
        def __init__(self):
            self.choices = [MagicMock()]
            self.choices[0].message.tool_calls = None
            self.choices[0].message.content = "Hello! It's wonderful to connect with you. I'm Archivio, the digital curator of the remarkable Emanuele Artom collection. How can I assist you today in exploring his fascinating intellectual legacy?"
            self.model = "gpt-4"
            self.choices[0].finish_reason = "stop"
    
    # Mock the OpenAI client
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = MockResponse()
    
    agent = SmartAgent()
    agent._client = mock_client
    
    # Test with greeting
    session = MagicMock()  # Mock database session
    history = []
    user_query = "Hello!"
    
    answer, citations, answer_type, citation_map = await agent.chat(session, history, user_query)
    
    print(f"   Answer: {answer[:100]}...")
    print(f"   Answer type: {answer_type}")
    print(f"   Citations: {citations}")
    print(f"   ✅ Expected chitchat mode with personality")
    print()


async def test_knowledge_request():
    """Test knowledge request functionality."""
    print("📚 Testing knowledge request...")
    
    # Create mock responses for tool calling scenario
    class MockToolCallResponse:
        def __init__(self):
            self.choices = [MagicMock()]
            # First response: agent decides to call retrieve_knowledge tool
            self.choices[0].message.tool_calls = [MagicMock()]
            self.choices[0].message.tool_calls[0].id = "call_123"
            self.choices[0].message.tool_calls[0].function.name = "retrieve_knowledge"
            self.choices[0].message.tool_calls[0].function.arguments = '{"query": "Emanuele Artom biography", "reasoning": "User is asking about who Artom was"}'
            self.choices[0].message.content = "I'll search for information about Emanuele Artom."
            self.model = "gpt-4"
            self.choices[0].finish_reason = "tool_calls"
    
    class MockFinalResponse:
        def __init__(self):
            self.choices = [MagicMock()]
            # Final response: agent provides answer with citations
            self.choices[0].message.tool_calls = None
            self.choices[0].message.content = "Emanuele Artom (1915-1944) was a brilliant Italian-Jewish intellectual and resistance fighter [1]. He studied at the Scuola Normale Superiore in Pisa and was tragically killed by Nazi forces while fighting with the Italian Resistance [1]."
            self.model = "gpt-4"
            self.choices[0].finish_reason = "stop"
    
    # Mock the OpenAI client with two different responses
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = [
        MockToolCallResponse(),  # First call: decides to use tool
        MockFinalResponse()      # Second call: provides final answer
    ]
    
    # Mock the retrieval service
    from backend.services import retrieval_service
    original_retrieve = retrieval_service.retrieve_similar_chunks
    
    # Create mock chunk and document
    mock_document = MagicMock()
    mock_document.title = "Emanuele Artom: A Biography"
    mock_document.document_class = "about_subject"
    
    mock_chunk = MagicMock()
    mock_chunk.text = "Emanuele Artom was born in 1915 in Turin to a prominent Jewish family. He was a brilliant student who studied at the Scuola Normale Superiore in Pisa."
    mock_chunk.document = mock_document
    mock_chunk.document_id = "doc_123"
    mock_chunk.sequence_number = 1
    
    async def mock_retrieve(session, query, k=5):
        return [(mock_chunk, 0.85)]
    
    retrieval_service.retrieve_similar_chunks = mock_retrieve
    
    try:
        agent = SmartAgent()
        agent._client = mock_client
        
        # Test with knowledge question
        session = MagicMock()  # Mock database session
        history = []
        user_query = "Who was Emanuele Artom?"
        
        answer, citations, answer_type, citation_map = await agent.chat(session, history, user_query)
        
        print(f"   Answer: {answer[:150]}...")
        print(f"   Answer type: {answer_type}")
        print(f"   Citations: {citations}")
        print(f"   Citation map: {citation_map}")
        print(f"   ✅ Expected knowledge mode with citations")
        print()
        
    finally:
        # Restore original function
        retrieval_service.retrieve_similar_chunks = original_retrieve


async def main():
    """Run all tests."""
    print("🧪 Testing SmartAgent implementation\n")
    
    try:
        await test_chitchat()
        await test_knowledge_request()
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 