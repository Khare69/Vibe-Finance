"""
FastAPI Authentication Dependencies and Session Management for Vibe Finance.
Implements:
- JWT Bearer Token Extraction from HTTP Authorization headers.
- Multi-tenant UserSession modeling (Guest/Demo fallback vs. Authenticated User).
- Dependencies:
  - `get_current_user`: Soft dependency allowing seamless demo/guest access (id='default_user')
    while validating signed tokens when provided.
  - `require_authenticated_user`: Strict dependency raising 401 Unauthorized for protected endpoints.
- `resolve_user_session`: Robust helper ensuring direct function calls in test scripts
  safely fall back to GUEST_SESSION when called outside FastAPI dependency injection.
"""
from typing import Optional, Any
from fastapi import Request, HTTPException, status, Depends
from pydantic import BaseModel
from backend.auth.security import decode_access_token


class UserSession(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    role: str = "investor"
    is_authenticated: bool = False


# Default guest / demo session when no Authorization header is provided
GUEST_SESSION = UserSession(
    id="default_user",
    username="demo_user",
    email="demo@vibefinance.internal",
    role="investor",
    is_authenticated=False
)


def extract_bearer_token(request: Request) -> Optional[str]:
    """Extracts raw JWT token from Authorization header ('Bearer <token>')."""
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if not auth_header:
        return None
    
    parts = auth_header.strip().split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


async def get_current_user(request: Request) -> UserSession:
    """
    Soft authentication dependency.
    - If Authorization header is absent: returns GUEST_SESSION (enables out-of-the-box demo exploration).
    - If Authorization header is provided: validates token. If valid, returns authenticated UserSession.
      If token is invalid or expired, raises HTTP 401.
    """
    token = extract_bearer_token(request)
    if not token:
        return GUEST_SESSION

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, tampered, or expired authentication token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = payload.get("sub")
    username = payload.get("username", "user")
    email = payload.get("email")
    role = payload.get("role", "investor")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token: missing subject claim",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return UserSession(
        id=user_id,
        username=username,
        email=email,
        role=role,
        is_authenticated=True
    )


async def require_authenticated_user(current_user: UserSession = Depends(get_current_user)) -> UserSession:
    """
    Strict authentication dependency.
    Raises HTTP 401 if the requester is operating in unauthenticated guest/demo mode.
    """
    session = resolve_user_session(current_user)
    if not session.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this operation. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return session


def resolve_user_session(user_param: Any) -> UserSession:
    """Safely extracts a valid UserSession even if called directly outside FastAPI's runner."""
    if isinstance(user_param, UserSession):
        return user_param
    return GUEST_SESSION
