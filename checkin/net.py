# -*- coding: utf-8 -*-
# @File     : net.py
# @Author   : Jckling
# @Time     : 2026/09/20
# Shared network route helper: probe direct first, fall back to PROXY_URL.

import os

PROXY_URL = os.environ.get("PROXY_URL")

DEFAULT_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
}

_status = ""


def _probe(session, url, headers, impersonate, proxies):
    """One route probe: True when the site answers with an HTTP status below 500."""
    try:
        r = session.get(
            url,
            headers={**DEFAULT_HEADERS, **(headers or {})},
            proxies=proxies,
            timeout=15,
            **({"impersonate": impersonate} if impersonate else {}),
        )
    except Exception:
        return False
    return r.status_code < 500


def open_route(session, url, headers=None, impersonate=None, prefer_proxy=False):
    """Pre-flight the route: direct first, PROXY_URL fallback; <500 responses are usable and the session keeps the chosen exit IP."""
    global _status
    candidates = [{}]
    if PROXY_URL:
        candidates.append({"http": PROXY_URL, "https": PROXY_URL})
    if prefer_proxy:
        candidates.reverse()

    for proxies in candidates:
        if _probe(session, url, headers, impersonate, proxies):
            session.proxies = proxies
            _status = ""
            return True
        if prefer_proxy and proxies:
            # challenge failures ban the exit IP: a dead proxy must not fall back to direct
            _status = "proxy_dead"
            return False

    _status = "proxy_dead" if PROXY_URL else "no_proxy"
    return False


def browser_proxy(session):
    """Playwright proxy config matching the session's active route."""
    server = (session.proxies or {}).get("https")
    return {"server": server} if server else None


def proxy_hint():
    """Why the last open_route failed, for failure messages."""
    if _status == "proxy_dead":
        return "（代理不可用）"
    if _status == "no_proxy":
        return "（未配置 PROXY_URL）"
    return ""
