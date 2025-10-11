#!/usr/bin/env python3
"""
Quip Folder → Markdown (with images) Exporter

- Resolve a Quip folder by ID (handles both web shorthand and API IDs).
- Enumerate threads (docs) in that folder (optionally include subfolders).
- Fetch each thread's HTML, download inline images locally, rewrite <img src> to relative paths.
- Convert HTML → Markdown with solid defaults for headings/lists/tables/code.
- Add YAML front-matter (title, id, urls, timestamps).
- Maintain a manifest (manifest.json) to skip unchanged docs on subsequent runs.

Env vars (or override with CLI):
  QUIP_TOKEN        : required Personal Access Token
  QUIP_FOLDER_ID    : folder ID (e.g., eKLAOA5UvPd)
  QUIP_OUT          : output directory (default: ~/Documents/QuipNotes)
  QUIP_RECURSIVE    : "1" to include subfolders (default 1)

CLI:
  python -m quip_exporter --folder-id eKLAOA5UvPd --token YOUR_TOKEN
"""

import argparse
import sys
from pathlib import Path

from quip_exporter.utils import env_default
from quip_exporter.export import export_folder_to_markdown, export_all_folders


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    p = argparse.ArgumentParser(description="Export a Quip folder to Markdown with images.")
    p.add_argument("--token", default=env_default("QUIP_TOKEN"), help="Quip Personal Access Token")
    p.add_argument("--folder-id", default=env_default("QUIP_FOLDER_ID"), help="Folder ID (e.g., eKLAOA5UvPd or WT24OK8OZC6B)")
    p.add_argument("--all", action="store_true", help="Export all accessible folders")
    p.add_argument("--out", default=env_default("QUIP_OUT", str(Path.home() / "Documents/QuipNotes")), help="Output directory")
    p.add_argument("--no-recursive", action="store_true", help="Do not include subfolders")
    p.add_argument("--maintain-structure", action="store_true", help="Maintain Quip folder structure in output")
    return p.parse_args()


def main():
    """Main CLI entry point."""
    args = parse_args()
    if not args.token:
        print("ERROR: Set QUIP_TOKEN or pass --token")
        sys.exit(1)
    
    out_dir = Path(args.out)
    recursive = not args.no_recursive
    
    if args.all:
        # Export all accessible folders
        export_all_folders(
            args.token,
            out_dir,
            recursive=recursive,
            maintain_structure=args.maintain_structure
        )
    else:
        # Export specific folder
        if not args.folder_id:
            print("ERROR: Set QUIP_FOLDER_ID or pass --folder-id (or use --all to export everything)")
            print("\nTo get your folder ID:")
            print("  1. Navigate to your folder in Quip web UI")
            print("  2. Copy the ID from the URL (e.g., WT24OK8OZC6B)")
            print("  3. Use: --folder-id <ID>")
            print("\nOr use --all to export all accessible folders")
            sys.exit(1)
        
        export_folder_to_markdown(
            args.token, 
            args.folder_id, 
            out_dir, 
            recursive=recursive,
            maintain_structure=args.maintain_structure
        )


if __name__ == "__main__":
    main()