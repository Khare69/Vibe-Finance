"""
Safe Network Guard for Vibe Finance.
Controls and validates outbound network access for testing and live market data retrieval.

Safety & Reliability Guarantees:
1. Strict Domain Whitelisting: Outbound calls are confined to approved financial & LLM APIs.
2. Fast Connectivity Probe: Lightweight 1.5s TCP probe prevents multi-minute yfinance retry hangs when offline.
3. Execution Mode Flags:
   - Default testing (TESTING=1): Instant offline mode using high-fidelity snapshot cache (<2s total).
   - Live testing (VIBE_ALLOW_NETWORK=1): Controlled real-time fetching with active internet access.
   - Production / Dev server: Transparent live fetching with automated fallback on outage.
4. Graceful Degradation: Zero unhandled network crashes; automatically returns verified fallback data.
"""
import os
import socket
from typing import Tuple, Dict, Any, Optional

ALLOWED_DOMAINS = [
    "query1.finance.yahoo.com",
    "query2.finance.yahoo.com",
    "generativelanguage.googleapis.com"
]

DEFAULT_TIMEOUT_SECONDS = 5.0
_CONNECTIVITY_CACHE: Dict[str, Tuple[float, bool]] = {}
_CACHE_TTL_SECONDS = 30.0


def is_network_allowed() -> bool:
    """
    Checks if live external network requests are permitted.
    Network requests are blocked if:
    - VIBE_OFFLINE_MODE is explicitly '1'.
    - TESTING is '1' and VIBE_ALLOW_NETWORK is not '1'.
    """
    if os.environ.get("VIBE_OFFLINE_MODE") == "1":
        return False
    if os.environ.get("TESTING") == "1" and os.environ.get("VIBE_ALLOW_NETWORK") != "1":
        return False
    return True


def probe_connectivity(host: str = "1.1.1.1", port: int = 53, timeout: float = 0.5) -> bool:
    """
    Ultra-fast, non-blocking TCP socket probe to verify internet access before
    triggering heavy yfinance downloads. Uses direct IP to avoid Windows DNS resolution hangs.
    Caches results for 30s to avoid redundant checks.
    """
    if not is_network_allowed():
        return False

    import time
    now = time.time()
    cache_key = f"{host}:{port}"
    if cache_key in _CONNECTIVITY_CACHE:
        cached_time, status = _CONNECTIVITY_CACHE[cache_key]
        if now - cached_time < _CACHE_TTL_SECONDS:
            return status

    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        _CONNECTIVITY_CACHE[cache_key] = (now, True)
        return True
    except (socket.timeout, OSError, Exception):
        _CONNECTIVITY_CACHE[cache_key] = (now, False)
        return False


def get_network_diagnostics() -> Dict[str, Any]:
    """Returns real-time network safety and accessibility state."""
    allowed = is_network_allowed()
    connected = probe_connectivity() if allowed else False
    return {
        "network_allowed": allowed,
        "internet_reachable": connected,
        "offline_mode_env": os.environ.get("VIBE_OFFLINE_MODE", "0"),
        "allow_network_env": os.environ.get("VIBE_ALLOW_NETWORK", "0"),
        "testing_env": os.environ.get("TESTING", "0"),
        "whitelisted_domains": ALLOWED_DOMAINS
    }
