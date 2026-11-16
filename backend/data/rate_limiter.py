"""
Token Bucket Rate Limiter & Circuit Breaker Layer
Controls outbound API request velocity to external market data providers (e.g. Yahoo Finance)
and trips an immediate 60-second cooldown circuit breaker upon encountering HTTP 429 errors.
"""

import time
import threading
from typing import Tuple

class TokenBucketRateLimiter:
    """
    Token Bucket Rate Limiter:
    - replenishment_rate: tokens added per second (default: 2.0 req/s)
    - max_capacity: maximum burst token buffer (default: 10 tokens)
    """
    def __init__(self, replenishment_rate: float = 2.0, max_capacity: float = 10.0):
        self.rate = replenishment_rate
        self.capacity = max_capacity
        self.tokens = max_capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def acquire(self, tokens_needed: float = 1.0, timeout: float = 5.0) -> bool:
        start_wait = time.time()
        while True:
            with self.lock:
                now = time.time()
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + (elapsed * self.rate))
                self.last_refill = now

                if self.tokens >= tokens_needed:
                    self.tokens -= tokens_needed
                    return True

            if (time.time() - start_wait) > timeout:
                return False
            time.sleep(0.05)


class CircuitBreaker:
    """
    Circuit Breaker:
    - CLOSED: Normal operation. Outbound requests permitted.
    - OPEN: Tripped on HTTP 429 Too Many Requests. Outbound requests blocked for cooldown_seconds (60s).
    - HALF_OPEN: Probe request permitted after cooldown to evaluate endpoint recovery.
    """
    def __init__(self, cooldown_seconds: float = 60.0):
        self.cooldown_seconds = cooldown_seconds
        self.state = "CLOSED"  # "CLOSED" | "OPEN" | "HALF_OPEN"
        self.last_tripped_time = 0.0
        self.lock = threading.Lock()

    def can_execute(self) -> Tuple[bool, str]:
        with self.lock:
            now = time.time()
            if self.state == "OPEN":
                if (now - self.last_tripped_time) >= self.cooldown_seconds:
                    self.state = "HALF_OPEN"
                    return True, "HALF_OPEN_PROBE"
                time_remaining = int(self.cooldown_seconds - (now - self.last_tripped_time))
                return False, f"CIRCUIT_OPEN_COOLDOWN_{time_remaining}S"
            elif self.state == "HALF_OPEN":
                return True, "HALF_OPEN"
            return True, "CLOSED"

    def record_success(self):
        with self.lock:
            if self.state in ["HALF_OPEN", "OPEN"]:
                print("[CircuitBreaker] Endpoint recovered. Circuit reset to CLOSED.")
            self.state = "CLOSED"

    def record_429(self):
        with self.lock:
            self.state = "OPEN"
            self.last_tripped_time = time.time()
            print(f"[CircuitBreaker] HTTP 429 encountered! Tripped circuit breaker for {self.cooldown_seconds}s cooldown.")


# Global instances
market_rate_limiter = TokenBucketRateLimiter(replenishment_rate=2.0, max_capacity=10.0)
market_circuit_breaker = CircuitBreaker(cooldown_seconds=60.0)
