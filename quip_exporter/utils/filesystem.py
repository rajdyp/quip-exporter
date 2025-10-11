"""Filesystem utility functions."""

import os
import re
from pathlib import Path

def slugify(name: str) -> str:
    """Convert a string to a safe filename."""
    name = (name or "").strip().replace("/", "-")
    name = re.sub(r"[\t\r\n]+", " ", name)
    safe = re.sub(r"[^A-Za-z0-9._ \-\(\)\[\]]+", "", name).strip()
    return (safe[:150] or "untitled").rstrip(" .")

def ensure_dir(p: Path) -> None:
    """Create directory and parents if they don't exist."""
    p.mkdir(parents=True, exist_ok=True)

def safe_write_atomic(path: Path, data: bytes) -> None:
    """Write data to file atomically using a temporary file."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)

def filename_from_url(url: str) -> str:
    """Extract a safe filename from a URL."""
    base = os.path.basename(url.split("?")[0].split("#")[0]) or "image"
    return slugify(base)