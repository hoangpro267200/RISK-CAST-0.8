"""
Request signing for tamper protection.

RISKCAST v17 - Cryptographic Request Signing

This module provides HMAC-SHA256 based request signing for
sensitive operations like financial transactions, batch operations,
and administrative actions.
"""

import hmac
import hashlib
import json
import time
import base64
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import os


class RequestSigner:
    """
    Request signing utility for client applications.
    
    Usage (Python client):
        signer = RequestSigner(secret="your-secret-key")
        payload = {"action": "transfer", "amount": 1000}
        signature = signer.sign(payload)
        
        # Include in request headers
        headers = {"X-Signature": signature}
    
    Usage (JavaScript client):
        const crypto = require('crypto');
        
        function signPayload(payload, secret) {
            const data = JSON.stringify(payload, Object.keys(payload).sort());
            return crypto.createHmac('sha256', secret)
                        .update(data)
                        .digest('hex');
        }
    """
    
    def __init__(self, secret: Optional[str] = None):
        """
        Initialize signer with secret key.
        
        Args:
            secret: Secret key for signing. If not provided, uses
                   REQUEST_SIGNING_SECRET environment variable.
        """
        self.secret = secret or os.getenv('REQUEST_SIGNING_SECRET', '')
        
        if not self.secret:
            raise ValueError(
                "Signing secret required. Set REQUEST_SIGNING_SECRET "
                "environment variable or pass secret to constructor."
            )
    
    def sign(self, payload: Dict[str, Any]) -> str:
        """
        Generate HMAC-SHA256 signature for payload.
        
        Args:
            payload: Dictionary to sign
        
        Returns:
            Hex-encoded signature
        """
        return sign_payload(payload, self.secret)
    
    def verify(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Verify payload signature.
        
        Args:
            payload: Original payload dictionary
            signature: Signature to verify
        
        Returns:
            True if signature is valid
        """
        return verify_signature(payload, signature, self.secret)
    
    def sign_with_timestamp(
        self,
        payload: Dict[str, Any],
        timestamp: Optional[float] = None
    ) -> Tuple[str, float]:
        """
        Sign payload with embedded timestamp.
        
        Adds timestamp to payload before signing, providing
        replay attack protection.
        
        Args:
            payload: Dictionary to sign
            timestamp: Optional timestamp (defaults to current time)
        
        Returns:
            (signature, timestamp) tuple
        """
        ts = timestamp or time.time()
        payload_with_ts = {**payload, '_timestamp': ts}
        signature = self.sign(payload_with_ts)
        return signature, ts
    
    def verify_with_timestamp(
        self,
        payload: Dict[str, Any],
        signature: str,
        timestamp: float,
        max_age_seconds: int = 300  # 5 minutes default
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify signature with timestamp validation.
        
        Args:
            payload: Original payload
            signature: Signature to verify
            timestamp: Timestamp from request
            max_age_seconds: Maximum age of request
        
        Returns:
            (valid, error_message) tuple
        """
        # Check timestamp age
        age = time.time() - timestamp
        
        if age > max_age_seconds:
            return False, f"Request too old: {age:.0f}s (max: {max_age_seconds}s)"
        
        if age < -60:  # Allow 1 minute clock skew
            return False, "Request timestamp in the future"
        
        # Verify signature
        payload_with_ts = {**payload, '_timestamp': timestamp}
        if not self.verify(payload_with_ts, signature):
            return False, "Invalid signature"
        
        return True, None


def sign_payload(payload: Dict[str, Any], secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for payload.
    
    The payload is serialized deterministically (sorted keys, no spaces)
    to ensure consistent signatures across different systems.
    
    Args:
        payload: Dictionary to sign
        secret: Secret key for signing
    
    Returns:
        Hex-encoded signature (64 characters)
    """
    # Serialize payload deterministically
    payload_bytes = json.dumps(
        payload,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=True
    ).encode('utf-8')
    
    # Generate HMAC-SHA256 signature
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    return signature


def verify_signature(
    payload: Dict[str, Any],
    signature: str,
    secret: str
) -> bool:
    """
    Verify payload signature using constant-time comparison.
    
    Args:
        payload: Original payload dictionary
        signature: Signature to verify (hex-encoded)
        secret: Secret key
    
    Returns:
        True if signature is valid, False otherwise
    """
    expected_signature = sign_payload(payload, secret)
    
    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(signature.lower(), expected_signature.lower())


def create_signed_url(
    base_url: str,
    params: Dict[str, Any],
    secret: str,
    expires_in: int = 3600
) -> str:
    """
    Create a signed URL with expiration.
    
    Useful for:
    - Pre-signed download links
    - Email verification links
    - Password reset links
    
    Args:
        base_url: Base URL (e.g., "https://api.riskcast.io/download")
        params: URL parameters
        secret: Signing secret
        expires_in: Expiration time in seconds
    
    Returns:
        Signed URL with signature and expiry
    """
    expires = int(time.time()) + expires_in
    
    # Add expiry to params
    sign_params = {**params, '_expires': expires}
    
    # Generate signature
    signature = sign_payload(sign_params, secret)
    
    # Build URL
    from urllib.parse import urlencode
    query_string = urlencode({**params, '_expires': expires, '_sig': signature})
    
    return f"{base_url}?{query_string}"


def verify_signed_url(url: str, secret: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Verify a signed URL.
    
    Args:
        url: Full URL with signature
        secret: Signing secret
    
    Returns:
        (valid, params, error_message) tuple
    """
    from urllib.parse import urlparse, parse_qs
    
    parsed = urlparse(url)
    params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    
    # Extract signature and expiry
    signature = params.pop('_sig', None)
    expires = params.pop('_expires', None)
    
    if not signature or not expires:
        return False, None, "Missing signature or expiry"
    
    try:
        expires = int(expires)
    except ValueError:
        return False, None, "Invalid expiry format"
    
    # Check expiry
    if time.time() > expires:
        return False, None, "URL has expired"
    
    # Rebuild params for verification
    sign_params = {**params, '_expires': expires}
    
    # Verify signature
    if not verify_signature(sign_params, signature, secret):
        return False, None, "Invalid signature"
    
    return True, params, None


# ============================================================
# WEBHOOK SIGNING
# ============================================================

class WebhookSigner:
    """
    Sign outgoing webhooks for verification by recipients.
    
    Usage:
        signer = WebhookSigner(secret="webhook-secret")
        
        # When sending webhook
        payload = {"event": "risk.analyzed", "data": {...}}
        headers = signer.get_headers(payload)
        
        requests.post(webhook_url, json=payload, headers=headers)
    
    Recipient verification:
        signature = request.headers.get('X-Webhook-Signature')
        timestamp = request.headers.get('X-Webhook-Timestamp')
        
        signer.verify_webhook(payload, signature, timestamp)
    """
    
    def __init__(self, secret: str):
        self.secret = secret
    
    def get_headers(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Get headers for webhook request.
        
        Returns:
            Dictionary with X-Webhook-Signature and X-Webhook-Timestamp
        """
        timestamp = str(int(time.time()))
        
        # Sign: timestamp + payload
        sign_data = f"{timestamp}.{json.dumps(payload, sort_keys=True)}"
        signature = hmac.new(
            self.secret.encode(),
            sign_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            'X-Webhook-Signature': signature,
            'X-Webhook-Timestamp': timestamp,
            'Content-Type': 'application/json'
        }
    
    def verify_webhook(
        self,
        payload: Dict[str, Any],
        signature: str,
        timestamp: str,
        tolerance: int = 300
    ) -> bool:
        """
        Verify incoming webhook signature.
        
        Args:
            payload: Webhook payload
            signature: X-Webhook-Signature header
            timestamp: X-Webhook-Timestamp header
            tolerance: Maximum age in seconds (default 5 minutes)
        
        Returns:
            True if valid
        """
        try:
            ts = int(timestamp)
        except ValueError:
            return False
        
        # Check timestamp
        if abs(time.time() - ts) > tolerance:
            return False
        
        # Verify signature
        sign_data = f"{timestamp}.{json.dumps(payload, sort_keys=True)}"
        expected = hmac.new(
            self.secret.encode(),
            sign_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)


# ============================================================
# TOKEN GENERATION
# ============================================================

def generate_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    import secrets
    return secrets.token_urlsafe(length)


def generate_api_key() -> str:
    """Generate an API key with prefix."""
    import secrets
    return f"rsk_{secrets.token_urlsafe(32)}"


# ============================================================
# DEMO / TESTING
# ============================================================

if __name__ == "__main__":
    # Demo usage
    secret = "demo-secret-key"
    
    print("=== Request Signing Demo ===\n")
    
    # Basic signing
    payload = {"action": "analyze", "shipment_id": "SHP123", "value": 50000}
    signature = sign_payload(payload, secret)
    print(f"Payload: {payload}")
    print(f"Signature: {signature}")
    print(f"Verified: {verify_signature(payload, signature, secret)}")
    
    print("\n=== Signed URL Demo ===\n")
    
    # Signed URL
    url = create_signed_url(
        "https://api.riskcast.io/reports/download",
        {"report_id": "RPT456"},
        secret,
        expires_in=3600
    )
    print(f"Signed URL: {url}")
    
    valid, params, error = verify_signed_url(url, secret)
    print(f"Valid: {valid}, Params: {params}")
    
    print("\n=== Webhook Signing Demo ===\n")
    
    # Webhook
    webhook_signer = WebhookSigner(secret)
    webhook_payload = {"event": "risk.analyzed", "risk_score": 67.5}
    headers = webhook_signer.get_headers(webhook_payload)
    print(f"Webhook headers: {headers}")
