# PROMPT: Add structured JSON request logging middleware that attaches a trace_id to every request and logs endpoint, latency, status, and store context
# CHANGES MADE: Created LoggingMiddleware using Starlette BaseHTTPMiddleware

import json, time, uuid, logging
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("store_intelligence")

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        trace_id = str(uuid.uuid4())[:8]
        request.state.trace_id = trace_id
        start = time.monotonic()
        response = await call_next(request)
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        
        store_id = None
        parts = request.url.path.split("/")
        if len(parts) >= 3 and parts[1] == "stores":
            store_id = parts[2]
            
        log = {
            "trace_id":   trace_id,
            "method":     request.method,
            "path":       request.url.path,
            "status":     response.status_code,
            "latency_ms": latency_ms,
            "store_id":   store_id,
        }
        print(json.dumps(log))
        response.headers["X-Trace-Id"] = trace_id
        return response
