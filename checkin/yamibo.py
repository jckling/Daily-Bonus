# -*- coding: utf-8 -*-
# @File     : yamibo.py
# @Time     : 2021/04/07 15:48
# @Author   : Jckling

import os
import re

from curl_cffi import requests as cffi_requests
from lxml import html
from playwright.sync_api import sync_playwright

# info
USERNAME = os.environ.get("YAMIBO_USERNAME")
PASSWORD = os.environ.get("YAMIBO_PASSWORD")
msg = []

BASE_URL = "https://bbs.yamibo.com"

SESSION = cffi_requests.Session()

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "referer": "https://bbs.yamibo.com/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
}


def solve_waf():
    """Use Playwright to solve Baidu WAF JS challenge and return nox_jst_v1 cookie."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=HEADERS["user-agent"],
        )
        page = context.new_page()
        page.goto(f"{BASE_URL}/forum.php", wait_until="networkidle", timeout=30000)
        cookies = context.cookies()
        browser.close()

    nox_cookie = next((c for c in cookies if c["name"] == "nox_jst_v1"), None)
    if nox_cookie:
        SESSION.cookies.set("nox_jst_v1", nox_cookie["value"], domain="bbs.yamibo.com")
        return True
    return False


def login():
    """Login via Discuz member.php and return True if successful."""
    global msg

    if not solve_waf():
        msg.append({"name": "登录信息", "value": "WAF 挑战失败"})
        return False

    # Step 1: GET login page to extract formhash and loginhash
    r = SESSION.get(
        f"{BASE_URL}/member.php",
        headers=HEADERS,
        params={
            "mod": "logging",
            "action": "login",
            "infloat": "yes",
            "frommessage": "",
            "inajax": "1",
            "ajaxtarget": "messagelogin",
        },
        impersonate="chrome",
    )

    formhash_match = re.search(r'name="formhash"\s+value="([a-f0-9]+)"', r.text)
    loginhash_match = re.search(r'loginhash=([a-zA-Z0-9]+)', r.text)

    if not formhash_match:
        msg.append({"name": "登录信息", "value": "登录失败，无法获取 formhash"})
        return False

    formhash = formhash_match.group(1)
    loginhash = loginhash_match.group(1) if loginhash_match else ""

    # Step 2: POST login
    r2 = SESSION.post(
        f"{BASE_URL}/member.php",
        headers={
            **HEADERS,
            "content-type": "application/x-www-form-urlencoded",
        },
        params={
            "mod": "logging",
            "action": "login",
            "loginsubmit": "yes",
            "frommessage": "",
            "loginhash": loginhash,
            "inajax": "1",
        },
        data={
            "formhash": formhash,
            "referer": f"{BASE_URL}/forum.php",
            "username": USERNAME,
            "password": PASSWORD,
            "questionid": "0",
            "answer": "",
            "cookietime": "2592000",
        },
        impersonate="chrome",
    )

    if "succeedhandle" in r2.text or "succeed" in r2.text:
        msg.append({"name": "登录信息", "value": "登录成功"})
        return True
    elif "登录失败" in r2.text:
        error_match = re.search(r'<p[^>]*>([^<]+)</p>', r2.text)
        error_msg = error_match.group(1) if error_match else "登录失败"
        msg.append({"name": "登录信息", "value": error_msg})
        return False
    else:
        msg.append({"name": "登录信息", "value": f"登录失败，{r2.text[:100]}"})
        return False


def get_sign_page():
    """Fetch sign page.

    Returns (sign_hash, already_signed, page_text) or (None, None, None) if not logged in.
    """
    url = f"{BASE_URL}/plugin.php?id=zqlj_sign"
    r = SESSION.get(url, headers=HEADERS, impersonate="chrome")

    global msg
    if "需要先登录" in r.text:
        msg.append({"name": "登录信息", "value": "登录失败，Cookie 可能已经失效"})
        return None, None, None

    sign_match = re.search(r'sign=([a-f0-9]+)', r.text)
    sign_hash = sign_match.group(1) if sign_match else None
    btn_match = re.search(r'class="btna"[^>]*>([^<]+)<', r.text)
    btn_text = btn_match.group(1).strip() if btn_match else ""

    if not btn_text and "我的打卡动态" not in r.text:
        msg.append({"name": "签到信息", "value": "页面被拦截，无法获取签到状态"})
        return None, None, None

    already_signed = "今日已打卡" in btn_text and "点击打卡" not in btn_text

    return sign_hash, already_signed, r.text


def check_in(sign_hash):
    """Perform sign-in by visiting the sign URL with the one-time hash."""
    url = f"{BASE_URL}/plugin.php?id=zqlj_sign&sign={sign_hash}"
    r = SESSION.get(url, headers=HEADERS, impersonate="chrome")

    global msg
    if "打卡成功" in r.text:
        msg.append({"name": "签到信息", "value": "签到成功"})
        return True, r.text
    elif "打过卡" in r.text:
        msg.append({"name": "签到信息", "value": "今日已签到"})
        return True, r.text
    elif "需要先登录" in r.text:
        msg.append({"name": "签到信息", "value": "登录失败，Cookie 可能已经失效"})
        return False, r.text
    else:
        msg.append({"name": "签到信息", "value": "签到失败，未能从页面获取结果"})
        return False, r.text


def query_stats(page_text):
    """Query sign stats from sign page HTML and credit info from credit page."""
    global msg

    stats_map = {
        "最近打卡": "签到时间",
        "本月打卡": "本月签到",
        "连续打卡": "连续签到",
        "累计打卡": "累计签到",
        "最近奖励": "最近奖励",
    }
    for kw, name in stats_map.items():
        match = re.search(rf'{kw}：([^<]+)', page_text)
        if match:
            msg.append({"name": name, "value": match.group(1)})

    url = f"{BASE_URL}/home.php?mod=spacecp&ac=credit"
    r = SESSION.get(url, headers=HEADERS, impersonate="chrome")
    tree = html.fromstring(r.content)
    items = tree.xpath('//ul[@class="creditl mtm bbda cl"]/li')

    credit = {}
    for item in items:
        text = item.text_content().strip()
        match = re.match(r'(\S+):\s*(\S+)', text)
        if match:
            name, value = match.group(1), match.group(2)
            if name not in credit:
                credit[name] = value

    if credit:
        parts = [f"{k} {v}" for k, v in credit.items()]
        msg.append({"name": "账户余额", "value": "，".join(parts)})
    else:
        msg.append({"name": "账户余额", "value": "查询余额失败"})


def main():
    global msg
    if not USERNAME or not PASSWORD:
        return "No YAMIBO_USERNAME or YAMIBO_PASSWORD set"

    if not login():
        return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])

    sign_hash, already_signed, page_text = get_sign_page()
    if sign_hash is None and already_signed is None:
        return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])

    if not already_signed and sign_hash:
        check_in(sign_hash)
        r2 = SESSION.get(f"{BASE_URL}/plugin.php?id=zqlj_sign", headers=HEADERS, impersonate="chrome")
        page_text = r2.text
    else:
        msg.append({"name": "签到信息", "value": "今日已签到，无需重复签到"})

    query_stats(page_text)

    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == "__main__":
    print(" Yamibo 签到开始 ".center(60, "="))
    print(main())
    print(" Yamibo 签到结束 ".center(60, "="), "\n")
