"""Safe HTTP(S) browsing and web search."""

from __future__ import annotations

import webbrowser
from urllib.parse import quote_plus

from brain.parser import validate_url_target


def open_url(target: str, opener: object = webbrowser.open) -> str:
    url = validate_url_target(target)
    if not opener(url):
        raise RuntimeError("Windows could not open the default browser")
    return url


def web_search(query: str, opener: object = webbrowser.open) -> str:
    if not query.strip() or len(query) > 500:
        raise ValueError("Search query is empty or too long")
    return open_url(f"https://www.google.com/search?q={quote_plus(query.strip())}", opener)

