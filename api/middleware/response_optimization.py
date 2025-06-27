"""
API Response Optimization Middleware for HigherSelf Network Server.

Provides response compression, caching headers, structured responses,
and performance optimizations for API endpoints.
"""

import gzip
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import asyncio

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger
from pydantic import BaseModel

from models.base import OptimizedBaseModel
from services.performance_monitoring_service import performance_monitor


class OptimizedResponse(OptimizedBaseModel):
    """Standardized optimized API response structure."""
    
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    request_id: Optional[str] = None
    execution_time_ms: Optional[float] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now()
        super().__init__(**data)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ResponseOptimizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for optimizing API responses.
    
    Features:
    - Response compression (gzip)
    - Structured response format
    - Performance monitoring
    - Caching headers
    - Response size optimization
    """
    
    def __init__(
        self,
        app: ASGIApp,
        compress_responses: bool = True,
        min_compression_size: int = 1024,
        enable_caching: bool = True,
        default_cache_ttl: int = 300
    ):
        super().__init__(app)
        self.compress_responses = compress_responses
        self.min_compression_size = min_compression_size
        self.enable_caching = enable_caching
        self.default_cache_ttl = default_cache_ttl
        
        # Performance tracking
        self.request_count = 0
        self.total_response_time = 0.0
        self.compression_savings = 0
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and optimize response."""
        start_time = time.time()
        request_id = self._generate_request_id()
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Optimize response
            optimized_response = await self._optimize_response(
                request, response, execution_time, request_id
            )
            
            # Record metrics
            self._record_metrics(request, optimized_response, execution_time)
            
            return optimized_response
            
        except Exception as e:
            # Handle errors with optimized error response
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Request {request_id} failed: {e}")
            
            error_response = self._create_error_response(
                str(e), execution_time, request_id
            )
            
            self._record_metrics(request, error_response, execution_time, success=False)
            return error_response
    
    async def _optimize_response(
        self,
        request: Request,
        response: Response,
        execution_time: float,
        request_id: str
    ) -> Response:
        """Optimize the response with compression and headers."""
        
        # Handle different response types
        if isinstance(response, JSONResponse):
            # Optimize JSON responses
            return await self._optimize_json_response(
                request, response, execution_time, request_id
            )
        else:
            # Optimize other response types
            return await self._optimize_generic_response(
                request, response, execution_time, request_id
            )
    
    async def _optimize_json_response(
        self,
        request: Request,
        response: JSONResponse,
        execution_time: float,
        request_id: str
    ) -> JSONResponse:
        """Optimize JSON responses."""
        
        # Get response content
        content = response.body
        
        # Parse existing content if it's JSON
        try:
            if isinstance(content, bytes):
                content_str = content.decode('utf-8')
                existing_data = json.loads(content_str)
            else:
                existing_data = content
        except (json.JSONDecodeError, UnicodeDecodeError):
            existing_data = {"raw_content": str(content)}
        
        # Create optimized response structure
        if not isinstance(existing_data, dict) or 'success' not in existing_data:
            # Wrap non-standard responses
            optimized_data = OptimizedResponse(
                success=response.status_code < 400,
                data=existing_data,
                execution_time_ms=execution_time,
                request_id=request_id
            )
        else:
            # Update existing structured response
            existing_data.update({
                'execution_time_ms': execution_time,
                'request_id': request_id,
                'timestamp': datetime.now().isoformat()
            })
            optimized_data = existing_data
        
        # Serialize response
        if isinstance(optimized_data, OptimizedResponse):
            response_content = optimized_data.model_dump_json()
        else:
            response_content = json.dumps(optimized_data, default=str)
        
        # Apply compression if enabled and beneficial
        if self.compress_responses and len(response_content) > self.min_compression_size:
            if self._should_compress(request):
                compressed_content = gzip.compress(response_content.encode('utf-8'))
                
                # Only use compression if it actually reduces size
                if len(compressed_content) < len(response_content):
                    self.compression_savings += len(response_content) - len(compressed_content)
                    
                    optimized_response = Response(
                        content=compressed_content,
                        status_code=response.status_code,
                        headers=response.headers,
                        media_type="application/json"
                    )
                    optimized_response.headers["content-encoding"] = "gzip"
                    optimized_response.headers["vary"] = "Accept-Encoding"
                else:
                    optimized_response = JSONResponse(
                        content=optimized_data if isinstance(optimized_data, dict) else optimized_data.model_dump(),
                        status_code=response.status_code,
                        headers=response.headers
                    )
            else:
                optimized_response = JSONResponse(
                    content=optimized_data if isinstance(optimized_data, dict) else optimized_data.model_dump(),
                    status_code=response.status_code,
                    headers=response.headers
                )
        else:
            optimized_response = JSONResponse(
                content=optimized_data if isinstance(optimized_data, dict) else optimized_data.model_dump(),
                status_code=response.status_code,
                headers=response.headers
            )
        
        # Add optimization headers
        self._add_optimization_headers(optimized_response, request)
        
        return optimized_response
    
    async def _optimize_generic_response(
        self,
        request: Request,
        response: Response,
        execution_time: float,
        request_id: str
    ) -> Response:
        """Optimize non-JSON responses."""
        
        # Add performance headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Execution-Time-MS"] = str(execution_time)
        
        # Apply compression for text responses
        if (self.compress_responses and 
            response.headers.get("content-type", "").startswith("text/") and
            len(response.body) > self.min_compression_size and
            self._should_compress(request)):
            
            compressed_content = gzip.compress(response.body)
            if len(compressed_content) < len(response.body):
                self.compression_savings += len(response.body) - len(compressed_content)
                
                response = Response(
                    content=compressed_content,
                    status_code=response.status_code,
                    headers=response.headers
                )
                response.headers["content-encoding"] = "gzip"
                response.headers["vary"] = "Accept-Encoding"
        
        # Add optimization headers
        self._add_optimization_headers(response, request)
        
        return response
    
    def _should_compress(self, request: Request) -> bool:
        """Check if response should be compressed based on request headers."""
        accept_encoding = request.headers.get("accept-encoding", "")
        return "gzip" in accept_encoding.lower()
    
    def _add_optimization_headers(self, response: Response, request: Request):
        """Add optimization and caching headers."""
        
        # Performance headers
        response.headers["X-Powered-By"] = "HigherSelf-Network-Server"
        response.headers["X-Response-Optimized"] = "true"
        
        # Caching headers for GET requests
        if self.enable_caching and request.method == "GET":
            # Check if endpoint should be cached
            cache_ttl = self._get_cache_ttl(request.url.path)
            if cache_ttl > 0:
                response.headers["Cache-Control"] = f"public, max-age={cache_ttl}"
                response.headers["Expires"] = (
                    datetime.now() + timedelta(seconds=cache_ttl)
                ).strftime("%a, %d %b %Y %H:%M:%S GMT")
            else:
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
    
    def _get_cache_ttl(self, path: str) -> int:
        """Get cache TTL for specific endpoint."""
        # Define caching rules for different endpoints
        cache_rules = {
            "/health": 60,           # 1 minute
            "/api/health": 60,       # 1 minute
            "/metrics": 30,          # 30 seconds
            "/api/agents": 300,      # 5 minutes
            "/api/workflows": 600,   # 10 minutes
        }
        
        # Check for exact matches first
        if path in cache_rules:
            return cache_rules[path]
        
        # Check for pattern matches
        if path.startswith("/api/static/"):
            return 3600  # 1 hour for static content
        elif path.startswith("/docs") or path.startswith("/redoc"):
            return 1800  # 30 minutes for documentation
        elif "health" in path:
            return 60    # 1 minute for health checks
        
        # Default: no caching for dynamic content
        return 0
    
    def _create_error_response(
        self,
        error_message: str,
        execution_time: float,
        request_id: str
    ) -> JSONResponse:
        """Create standardized error response."""
        
        error_response = OptimizedResponse(
            success=False,
            data=None,
            message="An error occurred while processing the request",
            errors=[error_message],
            execution_time_ms=execution_time,
            request_id=request_id
        )
        
        return JSONResponse(
            content=error_response.model_dump(),
            status_code=500,
            headers={
                "X-Request-ID": request_id,
                "X-Execution-Time-MS": str(execution_time),
                "X-Response-Optimized": "true"
            }
        )
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _record_metrics(
        self,
        request: Request,
        response: Response,
        execution_time: float,
        success: bool = True
    ):
        """Record performance metrics."""
        self.request_count += 1
        self.total_response_time += execution_time
        
        # Record in performance monitor
        performance_monitor.record_request(execution_time / 1000, success)  # Convert to seconds
        
        # Record detailed metrics
        performance_monitor.record_metric(
            "api_request_duration",
            execution_time,
            {
                "method": request.method,
                "path": request.url.path,
                "status_code": str(response.status_code),
                "success": str(success)
            }
        )
        
        # Record compression metrics
        if hasattr(response, 'headers') and response.headers.get("content-encoding") == "gzip":
            performance_monitor.record_metric(
                "response_compressed",
                1,
                {"path": request.url.path}
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get middleware performance metrics."""
        avg_response_time = (
            self.total_response_time / self.request_count
            if self.request_count > 0 else 0
        )
        
        return {
            "total_requests": self.request_count,
            "avg_response_time_ms": avg_response_time,
            "compression_enabled": self.compress_responses,
            "compression_savings_bytes": self.compression_savings,
            "caching_enabled": self.enable_caching
        }


def create_response_optimization_middleware(
    compress_responses: bool = True,
    min_compression_size: int = 1024,
    enable_caching: bool = True,
    default_cache_ttl: int = 300
) -> ResponseOptimizationMiddleware:
    """Factory function to create response optimization middleware."""
    
    def middleware_factory(app: ASGIApp) -> ResponseOptimizationMiddleware:
        return ResponseOptimizationMiddleware(
            app=app,
            compress_responses=compress_responses,
            min_compression_size=min_compression_size,
            enable_caching=enable_caching,
            default_cache_ttl=default_cache_ttl
        )
    
    return middleware_factory
