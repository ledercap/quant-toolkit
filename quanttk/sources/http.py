"""HTTP helpers shared by the loaders."""

from __future__ import annotations

import time

import requests

BROWSER_HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_json(url: str, headers: dict[str, str] | None = None, attempts: int = 3, timeout: float = 90) -> dict:
    """GET a JSON document with retries and backoff.

    Cboe's CDN occasionally drops large downloads (the SPX chain is about 13 MB),
    so transient connection errors are retried before giving up.
    """
    for i in range(attempts):
        try:
            r = requests.get(url, headers=headers or BROWSER_HEADERS, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            if i == attempts - 1:
                raise
            time.sleep(2 * (i + 1))
    raise RuntimeError("unreachable")
