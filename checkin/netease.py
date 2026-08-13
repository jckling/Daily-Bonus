# -*- coding: utf-8 -*-
# @File     : netease.py
# @Time     : 2026/08/12
# @Author   : Jckling

import os

from curl_cffi import requests as cffi_requests

# cookies
COOKIES = os.environ.get("NETEASE_MUSIC_COOKIES")
msg = []

BASE_URL = "https://music.163.com"

SESSION = cffi_requests.Session()

HEADERS = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": COOKIES or "",
    "referer": "https://music.163.com/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
}


def pointmall_sign():
    """积分商城签到（云贝）"""
    r = SESSION.post(
        f"{BASE_URL}/api/pointmall/user/sign",
        headers=HEADERS,
        impersonate="chrome",
    )
    obj = r.json()

    global msg
    code = obj.get("code", -1)
    if code == 200:
        data = obj.get("data", {})
        signed = data.get("sign", False)
        yunbei = data.get("yunbeiNum", 0)
        if signed:
            msg.append({"name": "云贝签到", "value": f"签到成功，获得 {yunbei} 云贝"})
        else:
            msg.append({"name": "云贝签到", "value": "今日已签到"})
    else:
        msg.append({"name": "云贝签到", "value": f"签到失败，code={code}"})


def get_sign_info():
    """查询签到信息"""
    global msg

    r = SESSION.get(
        f"{BASE_URL}/api/pointmall/sign/calendar",
        headers=HEADERS,
        impersonate="chrome",
    )
    obj = r.json()
    if obj.get("code") == 200:
        sign_str = obj.get("data", {}).get("signStr", "")
        count = sign_str.count("1")
        msg.append({"name": "本月签到", "value": f"{count} 天"})


def main():
    global msg
    if not COOKIES:
        return "No NETEASE_MUSIC_COOKIES set"

    pointmall_sign()
    get_sign_info()

    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == "__main__":
    print(" 网易云音乐签到开始 ".center(60, "="))
    print(main())
    print(" 网易云音乐签到结束 ".center(60, "="), "\n")
