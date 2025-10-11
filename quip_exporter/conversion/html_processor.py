"""HTML processing and image downloading."""

import base64
from pathlib import Path
from typing import List, Tuple
import requests
from bs4 import BeautifulSoup

from quip_exporter.utils import ensure_dir, filename_from_url, safe_write_atomic
from quip_exporter.api import get_raw


def process_images(
    session: requests.Session,
    html: str,
    assets_dir: Path,
    relative_to: Path = None
) -> Tuple[BeautifulSoup, List[str]]:
    """
    Process images in HTML:
    - Download remote images
    - Convert data URLs to files
    - Rewrite src attributes to relative paths
    
    Args:
        session: Authenticated requests session
        html: HTML content to process
        assets_dir: Directory to save images
        relative_to: Directory to calculate relative paths from (defaults to assets_dir.parent)
        
    Returns:
        Tuple of (modified BeautifulSoup object, list of downloaded file paths)
    """
    ensure_dir(assets_dir)
    soup = BeautifulSoup(html, "html.parser")
    downloaded: List[str] = []
    
    # Default to assets_dir.parent if not specified
    if relative_to is None:
        relative_to = assets_dir.parent

    for img in soup.find_all("img"):
        src = (img.get("src") or "").strip()
        if not src:
            continue

        # Handle data URLs
        if src.startswith("data:"):
            try:
                header, b64 = src.split(",", 1)
                ext = "png" if "image/png" in header else "jpg"
                fn = filename_from_url(f"embedded.{ext}")
                dest = assets_dir / fn
                safe_write_atomic(dest, base64.b64decode(b64))
                img["src"] = str(dest.relative_to(relative_to))
                downloaded.append(str(dest))
                continue
            except Exception:
                pass

        # Handle remote URLs
        try:
            content = get_raw(session, src)
            fn = filename_from_url(src)
            dest = assets_dir / fn
            safe_write_atomic(dest, content)
            img["src"] = str(dest.relative_to(relative_to))
            downloaded.append(str(dest))
        except Exception:
            # Keep original URL if download fails
            pass

    return soup, downloaded