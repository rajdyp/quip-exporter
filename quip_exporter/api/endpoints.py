"""Quip API endpoints for folders and threads."""

from typing import List, Optional, Tuple, Dict
import requests

from quip_exporter.models import ThreadMeta
from quip_exporter.utils import short_sleep, slugify
from .client import API, DEF_TIMEOUT


def get_user_folders(session: requests.Session, include_archived: bool = False) -> List[Dict[str, str]]:
    """
    Get all top-level folders accessible to the current user.
    
    Args:
        session: Authenticated requests session
        include_archived: If True, include archived folders (default: False)
    
    Returns:
        List of dicts with 'id', 'title' keys for each folder
    """
    try:
        r = session.get(f"{API}/users/current", timeout=DEF_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        
        folders = []
        
        # IDs to skip (trash, starred are not real content folders)
        trash_id = data.get("trash_folder_id")
        starred_id = data.get("starred_folder_id")
        archive_id = data.get("archive_folder_id")
        
        skip_ids = {trash_id, starred_id}
        if not include_archived:
            skip_ids.add(archive_id)
        
        # Get desktop folder (main workspace - THIS IS WHERE YOUR CONTENT IS)
        desktop_folder_id = data.get("desktop_folder_id")
        if desktop_folder_id and desktop_folder_id not in skip_ids:
            try:
                folder_r = session.get(f"{API}/folders/{desktop_folder_id}", timeout=DEF_TIMEOUT)
                folder_r.raise_for_status()
                folder_data = folder_r.json()
                folder_obj = folder_data.get("folder", folder_data)
                folders.append({
                    "id": desktop_folder_id,
                    "title": folder_obj.get("title") or folder_obj.get("name") or "Desktop"
                })
                short_sleep()
            except Exception as e:
                print(f"Warning: Could not fetch desktop folder: {e}")
        
        # Get private folder (your personal private documents)
        private_folder_id = data.get("private_folder_id")
        if private_folder_id and private_folder_id not in skip_ids:
            try:
                folder_r = session.get(f"{API}/folders/{private_folder_id}", timeout=DEF_TIMEOUT)
                folder_r.raise_for_status()
                folder_data = folder_r.json()
                folder_obj = folder_data.get("folder", folder_data)
                folders.append({
                    "id": private_folder_id,
                    "title": folder_obj.get("title") or folder_obj.get("name") or "Private"
                })
                short_sleep()
            except Exception as e:
                print(f"Warning: Could not fetch private folder: {e}")
        
        # Get shared folders (folders shared with you by others)
        for folder_id in data.get("shared_folder_ids", []):
            if folder_id in skip_ids:
                continue
            try:
                folder_r = session.get(f"{API}/folders/{folder_id}", timeout=DEF_TIMEOUT)
                folder_r.raise_for_status()
                folder_data = folder_r.json()
                folder_obj = folder_data.get("folder", folder_data)
                folders.append({
                    "id": folder_id,
                    "title": folder_obj.get("title") or folder_obj.get("name") or folder_id
                })
                short_sleep()
            except Exception as e:
                print(f"Warning: Could not fetch folder {folder_id}: {e}")
        
        # Get group folders (team/workspace folders)
        for group_id in data.get("group_ids", []):
            try:
                group_r = session.get(f"{API}/groups/{group_id}", timeout=DEF_TIMEOUT)
                group_r.raise_for_status()
                group_data = group_r.json()
                folder_id = group_data.get("group", {}).get("folder_id")
                if folder_id and folder_id not in skip_ids:
                    folder_r = session.get(f"{API}/folders/{folder_id}", timeout=DEF_TIMEOUT)
                    folder_r.raise_for_status()
                    folder_data = folder_r.json()
                    folder_obj = folder_data.get("folder", folder_data)
                    folders.append({
                        "id": folder_id,
                        "title": folder_obj.get("title") or folder_obj.get("name") or folder_id
                    })
                short_sleep()
            except Exception as e:
                print(f"Warning: Could not fetch group {group_id}: {e}")
        
        return folders
    except Exception as e:
        print(f"Error getting user folders: {e}")
        return []


def resolve_folder_id(session: requests.Session, folder_input: str) -> Tuple[str, str]:
    """
    Resolve folder ID from either:
    - A web shorthand ID (like WT24OK8OZC6B from URL)
    - An actual API folder ID (like eKLAOA5UvPd)
    
    Returns: (actual_folder_id, folder_name)
    """
    try:
        # Try to get folder info - works with both shorthand and real IDs
        r = session.get(f"{API}/folders/{folder_input}", timeout=DEF_TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            folder_obj = data.get("folder", data)
            actual_id = folder_obj.get("id", folder_input)
            folder_name = folder_obj.get("title") or folder_obj.get("name") or actual_id
            return actual_id, folder_name
    except Exception as e:
        print(f"Warning: Could not resolve folder info: {e}")
    
    # Fallback: use input as-is
    return folder_input, folder_input


def list_folder_threads(
    session: requests.Session, 
    folder_id: str, 
    recursive: bool,
    maintain_structure: bool = False
) -> List[ThreadMeta]:
    """
    List all threads (documents) in a folder.
    
    Args:
        session: Authenticated requests session
        folder_id: Folder ID to list
        recursive: If True, include subfolders
        maintain_structure: If True, track folder hierarchy in ThreadMeta.folder_path
        
    Returns:
        List of ThreadMeta objects sorted by title
    """
    # Track folder hierarchy: folder_id -> (folder_name, parent_folder_id)
    folder_info: Dict[str, Tuple[str, Optional[str]]] = {}
    
    # Queue: (folder_id, parent_folder_id)
    to_visit = [(folder_id, None)]
    seen_folders = set()
    out: List[ThreadMeta] = []

    while to_visit:
        fid, parent_fid = to_visit.pop(0)
        if fid in seen_folders:
            continue
        seen_folders.add(fid)

        try:
            r = session.get(f"{API}/folders/{fid}", timeout=DEF_TIMEOUT)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"Warning: Could not access folder {fid}: {e}")
            continue

        # Store folder info
        folder_obj = data.get("folder", data)
        folder_name = folder_obj.get("title") or folder_obj.get("name") or fid
        folder_info[fid] = (folder_name, parent_fid)

        # Extract children
        children = data.get("children", [])
        
        for child in children:
            # Check if it's a thread or folder
            if "thread_id" in child:
                tid = child["thread_id"]
                # Fetch thread details
                try:
                    thread_r = session.get(f"{API}/threads/{tid}", timeout=DEF_TIMEOUT)
                    thread_r.raise_for_status()
                    thread_data = thread_r.json()
                    thread_obj = thread_data.get("thread", thread_data)
                    
                    title = thread_obj.get("title", tid)
                    updated_usec = thread_obj.get("updated_usec")
                    url = thread_obj.get("link") or thread_obj.get("url")
                    
                    # Calculate folder path if maintain_structure is enabled
                    folder_path = None
                    if maintain_structure:
                        folder_path = _build_folder_path(fid, folder_id, folder_info)
                    
                    out.append(ThreadMeta(
                        id=tid, 
                        title=title, 
                        updated_usec=updated_usec, 
                        url=url,
                        folder_path=folder_path
                    ))
                    short_sleep()
                except Exception as e:
                    print(f"Warning: Could not fetch thread {tid}: {e}")
                    
            elif "folder_id" in child and recursive:
                subfolder_id = child["folder_id"]
                to_visit.append((subfolder_id, fid))

        short_sleep()

    # stable sort: by folder_path, then title, then id
    if maintain_structure:
        out.sort(key=lambda x: (x.folder_path or "", x.title.lower(), x.id))
    else:
        out.sort(key=lambda x: (x.title.lower(), x.id))
    
    return out


def _build_folder_path(
    current_folder_id: str,
    root_folder_id: str,
    folder_info: Dict[str, Tuple[str, Optional[str]]]
) -> str:
    """
    Build a relative folder path from root to current folder.
    
    Args:
        current_folder_id: The folder containing the thread
        root_folder_id: The root folder being exported
        folder_info: Map of folder_id -> (folder_name, parent_folder_id)
        
    Returns:
        Relative path like "subfolder1/subfolder2" or "" for root
    """
    if current_folder_id == root_folder_id:
        return ""
    
    path_parts = []
    fid = current_folder_id
    
    # Walk up the tree until we hit root
    while fid and fid != root_folder_id:
        if fid not in folder_info:
            break
        folder_name, parent_fid = folder_info[fid]
        path_parts.append(slugify(folder_name))
        fid = parent_fid
    
    # Reverse to get root -> leaf order
    path_parts.reverse()
    return "/".join(path_parts) if path_parts else ""


def fetch_thread(session: requests.Session, thread_id: str) -> Optional[dict]:
    """Fetch a single thread's data."""
    try:
        r = session.get(f"{API}/threads/{thread_id}", timeout=DEF_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def extract_html(obj: dict) -> Optional[str]:
    """Extract HTML content from a thread API response."""
    if isinstance(obj, dict):
        if "html" in obj:
            return obj["html"]
        for key in ("thread", "document", "content", "expanded"):
            node = obj.get(key)
            if isinstance(node, dict) and "html" in node:
                return node["html"]
    return None