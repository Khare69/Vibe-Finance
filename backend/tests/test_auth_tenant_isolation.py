"""
Unit & Integration Test Suite for Sub-phase E.2:
User Authentication, JWT Middleware, Tenant Database Isolation & Rate Limiting.
"""
import time
import uuid
from backend.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)
from backend.auth.rate_limiter import SlidingWindowRateLimiter
from backend.models import (
    UserDB,
    PortfolioHoldingDB,
    WatchlistDB,
    DecisionMemoDB
)
from backend.database import (
    init_db,
    create_user,
    get_user_by_username,
    get_user_by_id,
    get_all_holdings,
    upsert_holding,
    delete_holding,
    clear_all_holdings,
    get_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    save_memo,
    get_memos,
    delete_memo
)
from fastapi import HTTPException, Request


def test_password_hashing_and_verification():
    """Verifies PBKDF2-SHA256 password hashing, salting, and constant-time verification."""
    password = "SuperSecretPassword#2026"
    hashed = hash_password(password)

    assert hashed.startswith("pbkdf2_sha256$100000$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(password, "") is False

    # Unique salts guarantee two hashes of the same password differ
    hashed_again = hash_password(password)
    assert hashed != hashed_again
    assert verify_password(password, hashed_again) is True


def test_jwt_token_lifecycle_and_tamper_proofing():
    """Verifies HS256 JWT creation, decoding, expiration, and cryptographic signature rejection."""
    claims = {"sub": "user_abc123", "username": "alpha_trader", "role": "portfolio_manager"}
    token = create_access_token(claims, expires_minutes=15)

    assert token.count(".") == 2
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user_abc123"
    assert decoded["username"] == "alpha_trader"
    assert decoded["role"] == "portfolio_manager"
    assert "exp" in decoded
    assert "iat" in decoded

    # Tampering with payload or signature must return None
    parts = token.split(".")
    tampered_token = f"{parts[0]}.eyJhZG1pbiI6dHJ1ZX0.{parts[2]}"
    assert decode_access_token(tampered_token) is None

    # Expired token test (token expired 10 seconds ago)
    expired_token = create_access_token(claims, expires_minutes=-1)
    assert decode_access_token(expired_token) is None


def test_sliding_window_rate_limiter():
    """Verifies sliding window rate limiter burst protection and HTTP 429 response."""
    limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=2)
    
    # Mock request with client IP
    class MockRequest:
        def __init__(self, ip: str):
            self.headers = {}
            self.client = type("Client", (), {"host": ip})()

    req_a = MockRequest("192.168.1.100")
    req_b = MockRequest("192.168.1.200")

    # Send 5 allowed requests for client A
    for _ in range(5):
        limiter.check(req_a)

    # 6th request from client A must raise HTTP 429
    raised = False
    try:
        limiter.check(req_a)
    except HTTPException as exc:
        raised = True
        assert exc.status_code == 429
        assert "Rate limit exceeded" in exc.detail
        assert "Retry-After" in exc.headers
    assert raised is True, "Expected HTTPException 429 was not raised"

    # Client B should still be unaffected (tenant/IP isolation)
    limiter.check(req_b)

    # After window expires, client A can request again
    time.sleep(2.1)
    limiter.check(req_a)


def test_multi_tenant_database_isolation():
    """
    STRICT TENANT ISOLATION INVARIANT:
    Verifies that User A and User B operate with complete isolation in SQLite:
    - Independent portfolio holdings with composite key (user_id, ticker).
    - Independent watchlists and decision memos.
    - User A mutating or deleting items never impacts User B.
    """
    init_db()

    user_a_id = f"test_user_a_{uuid.uuid4().hex[:6]}"
    user_b_id = f"test_user_b_{uuid.uuid4().hex[:6]}"

    # 1. Holdings Isolation Test
    holding_a = PortfolioHoldingDB(
        user_id=user_a_id,
        ticker="INFY",
        company_name="Infosys Ltd.",
        shares=100.0,
        avg_cost=1500.0,
        currency="INR",
        sector="Tech",
        beta=0.85
    )
    upsert_holding(holding_a, user_id=user_a_id)

    # User B checks holdings -> must NOT see User A's INFY
    b_holdings = get_all_holdings(user_id=user_b_id)
    assert not any(h.ticker == "INFY" for h in b_holdings)

    # User B adds their own holding of INFY with distinct shares and cost
    holding_b = PortfolioHoldingDB(
        user_id=user_b_id,
        ticker="INFY",
        company_name="Infosys Ltd.",
        shares=25.0,
        avg_cost=1620.0,
        currency="INR",
        sector="Tech",
        beta=0.85
    )
    upsert_holding(holding_b, user_id=user_b_id)

    # Verify both users have isolated holdings for the same ticker
    a_holdings_updated = get_all_holdings(user_id=user_a_id)
    b_holdings_updated = get_all_holdings(user_id=user_b_id)

    a_infy = next(h for h in a_holdings_updated if h.ticker == "INFY")
    b_infy = next(h for h in b_holdings_updated if h.ticker == "INFY")

    assert a_infy.shares == 100.0
    assert a_infy.avg_cost == 1500.0
    assert b_infy.shares == 25.0
    assert b_infy.avg_cost == 1620.0

    # User A deletes their holding -> User B's holding must remain untouched
    delete_holding("INFY", user_id=user_a_id)
    assert not any(h.ticker == "INFY" for h in get_all_holdings(user_id=user_a_id))
    assert any(h.ticker == "INFY" for h in get_all_holdings(user_id=user_b_id))

    # Clean up User B holding
    delete_holding("INFY", user_id=user_b_id)

    # 2. Watchlist Isolation Test
    wl_a = WatchlistDB(user_id=user_a_id, ticker="TATAMOTORS", target_price=980.0, notes="EV breakout")
    add_to_watchlist(wl_a, user_id=user_a_id)

    assert any(w.ticker == "TATAMOTORS" for w in get_watchlist(user_id=user_a_id))
    assert not any(w.ticker == "TATAMOTORS" for w in get_watchlist(user_id=user_b_id))

    remove_from_watchlist("TATAMOTORS", user_id=user_a_id)

    # 3. Decision Memos Isolation Test
    memo_id = f"memo_{uuid.uuid4().hex[:8]}"
    memo_a = DecisionMemoDB(
        id=memo_id,
        user_id=user_a_id,
        ticker="RELIANCE",
        company_name="Reliance Industries",
        memo_markdown="### Private Investment Thesis for User A"
    )
    save_memo(memo_a, user_id=user_a_id)

    memos_a = get_memos(user_id=user_a_id)
    memos_b = get_memos(user_id=user_b_id)

    assert any(m.id == memo_id for m in memos_a)
    assert not any(m.id == memo_id for m in memos_b)

    delete_memo(memo_id, user_id=user_a_id)


def test_user_repository_crud():
    """Verifies user registration and retrieval in SQLite."""
    unique_user = f"user_{uuid.uuid4().hex[:8]}"
    user_db = UserDB(
        id=f"id_{unique_user}",
        username=unique_user,
        hashed_password=hash_password("Pass@123456"),
        email=f"{unique_user}@vibe.finance",
        role="investor"
    )
    created = create_user(user_db)
    assert created.username == unique_user

    fetched = get_user_by_username(unique_user)
    assert fetched is not None
    assert fetched.id == f"id_{unique_user}"
    assert verify_password("Pass@123456", fetched.hashed_password) is True

    by_id = get_user_by_id(f"id_{unique_user}")
    assert by_id is not None
    assert by_id.username == unique_user
