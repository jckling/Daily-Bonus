# -*- coding: utf-8 -*-
# @File     : yurifans.py
# @Time     : 2023/04/25 12:17
# @Author   : Cloudac7, Jckling

import json
import os
import time

from curl_cffi import requests as cffi_requests
from patchright.sync_api import sync_playwright

from checkin import net

# info
USERNAME = os.environ.get("YURIFANS_EMAIL")
PASSWORD = os.environ.get("YURIFANS_PASSWORD")
msg = []

BASE_URL = "https://yuri.website"

SESSION = cffi_requests.Session()

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
    "content-type": "application/x-www-form-urlencoded",
    "origin": BASE_URL,
    "referer": f"{BASE_URL}/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
}

# Reuse clearance cookies like a real browser would: repeated cookie-less challenges get the IP banned
COOKIE_CACHE = os.path.expanduser(
    os.environ.get("YURIFANS_COOKIE_CACHE", "~/.yurifans_cookies.json")
)


def load_cookie_cache():
    """Load cached WAF cookies. Returns (cookies, user_agent) or (None, None)."""
    try:
        with open(COOKIE_CACHE) as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None, None
    if isinstance(data, dict):
        cookies, user_agent = data.get("cookies"), data.get("user_agent")
    else:
        cookies, user_agent = data, None
    if isinstance(cookies, list) and cookies:
        return cookies, user_agent
    return None, None


def save_cookie_cache(cookies):
    try:
        with open(COOKIE_CACHE, "w") as f:
            json.dump({"user_agent": HEADERS["user-agent"], "cookies": cookies}, f)
    except OSError:
        pass


def clear_cookie_cache():
    try:
        os.remove(COOKIE_CACHE)
    except OSError:
        pass


def apply_cookies(cookies):
    for cookie in cookies:
        SESSION.cookies.set(cookie["name"], cookie["value"], domain="yuri.website")


def clear_waf_cookies(cookies):
    """Drop stale/revoked clearance cookies from the session jar and the cache."""
    for cookie in cookies:
        try:
            SESSION.cookies.jar.clear("yuri.website", cookie.get("path", "/"), cookie["name"])
        except KeyError:
            pass
    clear_cookie_cache()


def waf_cleared():
    """True = reachable without a challenge, False = challenge needed, None = unreachable."""
    try:
        r = SESSION.get(f"{BASE_URL}/", headers=HEADERS, impersonate="chrome", timeout=30)
    except Exception:
        return None
    return r.status_code == 200


def solve_waf():
    """Pass SafeLine WAF human verification and load clearance cookies into the session."""
    cookies, user_agent = load_cookie_cache()
    if cookies:
        if user_agent:
            # Stay consistent with the browser that earned the clearance
            HEADERS["user-agent"] = user_agent
        apply_cookies(cookies)
        state = waf_cleared()
        if state is True:
            return True
        clear_waf_cookies(cookies)
        if state is None:
            msg.append({"name": "登录信息", "value": "无法连接网站"})
            return False

    launch_options = [
        {"channel": "chrome", "headless": False},
        {"headless": False},
        {"headless": True},
    ]
    args = ["--disable-blink-features=AutomationControlled"]
    if os.geteuid() == 0:
        # Chromium refuses to run as root without this (CI containers)
        args.append("--no-sandbox")

    jar = []
    with sync_playwright() as p:
        browser = None
        for options in launch_options:
            try:
                browser = p.chromium.launch(args=args, proxy=net.browser_proxy(SESSION), **options)
                break
            except Exception:
                continue
        if browser is None:
            clear_cookie_cache()
            msg.append({"name": "登录信息", "value": "浏览器启动失败"})
            return False

        context = browser.new_context(locale="zh-CN", timezone_id="Asia/Shanghai")
        page = context.new_page()

        trace = []
        page.on(
            "response",
            lambda r: trace.append(f"{r.status} {r.url.split('?')[0][:90]}")
            if ("safeline" in r.url or "chaitin" in r.url)
            else None,
        )

        try:
            try:
                page.goto(f"{BASE_URL}/", wait_until="commit", timeout=60000)
            except Exception as e:
                clear_cookie_cache()
                msg.append({"name": "登录信息", "value": f"无法连接网站（{str(e)[:90]}）"})
                return False

            deadline = time.time() + 150
            passed = False
            while time.time() < deadline:
                time.sleep(2)
                try:
                    html = page.content()
                except Exception:
                    continue
                if "SafeLineChallenge" not in html:
                    passed = "wp-content" in html
                    break
            if not passed:
                clear_cookie_cache()
                detail = trace[-1] if trace else "挑战未完成"
                msg.append({"name": "登录信息", "value": f"WAF 人机验证失败（{detail}）"})
                return False

            HEADERS["user-agent"] = page.evaluate("navigator.userAgent")
            jar = context.cookies([f"{BASE_URL}/"])
        finally:
            browser.close()

    apply_cookies(jar)
    save_cookie_cache(jar)
    return True


def login():
    """Login with email and password, return b2_token or None."""
    url = f"{BASE_URL}/wp-json/jwt-auth/v1/token"
    r = SESSION.post(
        url,
        headers=HEADERS,
        data={"username": USERNAME, "password": PASSWORD},
        impersonate="chrome",
    )
    if r.status_code != 200:
        msg.append({"name": "登录信息", "value": "登录失败，请检查账号密码"})
        return None

    b2_token = r.cookies.get("b2_token")
    if not b2_token:
        msg.append({"name": "登录信息", "value": "登录失败，未获取到 token"})
        return None

    data = r.json()
    name = data.get("name", "")
    masked = "█" * len(name)
    msg.append({"name": "登录信息", "value": masked})
    return b2_token


def get_auth_headers(b2_token):
    """Build headers with Bearer token for authenticated requests."""
    return {
        **HEADERS,
        "authorization": f"Bearer {b2_token}",
    }


def get_user_info(b2_token):
    """Get user info to verify login."""
    headers = get_auth_headers(b2_token)
    r = SESSION.post(
        f"{BASE_URL}/wp-json/b2/v1/getUserInfo",
        headers=headers,
        data="ref=null",
        impersonate="chrome",
    )
    if r.status_code != 200:
        return False
    return True


def get_mission(b2_token):
    """Get mission status. Returns (already_signed, credit, my_credit)."""
    headers = get_auth_headers(b2_token)
    r = SESSION.post(
        f"{BASE_URL}/wp-json/b2/v1/getUserMission",
        headers=headers,
        data="count=6&paged=1",
        impersonate="chrome",
    )
    if r.status_code != 200:
        msg.append({"name": "签到信息", "value": "查询签到状态失败"})
        return None

    mission = r.json().get("mission", {})
    date = mission.get("date", "")
    credit = mission.get("credit", 0)
    my_credit = mission.get("my_credit", 0)

    if date:
        # Already signed today
        msg.append({"name": "签到信息", "value": f"今日已签到（{date}）"})
        msg.append({"name": "今日奖励", "value": f"{credit} 积分"})
        msg.append({"name": "当前积分", "value": str(my_credit)})
        return True
    else:
        return False


def check_in(b2_token):
    """Perform daily check-in."""
    headers = get_auth_headers(b2_token)
    r = SESSION.post(
        f"{BASE_URL}/wp-json/b2/v1/userMission",
        headers=headers,
        impersonate="chrome",
    )

    if r.status_code != 200:
        msg.append({"name": "签到信息", "value": "签到失败"})
        return False

    # Response is either a credit number string or JSON with mission data
    try:
        data = r.json()
        if isinstance(data, dict) and "mission" in data:
            mission = data["mission"]
            date = mission.get("date", "")
            credit = mission.get("credit", 0)
            my_credit = mission.get("my_credit", 0)
            msg.append({"name": "签到信息", "value": f"签到成功（{date}）"})
            msg.append({"name": "今日奖励", "value": f"{credit} 积分"})
            msg.append({"name": "当前积分", "value": str(my_credit)})
        else:
            # Sometimes returns just the credit as a string
            msg.append({"name": "签到信息", "value": "签到成功"})
            msg.append({"name": "今日奖励", "value": f"{data} 积分"})
    except Exception:
        msg.append({"name": "签到信息", "value": f"签到成功（{r.text}）"})

    return True


def main():
    global msg
    if not USERNAME or not PASSWORD:
        return "No YURIFANS_EMAIL or YURIFANS_PASSWORD set"

    # SafeLine bans the exit IP for days on challenge failure; keep the home IP out of it
    if not net.open_route(SESSION, f"{BASE_URL}/", impersonate="chrome", prefer_proxy=True):
        return f"无法连接网站{net.proxy_hint()}"

    if not solve_waf():
        return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])

    try:
        b2_token = login()
        if not b2_token:
            return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])

        if not get_user_info(b2_token):
            msg.append({"name": "登录信息", "value": "登录失败，token 验证失败"})
            return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])

        already_signed = get_mission(b2_token)
        if already_signed is None:
            return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])

        if not already_signed:
            check_in(b2_token)
    except Exception as e:
        # Do not crash the whole message.py run (other modules still report)
        msg.append({"name": "签到信息", "value": f"请求异常（{e}）"})

    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == "__main__":
    print(" Yurifans 签到开始 ".center(60, "="))
    print(main())
    print(" Yurifans 签到结束 ".center(60, "="), "\n")
