import re
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

# Patterns that indicate someone probing for secrets
SECRET_PROBE_PATTERNS = [
    r'show\s+(?:me\s+)?(?:the\s+)?(?:api\s+key|secret|env|\.env|environment\s+variable)',
    r'reveal\s+(?:the\s+)?(?:api\s+key|secret|env|secret_key)',
    r'what\s+(?:is\s+)?(?:your\s+)?(?:api\s+key|secret\s+key|openai\s+key)',
    r'print\s+(?:the\s+)?(?:env|environment|secrets?|api\s+key)',
    r'(?:list|show|dump|display)\s+(?:all\s+)?(?:env(?:ironment)?\s+variables?|secrets?)',
    r'(?:OPENAI_API_KEY|SECRET_KEY|DATABASE_URL|REDIS_URL)',
]

# Patterns to redact from responses
SECRET_REDACT_PATTERNS = [
    r'sk-[a-zA-Z0-9\-_]{20,}',           # OpenAI keys
    r'sk-or-[a-zA-Z0-9\-_]{20,}',        # OpenRouter keys
    r'gsk_[a-zA-Z0-9]{20,}',              # Groq keys
    r'Bearer\s+[a-zA-Z0-9\-_\.]{20,}', # Bearer tokens
    r'FlyV1\s+[a-zA-Z0-9\+\/=]{20,}',  # Fly.io tokens
    r'cfut_[a-zA-Z0-9]{20,}',             # Cloudflare tokens
    r'(?:password|passwd|pwd)\s*[=:]\s*\S+',  # Passwords
]

BLOCKED_PATHS = {'/.env', '/env', '/secrets', '/.git', '/config/raw', '/admin/env'}

SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'no-referrer',
    'Cache-Control': 'no-store, max-age=0',
}


class SecurityGuardMiddleware(BaseHTTPMiddleware):
    """
    JARVIS Security Guard — runs on every request/response.
    Blocks secret-probe attempts and redacts any leaked secrets.
    """

    async def dispatch(self, request: Request, call_next):
        # Block sensitive paths
        if request.url.path in BLOCKED_PATHS:
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied"},
                headers=SECURITY_HEADERS,
            )

        # Scan request body for secret probes
        if request.method in ('POST', 'PUT', 'PATCH'):
            try:
                body_bytes = await request.body()
                body_text = body_bytes.decode('utf-8', errors='ignore').lower()
                for pattern in SECRET_PROBE_PATTERNS:
                    if re.search(pattern, body_text, re.IGNORECASE):
                        logger.warning(
                            f"Secret probe blocked from {request.client.host}: {request.url.path}"
                        )
                        return JSONResponse(
                            status_code=403,
                            content={"error": "This request was blocked by JARVIS Security Guard."},
                            headers=SECURITY_HEADERS,
                        )
            except Exception:
                pass  # Never break request flow on security check failure

        response = await call_next(request)

        # Inject security headers on every response
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        # Redact secrets from JSON responses
        if 'application/json' in response.headers.get('content-type', ''):
            try:
                body_bytes = b''
                async for chunk in response.body_iterator:
                    body_bytes += chunk
                body_text = body_bytes.decode('utf-8', errors='ignore')
                for pattern in SECRET_REDACT_PATTERNS:
                    body_text = re.sub(pattern, '[REDACTED]', body_text, flags=re.IGNORECASE)
                return Response(
                    content=body_text,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
            except Exception:
                pass  # Never break response flow on redaction failure

        return response
