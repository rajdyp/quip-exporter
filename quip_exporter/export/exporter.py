"""Main export orchestration logic."""

import time
from pathlib import Path
import yaml

from quip_exporter.utils import ensure_dir, slugify, sha256_bytes, short_sleep, safe_write_atomic
from quip_exporter.api import (
    requests_session,
    get_user_folders,
    resolve_folder_id,
    list_folder_threads,
    fetch_thread,
    extract_html,
)
from quip_exporter.conversion import html_to_md_with_images
from .manifest import load_manifest, save_manifest


def export_all_folders(
    token: str,
    out_dir: Path,
    recursive: bool = True,
    maintain_structure: bool = False,
) -> None:
    """
    Export all accessible Quip folders to Markdown files with images.
    
    Args:
        token: Quip Personal Access Token
        out_dir: Output directory for exported files
        recursive: If True, include subfolders
        maintain_structure: If True, maintain Quip folder structure in output
    """
    session = requests_session(token)
    
    print("Fetching all accessible folders...")
    folders = get_user_folders(session)
    
    if not folders:
        print("No folders found or unable to access folders.")
        return
    
    print(f"\nFound {len(folders)} top-level folder(s):")
    for folder in folders:
        print(f"  - {folder['title']} ({folder['id']})")
    
    print("\nStarting export...\n")
    
    for i, folder in enumerate(folders, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(folders)}] Exporting folder: {folder['title']}")
        print(f"{'='*60}\n")
        
        try:
            export_folder_to_markdown(
                token=token,
                folder_input=folder['id'],
                out_dir=out_dir,
                recursive=recursive,
                maintain_structure=maintain_structure,
            )
        except Exception as e:
            print(f"Error exporting folder {folder['title']}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print("All folders exported!")
    print(f"{'='*60}")


def export_folder_to_markdown(
    token: str,
    folder_input: str,
    out_dir: Path,
    recursive: bool = True,
    maintain_structure: bool = False,
) -> None:
    """
    Export a Quip folder to Markdown files with images.
    
    Args:
        token: Quip Personal Access Token
        folder_input: Folder ID (web shorthand or API ID)
        out_dir: Output directory for exported files
        recursive: If True, include subfolders
        maintain_structure: If True, maintain Quip folder structure in output
    """
    session = requests_session(token)

    # Resolve folder ID (handles both web shorthand and API IDs)
    print(f"Resolving folder ID: {folder_input}")
    folder_id, folder_name = resolve_folder_id(session, folder_input)
    print(f"Found folder: '{folder_name}' (API ID: {folder_id})")

    folder_dir = out_dir / slugify(folder_name)
    ensure_dir(folder_dir)
    assets_root = folder_dir / "_assets"
    ensure_dir(assets_root)
    manifest_path = folder_dir / "manifest.json"
    manifest = load_manifest(manifest_path)

    print(f"Exporting to: {folder_dir}")
    if maintain_structure:
        print("Maintaining folder structure")

    threads = list_folder_threads(session, folder_id, recursive=recursive, maintain_structure=maintain_structure)
    if not threads:
        print("No documents found.")
        return

    print(f"Found {len(threads)} documents")

    exported = 0
    skipped = 0
    errors = 0

    for t in threads:
        # Check if document is unchanged based on timestamp alone
        if t.updated_usec:
            updated_key = str(t.updated_usec)
            prev = manifest.get(t.id, {})
            if prev.get("updated_key") == updated_key:
                print(f"[skip] Unchanged: {t.title}")
                skipped += 1
                continue
        
        # Document changed or no timestamp - fetch full content
        obj = fetch_thread(session, t.id)
        if not obj:
            print(f"[skip] Could not fetch {t.id} ({t.title})")
            skipped += 1
            continue
            
        html = extract_html(obj)
        if not html:
            print(f"[skip] No HTML for {t.id} ({t.title})")
            skipped += 1
            continue

        # Determine change key (use hash only if no timestamp)
        if t.updated_usec:
            updated_key = str(t.updated_usec)
        else:
            updated_key = sha256_bytes(html.encode("utf-8"))
            # Double-check against manifest for hash-based comparison
            prev = manifest.get(t.id, {})
            if prev.get("updated_key") == updated_key:
                print(f"[skip] Unchanged (hash): {t.title}")
                skipped += 1
                continue

        safe_title = slugify(t.title)
        
        # Determine document location based on maintain_structure
        if maintain_structure and t.folder_path:
            doc_dir = folder_dir / t.folder_path
            ensure_dir(doc_dir)
            md_path = doc_dir / f"{safe_title} - {t.id}.md"
            # Assets stay in centralized location but organized by thread ID
            doc_assets = assets_root / t.id
        else:
            md_path = folder_dir / f"{safe_title} - {t.id}.md"
            doc_assets = assets_root / t.id
        
        ensure_dir(doc_assets)

        try:
            # HTML → Markdown (download images + relink)
            # Pass the markdown file's parent directory so images are relative to the MD file
            md_body, downloaded = html_to_md_with_images(
                session, 
                html, 
                doc_assets,
                relative_to=md_path.parent
            )

            # Calculate relative path from markdown file to assets directory
            # Need to go up from md file location to root, then into _assets
            if maintain_structure and t.folder_path:
                # Count folder depth to calculate relative path
                depth = len(t.folder_path.split('/'))
                # Go up 'depth' levels, then into _assets/thread_id
                relative_assets = Path('../' * depth) / '_assets' / t.id
            else:
                # Flat structure: assets are in _assets/ relative to folder_dir
                relative_assets = Path('_assets') / t.id

            # YAML front-matter
            fm = {
                "title": t.title,
                "thread_id": t.id,
                "quip_url": t.url or f"https://quip.com/{t.id}",
                "updated_usec": t.updated_usec,
                "exported_at": int(time.time()),
                "assets_dir": str(relative_assets),
            }
            if t.folder_path:
                fm["folder_path"] = t.folder_path
                
            front_matter = "---\n" + yaml.safe_dump(fm, sort_keys=False).strip() + "\n---\n\n"

            content = (front_matter + md_body).encode("utf-8")
            safe_write_atomic(md_path, content)

            manifest[t.id] = {
                "title": t.title,
                "filename": str(md_path.relative_to(folder_dir)),
                "updated_key": updated_key,
                "last_exported": int(time.time()),
                "images": [str(Path(p).relative_to(folder_dir)) for p in downloaded],
            }
            if t.folder_path:
                manifest[t.id]["folder_path"] = t.folder_path
                
            print(f"[ok] {md_path.relative_to(folder_dir)} ({len(downloaded)} image(s))")
            exported += 1
            short_sleep()
        except Exception as e:
            print(f"[error] {t.id} ({t.title}): {e}")
            errors += 1

    save_manifest(manifest_path, manifest)
    print(f"\nDone. Exported: {exported}, Skipped: {skipped}, Errors: {errors}")
    print(f"Output: {folder_dir}")