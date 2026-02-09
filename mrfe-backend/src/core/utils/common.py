"""Pure utility helpers."""

from __future__ import annotations

import html
import re
from collections.abc import Iterator, Sequence
from typing import TypeVar
from uuid import uuid4

T = TypeVar("T")


def generate_unique_id() -> str:
    """Generate UUID string."""
    return str(uuid4())


def sanitize_text(value: str) -> str:
    """Sanitize text to reduce XSS payload risks."""
    escaped = html.escape(value.strip(), quote=True)
    return re.sub(r"\s+", " ", escaped)


def chunked(items: Sequence[T], size: int) -> Iterator[Sequence[T]]:
    """Yield fixed-size chunks."""
    if size <= 0:
        raise ValueError("size must be > 0")
    for index in range(0, len(items), size):
        yield items[index : index + size]
