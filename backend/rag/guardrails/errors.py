"""Custom exceptions used by the guardrails layer."""

class GuardrailError(RuntimeError):
    """Base class for guardrail violations."""


class TokenLimitError(GuardrailError):
    """Raised when the prompt exceeds the allowed token budget."""


class CitationError(GuardrailError):
    """Raised when citations in the answer are missing or invalid.""" 