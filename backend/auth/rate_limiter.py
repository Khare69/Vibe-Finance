"""
Thread-safe Sliding-Window Rate Limiter for Vibe Finance API.
Guarantees:
- Per-client (User ID or Remote IP) request metering.
- Sliding timestamp window algorithm eliminating end-of-window burst vulnerabilities.
- Thread-safe eviction using threading.Lock.
- Returns HTTP 429 Too Many Requests with compliant Retry-After headers when quota is exhausted.
"""
import time
import threading
from typing import Dict, Deque
from collections import deque
from fastapi import Request, HTTPException, status


class SlidingWindowRateLimiter:
    """
    In-memory, thread-safe sliding window rate limiter.
    Retains request timestamps in a deque per client key.
    """
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: Dict[str, Deque[float]] = {}
        self._lock = threading.Lock()

    def _get_client_identifier(self, request: Request) -> str:
        """
        Derives an isolated client identifier:
        1. Checks for Authorization header / user subject if already resolved.
        2. Falls back to X-Forwarded-For client IP or socket client IP.
        """
        # If request has authenticated user state attached
        if hasattr(request, "state") and hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"

        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # First IP in comma-separated chain
            client_ip = forwarded.split(",")[0].strip()
            return f"ip:{client_ip}"

        if request.client and request.client.host:
            return f"ip:{request.client.host}"

        return "ip:127.0.0.1"

    def check(self, request: Request):
        """
        Evaluates the client's current request against the sliding rate limit window.
        Raises HTTP 429 if the request limit has been breached.
        """
        client_key = self._get_client_identifier(request)
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            if client_key not in self._history:
                self._history[client_key] = deque()

            queue = self._history[client_key]

            # Evict timestamps outside the active sliding window
            while queue and queue[0] < window_start:
                queue.popleft()

            # Check if limit reached
            if len(queue) >= self.max_requests:
                oldest = queue[0]
                retry_after = max(1, int(oldest + self.window_seconds - now))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: Maximum {self.max_requests} requests per {self.window_seconds}s.",
                    headers={"Retry-After": str(retry_after)}
                )

            # Record this request
            queue.append(now)

    def reset(self):
        """Clears all tracked client history (used during unit testing)."""
        with self._lock:
            self._history.clear()


# Default instance for high-cost computation routes (Analyze, Backtest, Debate, Stream)
analysis_rate_limiter = SlidingWindowRateLimiter(max_requests=30, window_seconds=60)


def rate_limit_analysis(request: Request):
    """FastAPI dependency for metering expensive analysis and backtesting endpoints."""
    analysis_rate_limiter.check(request)
