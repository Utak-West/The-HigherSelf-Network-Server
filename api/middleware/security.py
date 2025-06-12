"""
Security middleware for the Higher Self Network Server.
Implements rate limiting, request validation, and security checks.
"""

import json
import os
import time
from typing import Any, Callable, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, Response
from fastapi.security import APIKeyHeader
from loguru import logger
from prometheus_client import Counter, Histogram
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_429_TOO_MANY_REQUESTS,
)

from services.redis_service import redis_service

# Metrics for monitoring
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint", "status_code"],
)
REQUEST_COUNT = Counter(
    "http_requests_total", "HTTP requests count", ["method", "endpoint", "status_code"]
)
REQUEST_REJECTED = Counter(
    "http_requests_rejected_total",
    "HTTP requests rejected count",
    ["method", "endpoint", "reason"],
)


class RateLimitConfig(BaseModel):
    """Rate limit configuration for endpoints."""

    requests_per_minute: int = Field(
        60, description="Number of requests allowed per minute"
    )
    burst: int = Field(10, description="Burst capacity for request spikes")
    key_prefix: str = Field(
        "rate_limit", description="Redis key prefix for rate limiting"
    )


class SecurityConfig(BaseModel):
    """Security configuration for the API gateway."""

    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    whitelisted_ips: List[str] = Field(
        default_factory=list, description="IP addresses exempt from rate limiting"
    )
    blacklisted_ips: List[str] = Field(
        default_factory=list, description="Blocked IP addresses"
    )
    sensitive_endpoints: List[str] = Field(
        default_factory=list, description="Endpoints requiring additional protection"
    )
    api_key_header_name: str = Field(
        "X-API-Key", description="Header name for API key authentication"
    )


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request validation.

    Validates incoming requests for:
    - Body size limits
    - JSON format (for POST, PUT, PATCH)
    - Required headers
    - Content-Type validation
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate incoming requests."""

        # Check content-type for POST/PUT/PATCH requests
        if (
            request.method in ["POST", "PUT", "PATCH"]
            and request.headers.get("content-type") != "application/json"
        ):
            REQUEST_REJECTED.labels(
                method=request.method,
                endpoint=request.url.path,
                reason="invalid_content_type",
            ).inc()
            return Response(
                content=json.dumps({"detail": "Content-Type must be application/json"}),
                status_code=415,
                media_type="application/json",
            )

        # Check body size limit (10MB)
        if (
            request.headers.get("content-length")
            and int(request.headers["content-length"]) > 10_485_760
        ):
            REQUEST_REJECTED.labels(
                method=request.method,
                endpoint=request.url.path,
                reason="request_too_large",
            ).inc()
            return Response(
                content=json.dumps({"detail": "Request body too large"}),
                status_code=413,
                media_type="application/json",
            )

        # Process the request
        try:
            response = await call_next(request)
            return response
        except json.JSONDecodeError:
            REQUEST_REJECTED.labels(
                method=request.method, endpoint=request.url.path, reason="invalid_json"
            ).inc()
            return Response(
                content=json.dumps({"detail": "Invalid JSON format"}),
                status_code=400,
                media_type="application/json",
            )
        except Exception as e:
            logger.error(f"Error in RequestValidationMiddleware: {str(e)}")
            return Response(
                content=json.dumps({"detail": "Internal server error"}),
                status_code=500,
                media_type="application/json",
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API rate limiting.

    Implements token bucket rate limiting using Redis.
    """

    def __init__(self, app, config: SecurityConfig):
        """Initialize with security configuration."""
        super().__init__(app)
        self.config = config

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Implement rate limiting for requests."""
        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/metrics", "/_cluster/health"]:
            return await call_next(request)

        # Skip rate limiting for whitelisted IPs
        client_ip = request.client.host
        if client_ip in self.config.whitelisted_ips:
            return await call_next(request)

        # Block blacklisted IPs immediately
        if client_ip in self.config.blacklisted_ips:
            REQUEST_REJECTED.labels(
                method=request.method,
                endpoint=request.url.path,
                reason="blacklisted_ip",
            ).inc()
            return Response(
                content=json.dumps({"detail": "Access denied"}),
                status_code=HTTP_403_FORBIDDEN,
                media_type="application/json",
            )

        # Check rate limit
        rate_key = f"{self.config.rate_limit.key_prefix}:{client_ip}"

        current_time = time.time()
        window_start = current_time - 60  # 1 minute window

        # Get recent requests within window
        async def get_requests():
            requests = await redis_service.async_get(rate_key, as_json=True)
            return requests if requests else []

        requests = await get_requests()

        # Filter requests within current window
        recent_requests = [req for req in requests if req > window_start]

        # Check if under limit
        if len(recent_requests) >= self.config.rate_limit.requests_per_minute:
            REQUEST_REJECTED.labels(
                method=request.method, endpoint=request.url.path, reason="rate_limited"
            ).inc()

            # Calculate retry-after time
            retry_after = 60 - int(current_time - min(recent_requests))

            return Response(
                content=json.dumps(
                    {"detail": "Too many requests", "retry_after": retry_after}
                ),
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(retry_after)},
                media_type="application/json",
            )

        # Record current request
        recent_requests.append(current_time)
        await redis_service.async_set(
            rate_key, recent_requests, ex=120
        )  # 2 minute expiry

        # Start timing the request
        start_time = time.time()

        # Process the request
        response = await call_next(request)

        # Record metrics
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).observe(duration)

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).inc()

        return response


class AgentAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for agent authentication.

    Validates agent requests based on Agent Communication Security rules.
    Enforces the Agent Autonomy Boundaries from server rules.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Enforce agent authorization rules."""
        # Skip authentication for non-agent endpoints
        if not request.url.path.startswith("/api/agents"):
            return await call_next(request)

        # Extract agent ID and target from request
        agent_id = request.headers.get("X-Agent-ID")
        target_agent_id = request.headers.get("X-Target-Agent-ID")

        # Require agent identification
        if not agent_id:
            REQUEST_REJECTED.labels(
                method=request.method,
                endpoint=request.url.path,
                reason="missing_agent_id",
            ).inc()
            return Response(
                content=json.dumps({"detail": "Missing X-Agent-ID header"}),
                status_code=HTTP_401_UNAUTHORIZED,
                media_type="application/json",
            )

        # Check if inter-agent communication
        if target_agent_id:
            # Verify the communication pattern is authorized
            is_authorized = await self._check_agent_communication_pattern(
                agent_id, target_agent_id, request.url.path
            )

            if not is_authorized:
                REQUEST_REJECTED.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    reason="unauthorized_agent_communication",
                ).inc()
                return Response(
                    content=json.dumps(
                        {
                            "detail": f"Communication from {agent_id} to {target_agent_id} is not authorized"
                        }
                    ),
                    status_code=HTTP_403_FORBIDDEN,
                    media_type="application/json",
                )

        # Process the request
        response = await call_next(request)
        return response

    async def _check_agent_communication_pattern(
        self, source_agent: str, target_agent: str, path: str
    ) -> bool:
        """
        Check if the communication pattern between agents is authorized.

        Args:
            source_agent: The agent initiating the communication
            target_agent: The target agent
            path: The API path being accessed

        Returns:
            True if the communication is authorized, False otherwise
        """
        try:
            # Look up authorized communication patterns from MongoDB
            from services.mongodb_service import mongo_service

            # Query the agent communication registry
            pattern = await mongo_service.async_find_one(
                "agent_communication_registry",
                {
                    "$or": [
                        {
                            "authorized_source_agents": {"$in": [source_agent, "*"]},
                            "authorized_target_agents": {"$in": [target_agent, "*"]},
                        },
                        {"authorized_paths": {"$in": [path, "*"]}},
                    ]
                },
            )

            return pattern is not None
        except Exception as e:
            # Log the error but default to deny on failures (secure default)
            logger.error(f"Error checking agent communication pattern: {e}")
            return False


# API key security scheme for protected endpoints
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key: str = Depends(api_key_header)) -> str:
    """
    Validate API key for protected endpoints.

    Args:
        api_key: The API key from the X-API-Key header

    Returns:
        The API key if valid

    Raises:
        HTTPException: If the API key is missing or invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Validate against stored API keys
    # This could check against Redis, MongoDB, or environment variables
    valid_api_keys = {
        os.environ.get("API_KEY", "default_key"): "default",
        os.environ.get("ADMIN_API_KEY", "admin_key"): "admin",
    }

    if api_key not in valid_api_keys:
        REQUEST_REJECTED.labels(
            method="ANY", endpoint="ANY", reason="invalid_api_key"
        ).inc()
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Return the API key role for use in endpoint handlers
    return valid_api_keys[api_key]
