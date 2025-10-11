"""HTML to Markdown conversion."""

import re
from pathlib import Path
from typing import List, Tuple, Optional
import requests
from markdownify import markdownify as md

from .html_processor import process_images


def html_to_markdown(html: str) -> str:
    """
    Convert HTML to Markdown with standard settings.
    
    Args:
        html: HTML content to convert
        
    Returns:
        Markdown text
    """
    md_text = md(
        html,
        heading_style="ATX",
        bullets="*",
        code_language=False,
        strip=["span"],
        keep_inline_images=True,
    )
    
    # Post-process: collapse 3+ blank lines to 2
    md_text = re.sub(r"\n{3,}", "\n\n", md_text).rstrip() + "\n"
    return md_text


def html_to_md_with_images(
    session: requests.Session,
    html: str,
    assets_dir: Path,
    relative_to: Optional[Path] = None
) -> Tuple[str, List[str]]:
    """
    Convert HTML to Markdown while downloading and relinking images.
    
    - Downloads images referenced by <img src="...">
    - Rewrites src to relative path (from relative_to to assets_dir/filename)
    - Converts resulting HTML to Markdown
    
    Args:
        session: Authenticated requests session
        html: HTML content to convert
        assets_dir: Directory to save downloaded images
        relative_to: Directory to calculate image paths relative to (for images in markdown)
        
    Returns:
        Tuple of (markdown_text, list of downloaded file paths)
    """
    # Process images and get modified HTML
    soup, downloaded = process_images(session, html, assets_dir, relative_to)
    
    # Convert modified HTML to Markdown
    md_text = html_to_markdown(str(soup))
    
    return md_text, downloaded