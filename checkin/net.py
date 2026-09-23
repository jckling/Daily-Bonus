# -*- coding: utf-8 -*-
# @File     : net.py
# @Author   : Jckling
# @Time     : 2026/09/20

DEFAULT_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
}


def open_route(session, url, headers=None, impersonate=None):
    """Pre-flight the route: True when the site answers with an HTTP status below 500."""
    try:
        r = session.get(
            url,
            headers={**DEFAULT_HEADERS, **(headers or {})},
            timeout=15,
            **({"impersonate": impersonate} if impersonate else {}),
        )
    except Exception:
        return False
    return r.status_code < 500
