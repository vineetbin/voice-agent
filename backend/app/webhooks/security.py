"""Webhook security utilities for signature verification.

Retell AI signs webhook payloads to ensure they're authentic.
This module provides utilities to verify those signatures.
"""

import hmac
import hashlib
from typing import Optional

from fastapi import Request, HTTPException, status, Depends

from app.core.config import get_settings


async def get_raw_body(request: Request) -> bytes:
    """
    Get the raw request body for signature verification.
    
    FastAPI consumes the body when parsing JSON, so we need to
    read it before the route handler processes it.
    """
    return await request.body()


def verify_retell_signature(
    payload: bytes,
    signature: Optional[str],
    secret: str,
) -> bool:
    """
    Verify the Retell webhook signature.
    
    Retell uses HMAC-SHA256 to sign webhook payloads.
    
    Args:
        payload: Raw request body bytes
        signature: Signature from X-Retell-Signature header
        secret: Webhook secret from Retell dashboard
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not signature:
        return False
    
    if not secret:
        # If no secret configured, skip verification (development mode)
        return True
    
    # Compute expected signature
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(signature, expected_signature)


async def verify_webhook_signature(
    request: Request,
) -> bytes:
    """
    FastAPI dependency for webhook signature verification.
    
    Usage:
        @router.post("/webhook")
        async def handle_webhook(
            body: bytes = Depends(verify_webhook_signature)
        ):
            ...
    
    Returns the raw body if signature is valid.
    Raises HTTPException 401 if signature is invalid.
    """
    settings = get_settings()
    
    # Get raw body
    body = await request.body()
    
    # Get signature from header
    signature = request.headers.get("X-Retell-Signature")
    
    # In development/simulated mode, skip verification
    if settings.call_mode == "simulated":
        return body
    
    # Verify signature
    if not verify_retell_signature(body, signature, settings.retell_webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
    
    return body


class WebhookAuthenticator:
    """
    Class-based authenticator for more complex verification scenarios.
    
    Can be extended to support multiple webhook providers.
    """
    
    def __init__(self, secret: str, skip_in_dev: bool = True):
        self.secret = secret
        self.skip_in_dev = skip_in_dev
    
    def verify(self, payload: bytes, signature: Optional[str]) -> bool:
        """Verify webhook signature."""
        return verify_retell_signature(payload, signature, self.secret)
    
    async def __call__(self, request: Request) -> bytes:
        """Make authenticator callable as a FastAPI dependency."""
        body = await request.body()
        signature = request.headers.get("X-Retell-Signature")
        
        settings = get_settings()
        if self.skip_in_dev and settings.call_mode == "simulated":
            return body
        
        if not self.verify(body, signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        return body

