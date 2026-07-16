# -*- coding: utf-8 -*-
# @File     : bilibili.py
# @Time     : 2021/04/07 15:10
# @Author   : Jckling

import os
import time

import requests

# cookies
COOKIES = os.environ.get("BILIBILI_COOKIES")
SESSION = requests.Session()
msg = []

BASE_URL = "https://api.bilibili.com"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
    "cookie": COOKIES or "",
    "origin": "https://www.bilibili.com",
    "referer": "https://www.bilibili.com/",
    "sec-ch-ua": '"Not;A-Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
}


def visit_homepage():
    """Visit bilibili.com homepage to trigger the automatic daily coin reward."""
    url = "https://www.bilibili.com/"
    SESSION.get(url, headers=HEADERS)


def get_nav():
    """Get account info and trigger login visit."""
    url = f"{BASE_URL}/x/web-interface/nav"
    r = SESSION.get(url, headers=HEADERS)
    obj = r.json()

    global msg
    if obj.get("code") != 0:
        msg.append({"name": "登录信息", "value": "登录失败，Cookie 可能已经失效"})
        return False

    data = obj["data"]
    uname = data.get("uname", "")
    level = data.get("level_info", {}).get("current_level", "?")
    masked = "█" * len(uname)
    msg.append({"name": "登录信息", "value": f"{masked} (Lv{level})"})
    return True


def get_coins():
    """Get coin balance from account.bilibili.com."""
    url = "https://account.bilibili.com/site/getCoin"
    r = SESSION.get(url, headers=HEADERS)
    obj = r.json()

    global msg
    if obj.get("code") == 0:
        money = obj.get("data", {}).get("money", 0)
        msg.append({"name": "硬币余额", "value": str(money)})


def get_coin_log():
    """Check today's login reward from coin log.

    Bilibili grants 1 coin automatically when a logged-in user visits the
    site. The coin log API returns recent records (multiple days), so we
    filter by today's date to determine if the login reward was claimed.
    """
    url = f"{BASE_URL}/x/member/web/coin/log?jsonp=jsonp"
    r = SESSION.get(url, headers=HEADERS)
    obj = r.json()

    global msg
    if obj.get("code") == 0:
        today = time.strftime("%Y-%m-%d")
        coin_list = obj.get("data", {}).get("list", [])
        login_reward = [
            c for c in coin_list
            if c.get("reason") == "登录奖励" and c.get("time", "").startswith(today)
        ]
        if login_reward:
            reward_time = login_reward[0].get("time", "")
            msg.append({"name": "登录奖励", "value": f"已领取 {login_reward[0]['delta']} 硬币（{reward_time}）"})
        else:
            msg.append({"name": "登录奖励", "value": "今日未领取"})


def main():
    global msg
    if not COOKIES:
        return "No BILIBILI_COOKIES set"

    if not get_nav():
        return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])

    # Visit homepage to trigger automatic daily coin reward
    visit_homepage()
    time.sleep(2)

    get_coins()
    get_coin_log()

    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == "__main__":
    print(" Bilibili 签到开始 ".center(60, "="))
    print(main())
    print(" Bilibili 签到结束 ".center(60, "="), "\n")
