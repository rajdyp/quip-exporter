"""Base API client with retry logic."""

import requests
from quip_exporter.utils import backoff_sleep

API = "https://platform.quip.com/1"
DEF_TIMEOUT = 45
USER_AGENT = "quip-md-exporter/1.0"


def requests_session(token: str) -> requests.Session:
    """Create a requests session with authentication."""
    s = requests.Session()
    s.headers.update({
        "Authorization": f"Bearer {token}",
        "User-Agent": USER_AGENT,
    })
    return s


def get_json(session: requests.Session, url: str, **params):
    """Make a GET request and return JSON response with retry logic."""
    for i in range(4):
        try:
            r = session.get(url, params=params or None, timeout=DEF_TIMEOUT)
            if r.status_code in (429, 502, 503, 504):
                backoff_sleep(i)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if i == 3:
                raise
            backoff_sleep(i)
    raise RuntimeError("unreachable")


def get_raw(session: requests.Session, url: str) -> bytes:
    """Make a GET request and return raw bytes with retry logic."""
    for i in range(4):
        try:
            r = session.get(url, timeout=DEF_TIMEOUT)
            if r.status_code in (429, 502, 503, 504):
                backoff_sleep(i)
                continue
            r.raise_for_status()
            return r.content
        except requests.RequestException:
            if i == 3:
                raise
            backoff_sleep(i)
    raise RuntimeError("unreachable")