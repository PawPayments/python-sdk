"""Lightweight typed result wrappers.

These are TypedDicts so the SDK can stay dependency-light (no pydantic).
At runtime they are just plain dicts; the typing exists for editor
support only.
"""
from __future__ import annotations

from typing import Any, TypedDict


class Pagination(TypedDict):
    page: int
    per_page: int
    total: int
    pages: int


class ListResult(TypedDict):
    items: list[dict[str, Any]]
    pagination: Pagination
