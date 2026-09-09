"""Authentication integration point for the parent application."""

from typing import Any


async def get_current_user() -> Any:
    """Replace this dependency with the parent application's auth middleware."""
    return None
