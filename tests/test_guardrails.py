from backend.rag.guardrails import apply_guardrails, REFUSAL_MSG


def test_guardrails_ok():
    answer = "Artom was a scholar. [1]"
    citation_map = {1: {"dummy": True}}
    assert apply_guardrails(answer, citation_map) == answer


def test_guardrails_missing_citation():
    answer = "Artom was a scholar. [2]"
    citation_map = {1: {"dummy": True}}
    assert apply_guardrails(answer, citation_map) == REFUSAL_MSG 