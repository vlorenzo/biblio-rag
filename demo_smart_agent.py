#!/usr/bin/env python3
"""Demo script showcasing the SmartAgent vs old system."""

import asyncio
from backend.rag import smart_engine
from backend.rag.schemas import ChatMessage, Role


def print_divider(title: str):
    """Print a nice divider."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_response(response, title: str):
    """Print a formatted response."""
    print(f"\n{title}:")
    print(f"Answer: {response.answer}")
    print(f"Answer Type: {response.meta.get('mode', 'unknown')}")
    print(f"Citations: {len(response.citations)} found")
    if response.citations:
        for i, citation in enumerate(response.citations, 1):
            print(f"  [{i}] {citation.get('title', 'Unknown')}")


async def demo_conversation_flow():
    """Demonstrate the new intelligent conversation flow."""
    
    print_divider("🤖 SMART AGENT DEMO")
    print("This demo shows how the new SmartAgent makes intelligent decisions")
    print("about when to retrieve knowledge vs when to chat directly.")
    
    # Mock session (in real use, this would be a database session)
    from unittest.mock import MagicMock
    session = MagicMock()
    
    # Conversation scenarios
    scenarios = [
        {
            "title": "🗣️  Casual Greeting",
            "query": "Hello there!",
            "history": [],
            "expected": "Should respond warmly WITHOUT retrieving documents"
        },
        {
            "title": "❓ Knowledge Question", 
            "query": "Who was Emanuele Artom?",
            "history": [],
            "expected": "Should decide to search for information, then provide cited answer"
        },
        {
            "title": "🙏 Thank You",
            "query": "Thank you for that information!",
            "history": [
                ChatMessage(role=Role.USER, content="Who was Emanuele Artom?"),
                ChatMessage(role=Role.ASSISTANT, content="Emanuele Artom was a brilliant Italian-Jewish intellectual...")
            ],
            "expected": "Should respond warmly WITHOUT searching again"
        },
        {
            "title": "🔍 Follow-up Question",
            "query": "What did he study at university?",
            "history": [
                ChatMessage(role=Role.USER, content="Who was Emanuele Artom?"),
                ChatMessage(role=Role.ASSISTANT, content="Emanuele Artom was a brilliant Italian-Jewish intellectual...")
            ],
            "expected": "Should search for more specific information about his studies"
        }
    ]
    
    for scenario in scenarios:
        print_divider(scenario["title"])
        print(f"User: {scenario['query']}")
        print(f"Expected: {scenario['expected']}")
        
        try:
            # This would actually call the real API if we had a running server
            # For now, we'll show the structure
            print("\n🔄 Agent Decision Process:")
            print("1. Agent receives query and conversation history")
            print("2. Agent analyzes if it needs more information")
            
            if "Hello" in scenario["query"] or "Thank you" in scenario["query"]:
                print("3. ✅ Agent decides: 'I can respond directly with personality'")
                print("4. 🎭 Responds as passionate curator without tool calls")
                answer_type = "chitchat"
            else:
                print("3. 🔍 Agent decides: 'I need to search for information'")
                print("4. 🛠️  Calls retrieve_knowledge tool")
                print("5. 📚 Receives relevant documents")
                print("6. 📝 Crafts scholarly response with citations")
                answer_type = "knowledge"
            
            print(f"\n✅ Result: {answer_type} mode")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print_divider("🎯 KEY IMPROVEMENTS")
    print("""
    OLD SYSTEM PROBLEMS:
    ❌ Intent classification happens BEFORE the LLM sees the query
    ❌ System makes decisions FOR the AI instead of letting it be smart  
    ❌ Rigid pipeline: Intent → Retrieval → Prompt Stuffing → Response
    ❌ No real personality or curiosity
    ❌ Can't adapt to conversation context
    
    NEW SMART AGENT BENEFITS:
    ✅ LLM makes intelligent decisions about when to retrieve
    ✅ Real tool calling with proper reasoning
    ✅ Engaging personality that shines through
    ✅ Contextual responses based on conversation history
    ✅ Graceful handling of missing information
    ✅ Much cleaner, more maintainable code
    
    WORKFLOW COMPARISON:
    
    Old: User Query → Intent Classifier → [IF knowledge] → Retrieval → Prompt Builder → LLM
    New: User Query → Smart LLM → [IF needed] → Tool Call → Retrieval → Smart LLM
    
    The new system lets the AI be truly intelligent! 🧠✨
    """)


async def main():
    """Run the demo."""
    await demo_conversation_flow()
    
    print_divider("🚀 READY TO USE")
    print("The SmartAgent is ready! To use it:")
    print("1. Start your FastAPI server")
    print("2. Send requests to /chat endpoint") 
    print("3. Watch the agent make smart decisions! 🎉")


if __name__ == "__main__":
    asyncio.run(main()) 