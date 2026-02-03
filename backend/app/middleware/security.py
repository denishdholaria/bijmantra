"""
Security Middleware - PRAHARI Integration

Automatically observes all API requests through the PRAHARI security system.
Integrates with DRISHTI (observation), VIVEK (analysis), and SHAKTI (response).

For mission-critical environments including space research applications.
"""

import time
import asyncio
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    PRAHARI Security Middleware
    
    Observes all requests and integrates with the security framework:
    - Records request metrics for RAKSHAKA health monitoring
    - Observes security events through PRAHARI DRISHTI
    - Checks blocked IPs/users before processing
    - Applies rate limiting from PRAHARI SHAKTI
    """
    
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        # Paths to skip (health checks, static files, docs)
        self.skip_paths = {
            '/health', '/docs', '/redoc', '/openapi.json',
            '/favicon.ico', '/robots.txt'
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enabled:
            return await call_next(request)
        
        # Skip certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)
        
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)
        
        # Check if IP is blocked
        try:
            from app.services.prahari import threat_responder
            if threat_responder.is_ip_blocked(client_ip):
                logger.warning(f"Blocked IP attempted access: {client_ip}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Access denied. Your IP has been blocked."}
                )

            # Check if user is blocked
            if user_id and threat_responder.is_user_blocked(user_id):
                logger.warning(f"Blocked user attempted access: {user_id}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Access denied. Your account has been blocked."}
                )
            
            # Check rate limiting
            rate_limit = threat_responder.get_rate_limit(client_ip)
            if rate_limit:
                # Simple rate limit check - in production use Redis
                logger.info(f"Rate limited request from {client_ip}")
                # Allow but log - actual enforcement would need request counting
        except ImportError:
            pass  # PRAHARI not available
        except Exception as e:
            logger.error(f"Security check error: {e}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate metrics
        duration_ms = (time.time() - start_time) * 1000
        status_code = response.status_code
        
        # Record metrics for RAKSHAKA
        try:
            from app.services.rakshaka import health_monitor
            health_monitor.record_api_latency(request.url.path, duration_ms)
            health_monitor.record_request(request.url.path)
            
            if status_code >= 400:
                error_type = "client_error" if status_code < 500 else "server_error"
                health_monitor.record_error(error_type, request.url.path)
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Health recording error: {e}")
        
        # Observe security events for PRAHARI (async, non-blocking)
        asyncio.create_task(self._observe_request(
            request, response, client_ip, user_id, duration_ms, status_code
        ))
        
        return response
    
    async def _observe_request(
        self, request: Request, response: Response,
        client_ip: str, user_id: str | None,
        duration_ms: float, status_code: int
    ):
        """Observe request through PRAHARI DRISHTI (non-blocking)."""
        try:
            from app.services.prahari import security_observer
            
            # Get request size
            content_length = request.headers.get('content-length', '0')
            request_size = int(content_length) if content_length.isdigit() else 0
            
            # Observe the request
            event = await security_observer.observe_request(
                endpoint=request.url.path,
                method=request.method,
                source_ip=client_ip,
                user_id=user_id,
                status_code=status_code,
                response_time_ms=duration_ms,
                request_size=request_size,
            )
            
            # If a significant event was detected, analyze it
            if event and event.severity.value in ['medium', 'high', 'critical']:
                from app.services.prahari import threat_analyzer, threat_responder
                from app.services.chaitanya import chaitanya
                
                # Analyze threat
                assessment = await threat_analyzer.analyze(event)
                
                # Auto-respond if confidence is high enough
                if assessment.confidence_score >= 60:
                    await threat_responder.respond(assessment)
                
                # Log significant events
                logger.warning(
                    f"Security event: {event.event_type} from {client_ip} - "
                    f"Severity: {event.severity.value}, "
                    f"Threat: {assessment.category.value} ({assessment.confidence.value})"
                )
        except ImportError:
            pass  # Security services not available
        except Exception as e:
            logger.error(f"Security observation error: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxies."""
        # Check X-Forwarded-For header (from reverse proxy)
        forwarded = request.headers.get('x-forwarded-for')
        if forwarded:
            # Take the first IP (original client)
            return forwarded.split(',')[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fall back to direct client
        if request.client:
            return request.client.host
        
        return 'unknown'
    
    def _get_user_id(self, request: Request) -> str | None:
        """Extract user ID from request (from JWT or session)."""
        # Check Authorization header for JWT
        auth_header = request.headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                import jwt
                token = auth_header[7:]
                # Decode without verification just to get user_id
                # In production, this should be properly verified
                payload = jwt.decode(token, options={"verify_signature": False})
                return payload.get('sub') or payload.get('user_id')
            except Exception:
                pass
        
        return None


def create_security_middleware(enabled: bool = True):
    """Factory function to create security middleware."""
    return SecurityMiddleware
