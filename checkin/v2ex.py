# -*- coding: utf-8 -*-
# @File     : v2ex.py
# @Time     : 2021/04/08 09:43
# @Author   : Jckling

import os
import re
import time

import requests
from lxml import html

# cookies
COOKIES = os.environ.get("V2EX_COOKIES")
SESSION = requests.Session()
msg = []

BASE_URL = "https://www.v2ex.com"

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
    "cookie": COOKIES or "",
    "referer": "https://www.v2ex.com/",
    "sec-ch-ua": '"Not;A-Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
}


def get_once():
    """Check daily mission page for login status and once token.

    Returns (once, already_claimed, streak_text):
      - ("", False, "") if not logged in
      - ("", True, streak_text) if already claimed today
      - (once_token, False, "") if ready to claim
    """
    url = f"{BASE_URL}/mission/daily"
    r = SESSION.get(url, headers=HEADERS)

    global msg
    if "你要查看的页面需要先登录" in r.text:
        msg.append({"name": "登录信息", "value": "登录失败，Cookie 可能已经失效"})
        return "", False, ""

    if "每日登录奖励已领取" in r.text:
        streak = re.search(r"已连续登录 (\d+) 天", r.text)
        streak_days = streak.group(1) if streak else "?"
        msg.append({"name": "登录信息", "value": "每日登录奖励已领取"})
        msg.append({"name": "累计登录", "value": f"{streak_days} 天"})
        return "", True, ""

    match = re.search(r"once=(\d+)", r.text)
    if match:
        msg.append({"name": "登录信息", "value": "登录成功"})
        return match.group(1), False, ""

    msg.append({"name": "登录信息", "value": "无法获取 once 参数，页面结构可能已变更"})
    return "", False, ""


def check_in(once):
    """Redeem daily reward via GET to /mission/daily/redeem?once=XXX.

    The 302 redirect target page contains the reward text.
    """
    url = f"{BASE_URL}/mission/daily/redeem?once={once}"
    r = SESSION.get(url, headers=HEADERS)

    global msg
    match = re.search(r"已成功领取每日登录奖励 (\d+) 铜币", r.text)
    if match:
        msg.append({"name": "签到信息", "value": f"签到成功，获得 {match.group(1)} 铜币"})
        return True

    if "每日登录奖励已领取" in r.text:
        msg.append({"name": "签到信息", "value": "今日已签到，无需重复签到"})
        return True

    msg.append({"name": "签到信息", "value": "签到失败，未能从页面获取奖励信息"})
    return False


def query_balance():
    """Query account balance and today's reward from /balance page."""
    url = f"{BASE_URL}/balance"
    r = SESSION.get(url, headers=HEADERS)
    tree = html.fromstring(r.content)

    global msg

    # Today's reward from transaction history (includes timestamp)
    today = time.strftime("%Y%m%d")
    reward_match = re.search(rf"{today} 的每日登录奖励 (\d+) 铜币", r.text)
    if reward_match:
        # Find the timestamp in the same table row (previous td)
        reward_idx = r.text.find(f"{today} 的每日登录奖励")
        row_start = r.text.rfind("<tr>", 0, reward_idx)
        row_html = r.text[row_start:reward_idx + 50] if row_start >= 0 else ""
        ts_match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{2}:\d{2})", row_html)
        ts = ts_match.group(1) if ts_match else ""
        reward_str = f"{reward_match.group(1)} 铜币"
        if ts:
            reward_str += f"（{ts}）"
        msg.append({"name": "今日奖励", "value": reward_str})

    # Account balance
    balance_nodes = tree.xpath('//div[@class="balance_area bigger"]/text()')
    if not balance_nodes:
        msg.append({"name": "账户余额", "value": "查询余额失败"})
        return

    values = [s.strip() for s in balance_nodes if s.strip()]
    if len(values) == 2:
        values = ["0"] + values

    golden, silver, bronze = values
    msg.append({"name": "账户余额", "value": f"{golden} 金币，{silver} 银币，{bronze} 铜币"})


def main():
    global msg
    if not COOKIES:
        return "No V2EX_COOKIES set"

    once, _, _ = get_once()
    if once:
        check_in(once)

    # Always query balance for current state and today's reward
    query_balance()

    # If check_in failed but balance page shows today's reward, the sign-in
    # actually succeeded (redeem response was blocked by Cloudflare)
    has_reward = any(m["name"] == "今日奖励" for m in msg)
    has_fail = any(m["name"] == "签到信息" and "失败" in m["value"] for m in msg)
    if has_reward and has_fail:
        msg = [m for m in msg if not (m["name"] == "签到信息" and "失败" in m["value"])]
        msg.insert(1, {"name": "签到信息", "value": "签到成功"})

    # Append timestamp from 今日奖励 to 签到信息
    reward_ts = ""
    for m in msg:
        if m["name"] == "今日奖励" and "（" in m["value"]:
            reward_ts = m["value"][m["value"].find("（"):]
            break
    if reward_ts:
        for m in msg:
            if m["name"] == "签到信息":
                m["value"] += reward_ts
                break

    # If check_in failed and no today's reward, the cookie may be expired
    has_fail = any(m["name"] == "签到信息" and "失败" in m["value"] for m in msg)
    if has_fail and not has_reward:
        # Check if already claimed today (mission page shows "已领取")
        # This covers the case where CI runs close to midnight and the
        # daily reset hasn't happened yet for V2EX's timezone
        already = any(m["name"] == "登录信息" and "已领取" in m.get("value", "") for m in msg)
        if already:
            msg = [m for m in msg if not (m["name"] == "签到信息" and "失败" in m["value"])]
            msg.append({"name": "签到信息", "value": "今日已签到"})
        else:
            msg.append({"name": "提示", "value": "签到可能失败，请检查 Cookie 是否过期"})

    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == "__main__":
    print(" V2EX 签到开始 ".center(60, "="))
    print(main())
    print(" V2EX 签到结束 ".center(60, "="), "\n")
