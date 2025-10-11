"""Manifest file management for tracking exported documents."""

import json
from pathlib import Path
from typing import Dict

def load_manifest(path: Path) -> Dict[str, dict]:
    """
    Load manifest from JSON file.
    
    Args:
        path: Path to manifest.json
        
    Returns:
        Dictionary mapping thread_id to export metadata
    """
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_manifest(path: Path, data: Dict[str, dict]) -> None:
    """
    Save manifest to JSON file atomically.
    
    Args:
        path: Path to manifest.json
        data: Dictionary mapping thread_id to export metadata
    """
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)