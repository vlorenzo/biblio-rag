import types
from uuid import uuid4

from backend.rag.prompt import PromptBuilder
from backend.models import DocumentClass


def _make_dummy_hit(doc_class: DocumentClass, seq: int = 1):
    doc = types.SimpleNamespace(title="Test", document_class=doc_class)
    chunk = types.SimpleNamespace(
        document=doc,
        document_id=uuid4(),
        sequence_number=seq,
        text="dummy text",
    )
    return chunk, 0.05  # (chunk, distance)


def test_prompt_builder_inline():
    hits = [
        _make_dummy_hit(DocumentClass.AUTHORED_BY_SUBJECT, 1),
        _make_dummy_hit(DocumentClass.ABOUT_SUBJECT, 2),
    ]

    builder = PromptBuilder()
    _system, messages, citation_map = builder.build([], "Who was Artom?", hits)

    # Expect first message to be system
    assert messages[0]["role"] == "system"
    # Expect two citations in map
    assert len(citation_map) == 2
    # Ensure citation ids are 1 and 2
    assert set(citation_map.keys()) == {1, 2} 