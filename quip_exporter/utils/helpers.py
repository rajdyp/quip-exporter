"""General helper functions."""

import hashlib
import os
import re
from typing import Optional

def env_default(name: str, fallback: Optional[str] = None) -> Optional[str]:
    """Get environment variable with optional fallback."""
    v = os.environ.get(name)
    return v if v is not None else fallback

def is_id(s: str) -> bool:
    """Check if string is a valid Quip ID format."""
    return bool(re.fullmatch(r"[A-Za-z0-9]+", s or ""))

def sha256_bytes(b: bytes) -> str:
    """Calculate SHA256 hash of bytes."""
    return hashlib.sha256(b).hexdigest()