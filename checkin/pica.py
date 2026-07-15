# -*- coding: utf-8 -*-
# @File     : pica.py
# @Time     : 2022/03/02 15:33
# @Author   : Jckling

import hashlib
import hmac
import os
import time
import uuid

import requests

# info
EMAIL = os.environ.get("PICA_USERNAME")
PASSWORD = os.environ.get("PICA_PASSWORD")
msg = []

BASE_URL = "https://picaapi.picacomic.com"

API_KEY = "C69BAF41DA5ABD1FFEDC6D2FEA56B"
API_SECRET = "~d}$Q7$eIni=V)9\\RK/P.RM4;9[7|@/CA}b~OW!3?EV`:<>M7pddUBL5n|0/*Cn"

STATIC_HEADERS = {
    "accept": "application/vnd.picacomic.com.v1+json",
    "api-key": API_KEY,
    "app-build-version": "45",
    "app-channel": "3",
    "app-platform": "android",
    "app-version": "2.2.1.3.3.4",
    "app-uuid": "defaultUuid",
    "content-type": "application/json; charset=UTF-8",
    "image-quality": "original",
    "user-agent": "okhttp/3.8.1",
}


def gen_headers(method, path, token=None):
    """Generate request headers with HMAC-SHA256 signature."""
    nonce = uuid.uuid4().hex
    ts = str(int(time.time()))
    raw = (path + ts + nonce + method + API_KEY).lower()
    sig = hmac.new(API_SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()
    headers = {**STATIC_HEADERS, "nonce": nonce, "signature": sig, "time": ts}
    if token:
        headers["authorization"] = token
    return headers


def login():
    """Login with email and password, return token or None."""
    path = "auth/sign-in"
    headers = gen_headers("POST", path)
    r = requests.post(
        f"{BASE_URL}/{path}",
        headers=headers,
        json={"email": EMAIL, "password": PASSWORD},
    )
    obj = r.json()

    global msg
    if obj.get("code") == 200:
        msg.append({"name": "登录信息", "value": "登录成功"})
        return obj["data"]["token"]
    else:
        msg.append({"name": "登录信息", "value": f'登录失败，{obj.get("error", "unknown")}'})
        return None


def punch_in(token):
    """Punch in and return result status."""
    path = "users/punch-in"
    headers = gen_headers("POST", path, token)
    r = requests.post(f"{BASE_URL}/{path}", headers=headers)
    obj = r.json()

    global msg
    if obj.get("code") == 200:
        res = obj.get("data", {}).get("res", {})
        status = res.get("status", "")
        punch_day = res.get("punchInLastDay", "")

        if status == "ok":
            value = "打卡成功"
            if punch_day:
                value += f"（{punch_day}）"
            msg.append({"name": "签到信息", "value": value})
        elif status == "fail":
            msg.append({"name": "签到信息", "value": "今日已打卡"})
        else:
            msg.append({"name": "签到信息", "value": f"签到结果未知: {status}"})
    else:
        msg.append({"name": "签到信息", "value": f'签到失败，{obj.get("error", "unknown")}'})


def get_profile(token):
    """Get user profile: level, exp."""
    path = "users/profile"
    headers = gen_headers("GET", path, token)
    r = requests.get(f"{BASE_URL}/{path}", headers=headers)
    obj = r.json()

    global msg
    if obj.get("code") == 200:
        user = obj.get("data", {}).get("user", {})
        level = user.get("level", "?")
        exp = user.get("exp", "?")
        msg.append({"name": "等级经验", "value": f"Lv{level}，{exp} EXP"})


def main():
    global msg
    if not EMAIL or not PASSWORD:
        return "No PICA_USERNAME or PICA_PASSWORD set"

    token = login()
    if not token:
        return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])

    punch_in(token)
    get_profile(token)

    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == "__main__":
    print(" 哔咔漫画 签到开始 ".center(60, "="))
    print(main())
    print(" 哔咔漫画 签到结束 ".center(60, "="), "\n")
