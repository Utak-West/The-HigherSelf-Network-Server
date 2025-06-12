"""
Enhanced API Security for The HigherSelf Network Server.

This module provides robust authentication and authorization features including:
1. JWT-based authentication with role and scope validation
2. API key validation for webhooks
3. Role-based access control
4. Advanced rate limiting middleware

Usage:
    # In FastAPI app initialization
    from api.middleware.enhanced_security import (
        setup_security, authenticate_user, get_current_active_user,
        RoleChecker, require_scopes, validate_api_key
    )

    # Set up security for the application
    setup_security(app)

    # Example protected endpoint with role and scope checks
    @app.get("/admin/users")
    async def list_users(
        current_user: User = Depends(get_current_active_user),
        _: None = Depends(RoleChecker(["admin"])),
        __: None = Depends(require_scopes(["users:read"]))
    ):
        return {"users": [...]}
"""

import json
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union

import redis
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.security import (APIKeyHeader, OAuth2PasswordBearer,
                              OAuth2PasswordRequestForm)
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from utils.circuit_breaker import (CircuitBreaker, CircuitOpenException,
                                   registry)
from utils.error_handling import (AuthenticationException,
                                  AuthorizationException, ErrorCategory,
                                  ErrorHandler, ErrorResponse, ErrorSeverity)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Security schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
api_key_header = APIKeyHeader(name="X-API-Key")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create a circuit breaker for the authentication service
auth_circuit = registry.get_or_create(
    "authentication_service", failure_threshold=5, recovery_timeout=60, timeout=3.0
)


# Models for authentication
class Token(BaseModel):
    """JWT token response model."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_at: datetime


class TokenData(BaseModel):
    """JWT token data model."""

    sub: str
    scopes: List[str] = []
    role: str = "user"
    exp: datetime


class User(BaseModel):
    """User model with role and permissions information."""

    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    role: str = "user"  # or admin, etc.
    scopes: List[str] = []


class UserInDB(User):
    """User model with hashed password."""

    hashed_password: str


# Rate limiting configuration
class RateLimitConfig(BaseModel):
    """Configuration for rate limiting."""

    requests_per_minute: int = Field(
        60, description="Number of requests allowed per minute"
    )
    burst_capacity: int = Field(20, description="Burst capacity for request spikes")
    client_identifier: str = Field(
        "ip", description="How to identify clients (ip, user, api_key)"
    )


class RoleLimits(BaseModel):
    """Rate limits based on user role."""

    user: int = Field(60, description="Requests per minute for regular users")
    business: int = Field(120, description="Requests per minute for business accounts")
    admin: int = Field(300, description="Requests per minute for admins")
    api: int = Field(600, description="Requests per minute for API clients")


# Mock user database - replace with actual DB in production
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "disabled": False,
        "role": "admin",
        "hashed_password": pwd_context.hash("password"),
        "scopes": [
            "users:read",
            "users:write",
            "agents:read",
            "agents:write",
            "workflows:admin",
        ],
    },
    "user": {
        "username": "user",
        "email": "user@example.com",
        "full_name": "Regular User",
        "disabled": False,
        "role": "user",
        "hashed_password": pwd_context.hash("password"),
        "scopes": ["users:read", "agents:read"],
    },
    "business": {
        "username": "business",
        "email": "business@example.com",
        "full_name": "Business Account",
        "disabled": False,
        "role": "business",
        "hashed_password": pwd_context.hash("password"),
        "scopes": ["users:read", "agents:read", "agents:write"],
    },
}


# API keys for webhook authorization
# In production, store these securely in a database
api_keys = {
    "3f7d0c8e9a5b2f1e6d4c7b0a3f9e2d5c8b7a4f1e0d3c6b9": {
        "client": "webhook-service",
        "scopes": ["webhooks:all"],
        "role": "api",
    },
    "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3": {
        "client": "integration-service",
        "scopes": ["integrations:read", "integrations:write"],
        "role": "api",
    },
}


def verify_password(plain_password, hashed_password):
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Hash a password for storing."""
    return pwd_context.hash(password)


def get_user(db, username: str):
    """Get a user from the database."""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(db, username: str, password: str):
    """Authenticate a user."""
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create an access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire


def create_refresh_token(data: dict):
    """Create a refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validate and return the current user from a JWT token.

    This function uses a circuit breaker to prevent cascading failures
    if the authentication service is experiencing issues.
    """
    credentials_exception = AuthenticationException(
        message="Could not validate credentials",
        details={"headers": {"WWW-Authenticate": "Bearer"}},
    )

    try:
        # Execute through circuit breaker
        async def decode_token():
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                username = payload.get("sub")
                if username is None:
                    raise credentials_exception
                if username is None:
                    raise credentials_exception

                token_scopes = payload.get("scopes", [])
                token_role = payload.get("role", "user")
                token_data = TokenData(
                    sub=username,
                    scopes=token_scopes,
                    role=token_role,
                    exp=datetime.fromtimestamp(payload.get("exp", 0)),
                )
                return token_data
            except JWTError:
                raise credentials_exception

        token_data = await auth_circuit.execute(decode_token)

        # Verify the user exists
        user = get_user(fake_users_db, token_data.sub)
        if user is None:
            raise credentials_exception

        return user

    except CircuitOpenException as e:
        # If the circuit is open, provide a more specific error
        raise AuthenticationException(
            message="Authentication service is currently unavailable",
            details={
                "retry_after": e.details.get("remaining_seconds", 60),
                "circuit_state": e.details.get("circuit_state"),
            },
        )


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Check if the user is active."""
    if current_user.disabled:
        raise AuthorizationException(
            message="Inactive user", details={"username": current_user.username}
        )
    return current_user


def validate_api_key(api_key: str = Depends(api_key_header)):
    """
    Validate the API key for webhook endpoints.

    Args:
        api_key: The API key from the header

    Returns:
        dict: API key information including client and scopes

    Raises:
        AuthenticationException: If the API key is invalid
    """
    if api_key not in api_keys:
        raise AuthenticationException(
            message="Invalid API key", details={"header": "X-API-Key"}
        )

    return api_keys[api_key]


class RoleChecker:
    """
    Dependency for checking user roles.

    Usage:
        @app.get("/admin")
        async def admin_route(
            current_user: User = Depends(get_current_active_user),
            _: None = Depends(RoleChecker(["admin"]))
        ):
            return {"message": "Admin access granted"}
    """

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_active_user)):
        if user.role not in self.allowed_roles:
            raise AuthorizationException(
                message="Insufficient permissions",
                details={
                    "required_role": self.allowed_roles,
                    "current_role": user.role,
                },
            )
        return None


def require_scopes(required_scopes: List[str]):
    """
    Dependency for checking user scopes/permissions.

    Usage:
        @app.get("/users")
        async def list_users(
            current_user: User = Depends(get_current_active_user),
            _: None = Depends(require_scopes(["users:read"]))
        ):
            return {"users": [...]}
    """

    def check_scopes(user: User = Depends(get_current_active_user)):
        user_scopes = set(user.scopes)
        missing_scopes = [
            scope for scope in required_scopes if scope not in user_scopes
        ]

        if missing_scopes:
            raise AuthorizationException(
                message="Insufficient permissions",
                details={
                    "required_scopes": required_scopes,
                    "missing_scopes": missing_scopes,
                },
            )
        return None

    return check_scopes


class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting middleware with role-based limits and Redis backend.

    This implementation:
    1. Uses Redis for distributed rate limiting
    2. Applies different limits based on user roles
    3. Supports IP-based, user-based, or API key-based rate limiting
    4. Implements token bucket algorithm with burst capacity
    """

    def __init__(
        self,
        app,
        redis_url: Optional[str] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
        role_limits: Optional[RoleLimits] = None,
        exclude_paths: Optional[List[str]] = None,
    ):
        """Initialize the rate limiting middleware."""
        super().__init__(app)
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = redis.from_url(self.redis_url)
        self.config = rate_limit_config or RateLimitConfig(
            requests_per_minute=60, burst_capacity=20, client_identifier="ip"
        )
        self.role_limits = role_limits or RoleLimits(
            user=60, business=120, admin=300, api=600
        )
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
        ]

        # Error handler for standardized error responses
        self.error_handler = ErrorHandler()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        """Rate limit requests based on client identity and role."""
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Determine client identifier
        client_id = await self._get_client_identifier(request)

        # Determine rate limit based on authentication
        requests_per_minute = await self._get_rate_limit(request)

        # Check rate limit using token bucket algorithm
        rate_key = f"rate_limit:{client_id}"

        # Token bucket implementation in Redis
        now = time.time()
        bucket_key = f"{rate_key}:bucket"
        last_update_key = f"{rate_key}:last_update"

        # Script for atomic token bucket implementation in Redis
        # This ensures that concurrent requests don't lead to race conditions
        token_bucket_script = """
        local bucket_key = KEYS[1]
        local last_update_key = KEYS[2]
        local now = tonumber(ARGV[1])
        local rate = tonumber(ARGV[2])
        local burst = tonumber(ARGV[3])
        local cost = tonumber(ARGV[4])
        
        -- Get current tokens and last update time
        local tokens = tonumber(redis.call('get', bucket_key) or burst)
        local last_update = tonumber(redis.call('get', last_update_key) or 0)
        
        -- Calculate token refill based on time elapsed
        local elapsed = math.max(0, now - last_update)
        local new_tokens = math.min(burst, tokens + elapsed * (rate / 60.0))
        
        -- Check if enough tokens for request
        local allowed = new_tokens >= cost
        
        -- Update tokens if request is allowed
        if allowed then
            redis.call('set', bucket_key, new_tokens - cost)
            redis.call('set', last_update_key, now)
            redis.call('expire', bucket_key, 120)  -- 2 minute expiry
            redis.call('expire', last_update_key, 120)
            return 1
        else
            -- Calculate wait time until enough tokens
            local wait_time = math.ceil((cost - new_tokens) * 60.0 / rate)
            return -wait_time
        end
        """

        try:
            # Execute token bucket algorithm atomically in Redis
            result = self.redis.eval(
                token_bucket_script,
                2,  # Number of keys
                bucket_key,
                last_update_key,
                now,  # Current time
                requests_per_minute,  # Rate (requests per minute)
                self.config.burst_capacity,  # Burst capacity
                1,  # Cost of this request
            )

            # If result is positive, request is allowed
            if result > 0:
                # Process the request
                return await call_next(request)
            else:
                # Request is rate limited, wait_time is the negative result
                wait_time = abs(int(result))

                # Create a standardized error response
                error_response = await self.error_handler.log_error(
                    message="Rate limit exceeded",
                    error_code="RATE_LIMIT_EXCEEDED",
                    severity=ErrorSeverity.WARNING,
                    category=ErrorCategory.AUTHENTICATION,
                    details={
                        "client_id": client_id,
                        "retry_after": wait_time,
                        "limit": requests_per_minute,
                        "path": request.url.path,
                    },
                    log_to_notion=False,
                )

                return Response(
                    content=json.dumps(error_response.to_dict()),
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    headers={"Retry-After": str(wait_time)},
                    media_type="application/json",
                )

        except Exception as e:
            # If Redis fails, log the error but allow the request to proceed
            # This prevents the rate limiter from blocking all traffic on failure
            print(f"Rate limiting error: {str(e)}")
            return await call_next(request)

    async def _get_client_identifier(self, request: Request) -> str:
        """
        Determine the client identifier based on configuration.

        Args:
            request: The incoming request

        Returns:
            str: A unique identifier for the client
        """
        # Handle case where request.client might be None
        if not request.client:
            return "unknown_client"
        if self.config.client_identifier == "ip":
            return request.client.host
        elif self.config.client_identifier == "user":
            # Try to extract user from JWT token
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                try:
                    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                    if not payload:
                        return (
                            f"ip:{request.client.host if request.client else 'unknown'}"
                        )
                    return f"user:{payload.get('sub', 'anonymous')}"
                except JWTError:
                    pass
            return f"ip:{request.client.host}"
        elif self.config.client_identifier == "api_key":
            api_key = request.headers.get("X-API-Key", "")
            if api_key and api_key in api_keys:
                return f"api:{api_keys[api_key]['client']}"
            return f"ip:{request.client.host}"
        else:
            return request.client.host

    async def _get_rate_limit(self, request: Request) -> int:
        """
        Determine the rate limit based on user role or API key.

        Args:
            request: The incoming request

        Returns:
            int: Requests per minute allowed
        """
        # Check for API key
        api_key = request.headers.get("X-API-Key", "")
        if api_key and api_key in api_keys:
            return self.role_limits.api

        # Check for JWT token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                role = payload.get("role", "user")

                if role == "admin":
                    return self.role_limits.admin
                elif role == "business":
                    return self.role_limits.business
                else:
                    return self.role_limits.user
            except JWTError:
                pass

        # Default to basic user rate limit
        return self.role_limits.user


def setup_security(app: FastAPI):
    """
    Set up security middleware and endpoints for the application.

    Args:
        app: The FastAPI application
    """
    # Add rate limiting middleware
    rate_limit_config = RateLimitConfig(
        requests_per_minute=60, burst_capacity=20, client_identifier="ip"
    )

    role_limits = RoleLimits(user=60, business=120, admin=300, api=600)

    app.add_middleware(
        AdvancedRateLimitMiddleware,
        rate_limit_config=rate_limit_config,
        role_limits=role_limits,
        exclude_paths=["/health", "/metrics", "/docs", "/openapi.json", "/token"],
    )

    # Authentication endpoints
    @app.post("/token", response_model=Token)
    async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
        """Login endpoint to get JWT tokens."""
        user = authenticate_user(fake_users_db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create tokens
        token_data = {"sub": user.username, "scopes": user.scopes, "role": user.role}

        access_token, expires_at = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_at": expires_at,
        }

    @app.post("/token/refresh", response_model=Token)
    async def refresh_token(token: str = Depends(oauth2_scheme)):
        """Refresh an access token using a refresh token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Get user data
            user = get_user(fake_users_db, username)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Create new tokens
            token_data = {
                "sub": user.username,
                "scopes": user.scopes,
                "role": user.role,
            }

            access_token, expires_at = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_at": expires_at,
            }
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
