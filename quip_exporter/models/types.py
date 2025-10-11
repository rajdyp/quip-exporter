"""Type definitions for Quip data structures."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ThreadMeta:
    """Metadata for a Quip thread (document)."""
    id: str
    title: str
    updated_usec: Optional[int] = None
    url: Optional[str] = None
    folder_path: Optional[str] = None  # Relative path from root folder