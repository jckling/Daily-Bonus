# -*- coding: utf-8 -*-
# @File     : yamibo.py
# @Time     : 2021/04/07 15:48
# @Author   : Jckling

import os
import re

import requests
from lxml import html

# cookies
COOKIES = os.environ.get("YAMIBO_COOKIES")
SESSION = requests.Session()
msg = []

BASE_URL = "https://bbs.yamibo.com"

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
    "cookie": COOKIES or "",
    "referer": "https://bbs.yamibo.com/",
    "sec-ch-ua": '"Not;A-Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
}


def get_sign_page():
    """Fetch sign page.

    Returns (sign_hash, already_signed, page_text) or (None, None, None) if not logged in.
    """
    url = f"{BASE_URL}/plugin.php?id=zqlj_sign"
    r = SESSION.get(url, headers=HEADERS)

    global msg
    if "需要先登录" in r.text:
        msg.append({"name": "登录信息", "value": "登录失败，Cookie 可能已经失效"})
        return None, None, None

    sign_match = re.search(r'sign=([a-f0-9]+)', r.text)
    sign_hash = sign_match.group(1) if sign_match else None
    already_signed = "今日已打卡" in r.text

    return sign_hash, already_signed, r.text


def check_in(sign_hash):
    """Perform sign-in by visiting the sign URL with the one-time hash."""
    url = f"{BASE_URL}/plugin.php?id=zqlj_sign&sign={sign_hash}"
    r = SESSION.get(url, headers=HEADERS)

    global msg
    if "打卡成功" in r.text:
        match = re.search(r'获得.*?(\d+).*?对象', r.text)
        reward = match.group(0) if match else "签到成功"
        msg.append({"name": "签到信息", "value": f"签到成功，{reward}"})
        return True
    elif "打过卡" in r.text:
        msg.append({"name": "签到信息", "value": "今日已签到"})
        return True
    elif "需要先登录" in r.text:
        msg.append({"name": "签到信息", "value": "登录失败，Cookie 可能已经失效"})
        return False
    else:
        msg.append({"name": "签到信息", "value": "签到失败，未能从页面获取结果"})
        return False


def query_stats(page_text):
    """Query sign stats from sign page HTML and credit info from credit page."""
    global msg

    # Sign stats from the already-fetched sign page
    stats_map = {
        "本月打卡": "本月签到",
        "连续打卡": "连续签到",
        "累计打卡": "累计签到",
        "最近奖励": "最近奖励",
    }
    for kw, name in stats_map.items():
        match = re.search(rf'{kw}：([^<]+)', page_text)
        if match:
            msg.append({"name": name, "value": match.group(1)})

    # Credit info from credit page
    url = f"{BASE_URL}/home.php?mod=spacecp&ac=credit"
    r = SESSION.get(url, headers=HEADERS)
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
    if not COOKIES:
        return "No YAMIBO_COOKIES set"

    sign_hash, already_signed, page_text = get_sign_page()
    if sign_hash is None and already_signed is None:
        return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])

    if not already_signed and sign_hash:
        check_in(sign_hash)
    else:
        msg.append({"name": "签到信息", "value": "今日已签到，无需重复签到"})

    query_stats(page_text)

    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == "__main__":
    print(" Yamibo 签到开始 ".center(60, "="))
    print(main())
    print(" Yamibo 签到结束 ".center(60, "="), "\n")
