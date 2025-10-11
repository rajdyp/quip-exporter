"""Network utility functions."""

import time

def short_sleep():
    """Brief sleep between API calls to avoid rate limiting."""
    time.sleep(0.12)

def backoff_sleep(i: int):
    """Exponential backoff sleep for retries."""
    time.sleep(min(2.0 * (2 ** i), 10.0))