"""
Stealth Session & Header Rotation Manager
Provides modern desktop browser headers (Chrome, Firefox, Safari, Edge)
and custom requests.Session instances with optional residential proxy routing.
"""

import os
import random
import requests
from typing import Dict, Optional

BROWSER_USER_AGENTS = [
    # Chrome on Windows 11
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Chrome on macOS Sonoma
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]

def get_random_user_agent() -> str:
    return random.choice(BROWSER_USER_AGENTS)

def get_stealth_headers() -> Dict[str, str]:
    return {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }

def get_proxy_dict() -> Optional[Dict[str, str]]:
    """
    Checks for optional YFINANCE_PROXIES environment variable (comma-separated proxy URLs).
    If present, rotates a proxy from the pool. Returns None if unconfigured.
    """
    proxies_raw = os.environ.get("YFINANCE_PROXIES", "").strip()
    if not proxies_raw:
        return None
    proxy_list = [p.strip() for p in proxies_raw.split(",") if p.strip()]
    if not proxy_list:
        return None
    selected_proxy = random.choice(proxy_list)
    return {
        "http": selected_proxy,
        "https": selected_proxy,
    }

def create_stealth_session() -> requests.Session:
    """Creates a configured requests.Session with modern browser headers and proxy support."""
    session = requests.Session()
    session.headers.update(get_stealth_headers())
    proxies = get_proxy_dict()
    if proxies:
        session.proxies.update(proxies)
    return session
