"""
JARVIS Security v2
  - SecurityGuardMiddleware : secret-probe blocking + response redaction + security headers
  - RateLimitMiddleware      : per-IP rate limiting (no Redis dependency)
  - sanitize_user_input()    : prompt-injection prevention
  - require_admin()          : creator-only endpoint protection
"""
import re
import time
import os
import hashlib
from collections import defaultdict
from fastapi import Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

# ── Admin auth ────────────────────────────────────────────────────────────────
_ADMIN_TOKEN = os.getenv("JARVIS_ADMIN_TOKEN", "")
_admin_header = APIKeyHeader(name="X-Admin-Token", auto_error=False)

async def require_admin(token: str = Depends(_admin_header)):
    """Dependency: only the creator can call this endpoint."""
    if not _ADMIN_TOKEN:
        raise HTTPException(status_code=500, detail="Admin token not configured")
    if not token or not _safe_compare(token, _ADMIN_TOKEN):
        raise HTTPException(status_code=403, detail="Admin access required")
    return True

def _safe_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    ha = hashlib.sha256(a.encode()).digest()
    hb = hashlib.sha256(b.encode()).digest()
    return ha == hb

# ── Prompt injection prevention ───────────────────────────────────────────────
_INJECTION_PATTERNS = [
    r'ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?',
    r'disregard\s+(?:all\s+)?(?:previous|prior|above)',
    r'forget\s+(?:all\s+)?(?:previous|prior|above)',
    r'you\s+are\s+now\s+(?:a\s+)?(?:different|new|another)',
    r'new\s+instructions?:\s',
    r'system\s+prompt[:\s]',
    r'<\s*/?system\s*>',
    r'\[INST\]|\[/INST\]',
    r'###\s*(?:System|Instruction)',
    r'(?:act|pretend|roleplay|simulate)\s+as\s+(?:a\s+)?(?:different|evil|unfiltered)',
    r'jailbreak|DAN mode|developer mode',
]
_COMPILED_INJECTION = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]

def sanitize_user_input(text: str) -> str:
    """
    Wrap user input in clear delimiters and strip known injection patterns.
    Returns sanitized text safe to include in an LLM prompt.
    """
    if not text:
        return text
    # Strip injection attempts
    for pattern in _COMPILED_INJECTION:
        text = pattern.sub("[BLOCKED]", text)
    # Wrap in delimiters so the LLM cannot mistake user text for system instructions
    return f"<user_message>{text}</user_message>"

def is_injection_attempt(text: str) -> bool:
    """Returns True if the text looks like a prompt injection attempt."""
    for pattern in _COMPILED_INJECTION:
        if pattern.search(text):
            return True
    return False

# ── Rate limiting ─────────────────────────────────────────────────────────────
# Simple in-process sliding window — good for single-instance Fly.io deployment.
# Swap the _RateLimiter for a Redis-backed one when running multiple machines.
class _RateLimiter:
    def __init__(self):
        # { ip: [timestamp, ...] }
        self._windows: dict = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        timestamps = self._windows[key]
        # Evict old entries
        self._windows[key] = [t for t in timestamps if t > cutoff]
        if len(self._windows[key]) >= max_requests:
            return False
        self._windows[key].append(now)
        return True

_limiter = _RateLimiter()

# Per-route limits: (max_requests, window_seconds)
_RATE_LIMITS = {
    "/chat":         (30,  60),   # 30 req / min  — LLM calls
    "/voice":        (20,  60),   # 20 req / min  — voice pipeline
    "/api/brain":    (60,  60),   # 60 req / min  — brain status
    "/api/memory":   (60,  60),
    "/browser":      (10,  60),   # 10 req / min  — browser automation (expensive)
    "default":       (120, 60),   # 120 req / min — everything else
}

def _get_rate_limit(path: str):
    for prefix, limits in _RATE_LIMITS.items():
        if prefix != "default" and path.startswith(prefix):
            return limits
    return _RATE_LIMITS["default"]

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "unknown"
        path = request.url.path
        max_req, window = _get_rate_limit(path)
        key = f"{ip}:{path}"
        if not _limiter.is_allowed(key, max_req, window):
            logger.warning(f"Rate limit hit: {ip} → {path}")
            return JSONResponse(
                status_code=429,
                content={"error": "Too many requests. Slow down."},
                headers={"Retry-After": str(window)},
            )
        return await call_next(request)

# ── Secret patterns ───────────────────────────────────────────────────────────
SECRET_PROBE_PATTERNS = [
    r'show\s+(?:me\s+)?(?:the\s+)?(?:api\s+key|secret|env|\.env|environment\s+variable)',
    r'reveal\s+(?:the\s+)?(?:api\s+key|secret|env|secret_key)',
    r'what\s+(?:is\s+)?(?:your\s+)?(?:api\s+key|secret\s+key|openai\s+key)',
    r'print\s+(?:the\s+)?(?:env|environment|secrets?|api\s+key)',
    r'(?:list|show|dump|display)\s+(?:all\s+)?(?:env(?:ironment)?\s+variables?|secrets?)',
    r'(?:OPENAI_API_KEY|SECRET_KEY|DATABASE_URL|REDIS_URL)',
]

SECRET_REDACT_PATTERNS = [
    r'sk-[a-zA-Z0-9\-_]{20,}',
    r'sk-or-[a-zA-Z0-9\-_]{20,}',
    r'gsk_[a-zA-Z0-9]{20,}',
    r'Bearer\s+[a-zA-Z0-9\-_\.]{20,}',
    r'FlyV1\s+[a-zA-Z0-9\+\/=]{20,}',
    r'cfut_[a-zA-Z0-9]{20,}',
    r'(?:password|passwd|pwd)\s*[=:]\s*\S+',
]

BLOCKED_PATHS = {'/.env', '/env', '/secrets', '/.git', '/config/raw', '/admin/env'}

SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'no-referrer',
    'Cache-Control': 'no-store, max-age=0',
    'Content-Security-Policy': "default-src 'self'",
    'Permissions-Policy': 'geolocation=(), microphone=()',
}

class SecurityGuardMiddleware(BaseHTTPMiddleware):
    """
    JARVIS Security Guard v2
    Blocks secret-probe and injection attempts.
    Redacts leaked secrets from responses.
    Injects security headers on every response.
    """
    async def dispatch(self, request: Request, call_next):
        # Block sensitive paths
        if request.url.path in BLOCKED_PATHS:
            return JSONResponse(status_code=403,
                content={"error": "Access denied"}, headers=SECURITY_HEADERS)

        # Scan POST/PUT/PATCH bodies
        if request.method in ('POST', 'PUT', 'PATCH'):
            try:
                body_bytes = await request.body()
                body_text  = body_bytes.decode('utf-8', errors='ignore')
                body_lower = body_text.lower()
                # Secret probes
                for pattern in SECRET_PROBE_PATTERNS:
                    if re.search(pattern, body_lower, re.IGNORECASE):
                        logger.warning(f"Secret probe blocked: {request.client.host} → {request.url.path}")
                        return JSONResponse(status_code=403,
                            content={"error": "Blocked by JARVIS Security Guard."},
                            headers=SECURITY_HEADERS)
                # Injection attempts
                if is_injection_attempt(body_text):
                    logger.warning(f"Injection attempt blocked: {request.client.host} → {request.url.path}")
                    return JSONResponse(status_code=403,
                        content={"error": "Prompt injection attempt detected and blocked."},
                        headers=SECURITY_HEADERS)
            except Exception:
                pass

        response = await call_next(request)

        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        if 'application/json' in response.headers.get('content-type', ''):
            try:
                body_bytes = b''
                async for chunk in response.body_iterator:
                    body_bytes += chunk
                body_text = body_bytes.decode('utf-8', errors='ignore')
                for pattern in SECRET_REDACT_PATTERNS:
                    body_text = re.sub(pattern, '[REDACTED]', body_text, flags=re.IGNORECASE)
                return Response(content=body_text, status_code=response.status_code,
                    headers=dict(response.headers), media_type=response.media_type)
            except Exception:
                pass

        return response
