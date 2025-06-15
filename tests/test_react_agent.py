import asyncio
from uuid import uuid4
import types

import pytest

from backend.rag.agent import ReActAgent
from backend.rag.schemas import ChatMessage, Role


@pytest.mark.asyncio
async def test_react_agent_basic(monkeypatch):
    messages = [
        {"role": "system", "content": "You are."},
        {"role": "user", "content": "Who was Artom?"},
    ]
    citation_map = {1: {"dummy": True}}

    async def _fake_llm_call(self, prompt: str):  # noqa: D401
        return "Thought: done\nAction: Answer\nFinal: Artom was ... [1]"

    monkeypatch.setattr(ReActAgent, "_llm_call", _fake_llm_call, raising=True)

    agent = ReActAgent()
    answer, cites = await agent.run(messages, citation_map)

    assert "[1]" in answer
    assert cites == [1]
