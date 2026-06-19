"""
JARVIS Auth helpers — creator-only admin token.
Re-exported here so routers can import from `auth` directly.
"""
from security import require_admin  # noqa: F401 — single source of truth
