"""User-facing labels for collection metadata fields.

This module centralizes the mapping between internal DB column names (and common
aliases) and the labels we want to show to end users.
"""

from __future__ import annotations

from typing import Iterable, List


# NOTE: keep keys lowercase; mapping is applied case-insensitively.
USER_FACING_FIELD_LABELS: dict[str, str] = {
    # Internal DB columns
    "description": "Note",
    "publisher": "Luogo ed editore",
    # Common Italian aliases (defensive; may appear in queries / UI)
    "note": "Note",
    "editore": "Luogo ed editore",
}


def user_facing_label(field_name: str) -> str:
    """Return the user-facing label for a metadata field/column name."""
    key = (field_name or "").strip().lower()
    return USER_FACING_FIELD_LABELS.get(key, field_name)


def map_field_labels(fields: Iterable[str]) -> List[str]:
    """Map an iterable of field names to user-facing labels."""
    return [user_facing_label(f) for f in fields]

