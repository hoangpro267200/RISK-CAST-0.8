"""
Shared Utility Functions
RISKCAST V3 - Modular Monolith
"""
import time
import random
import struct
from typing import Optional


def generate_ulid() -> str:
    """
    Generate a ULID (Universally Unique Lexicographically Sortable Identifier).
    
    ULID format: 26 characters, base32 encoded
    - 48 bits timestamp (milliseconds since epoch)
    - 80 bits random
    
    Returns:
        ULID string (26 characters)
    """
    # Get current timestamp in milliseconds
    timestamp_ms = int(time.time() * 1000)
    
    # Generate 80 bits of random data (10 bytes)
    random_bytes = struct.pack('>Q', random.getrandbits(64))[:10]
    
    # Combine timestamp (6 bytes) and random (10 bytes)
    timestamp_bytes = struct.pack('>Q', timestamp_ms)[2:8]  # Take 6 bytes
    ulid_bytes = timestamp_bytes + random_bytes
    
    # Base32 encoding (RFC 4648, no padding)
    base32_chars = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
    ulid = ''
    value = 0
    bits = 0
    
    for byte in ulid_bytes:
        value = (value << 8) | byte
        bits += 8
        while bits >= 5:
            ulid += base32_chars[(value >> (bits - 5)) & 0x1F]
            bits -= 5
    
    if bits > 0:
        ulid += base32_chars[(value << (5 - bits)) & 0x1F]
    
    return ulid[:26]


def parse_ulid(ulid: str) -> Optional[dict]:
    """
    Parse ULID to extract timestamp and random components.
    
    Args:
        ulid: ULID string
        
    Returns:
        Dictionary with 'timestamp_ms' and 'random_bytes', or None if invalid
    """
    if len(ulid) != 26:
        return None
    
    try:
        base32_chars = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
        # Decode base32
        value = 0
        bits = 0
        bytes_list = []
        
        for char in ulid:
            value = (value << 5) | base32_chars.index(char.upper())
            bits += 5
            if bits >= 8:
                bytes_list.append((value >> (bits - 8)) & 0xFF)
                bits -= 8
        
        if len(bytes_list) != 16:
            return None
        
        # Extract timestamp (first 6 bytes) and random (last 10 bytes)
        timestamp_bytes = bytes(bytes_list[:6])
        random_bytes = bytes(bytes_list[6:])
        
        # Convert timestamp bytes to milliseconds
        timestamp_ms = int.from_bytes(b'\x00\x00' + timestamp_bytes, 'big')
        
        return {
            'timestamp_ms': timestamp_ms,
            'random_bytes': random_bytes
        }
    except Exception:
        return None


def build_audit_context(request: Optional['Request']) -> 'AuditContext':
    """
    Build audit context from FastAPI request.
    
    Args:
        request: FastAPI request object (optional)
        
    Returns:
        AuditContext with request information
    """
    # Lazy import to avoid circular dependency
    from app.modules.audit_ledger.schemas import AuditContext
    
    if request is None:
        return AuditContext()
    
    # Get request ID from state (set by middleware)
    request_id = getattr(request.state, "request_id", None)
    
    # Get trace ID from headers or state
    trace_id = (
        request.headers.get("X-Trace-Id") or
        getattr(request.state, "trace_id", None)
    )
    
    # Get client IP
    client_ip = None
    if request.client:
        client_ip = request.client.host
    
    # Get user agent
    user_agent = request.headers.get("user-agent")
    
    # Get route and method
    route = str(request.url.path) if request.url else None
    method = request.method
    
    return AuditContext(
        request_id=request_id,
        trace_id=trace_id,
        ip=client_ip,
        user_agent=user_agent,
        route=route,
        method=method
    )
