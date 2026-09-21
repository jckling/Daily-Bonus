# -*- coding: utf-8 -*-
# @File     : net.py
# @Author   : Jckling
# Shared network route helper: probe direct first, fall back to PROXY_URL.

import os

PROXY_URL = os.environ.get("PROXY_URL")

DEFAULT_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
}


def open_route(session, url, headers=None, impersonate=None, prefer_proxy=False):
    """Pre-flight the route: direct first, PROXY_URL fallback; any response below 500 is usable and the session keeps the chosen exit IP."""
    candidates = [{}]
    if PROXY_URL:
        candidates.append({"http": PROXY_URL, "https": PROXY_URL})
    if prefer_proxy:
        candidates.reverse()
    merged = {**DEFAULT_HEADERS, **(headers or {})}
    for proxies in candidates:
        try:
            r = session.get(
                url,
                headers=merged,
                proxies=proxies,
                timeout=15,
                **({"impersonate": impersonate} if impersonate else {}),
            )
        except Exception:
            continue
        if r.status_code < 500:
            session.proxies = proxies
            return True
    return False


def browser_proxy(session):
    """Playwright proxy config matching the session's active route."""
    server = (session.proxies or {}).get("https")
    return {"server": server} if server else None


def proxy_hint():
    """Suffix for failure messages when no fallback proxy is configured."""
    return "" if PROXY_URL else "（未配置 PROXY_URL）"
