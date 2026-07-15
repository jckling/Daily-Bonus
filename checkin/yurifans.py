# -*- coding: utf-8 -*-
# @File     : yurifans.py
# @Time     : 2023/04/25 12:17
# @Author   : Cloudac7

import os
import time

from curl_cffi import requests as cffi_requests

# info
USERNAME = os.environ.get("YURIFANS_EMAIL")
PASSWORD = os.environ.get("YURIFANS_PASSWORD")
msg = []

BASE_URL = "https://yuri.website"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
    "content-type": "application/x-www-form-urlencoded",
    "origin": BASE_URL,
    "referer": f"{BASE_URL}/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
}


def login():
    """Login with email and password, return b2_token or None."""
    url = f"{BASE_URL}/wp-json/jwt-auth/v1/token"
    r = cffi_requests.post(
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
        "cookie": f"b2_token={b2_token}",
        "authorization": f"Bearer {b2_token}",
    }


def get_user_info(b2_token):
    """Get user info to verify login."""
    headers = get_auth_headers(b2_token)
    r = cffi_requests.post(
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
    r = cffi_requests.post(
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
    r = cffi_requests.post(
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

    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == "__main__":
    print(" Yurifans 签到开始 ".center(60, "="))
    print(main())
    print(" Yurifans 签到结束 ".center(60, "="), "\n")
