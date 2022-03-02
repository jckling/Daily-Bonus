# -*- coding: utf-8 -*-
# @File     : pica_checkin.py
# @Time     : 2022/03/02 15:33
# @Author   : Jckling

import hashlib
import hmac
import json
import os
import time

import requests

# info
EMAIL = os.environ.get("PICA_EMAIL")
PASSWORD = os.environ.get("PICA_PASSWORD")
msg = []

# secret
api_key = "C69BAF41DA5ABD1FFEDC6D2FEA56B"
api_secret = "~d}$Q7$eIni=V)9\\RK/P.RM4;9[7|@/CA}b~OW!3?EV`:<>M7pddUBL5n|0/*Cn"
nonce = "b1ab87b4800d4d4590a11701b8551afa"

HEADERS = {
    "api-key": api_key,
    "accept": "application/vnd.picacomic.com.v1+json",
    "app-channel": "2",
    "time": str(int(time.time())),
    "nonce": nonce,
    "app-version": "2.2.1.2.3.3",
    "app-uuid": "defaultUuid",
    "app-platform": "android",
    "app-build-version": "44",
    "Content-Type": "application/json; charset=UTF-8",
    "User-Agent": "okhttp/3.8.1",
    "image-quality": "original",
}

SESSION = requests.Session()
# proxies = {'http': "127.0.0.1:7890", 'https': "127.0.0.1:7890"}
# SESSION.proxies.update(proxies)


# 登录
def login():
    raw = "auth/sign-in" + HEADERS["time"] + nonce + "POST" + api_key
    raw = raw.lower()
    h = hmac.new(api_secret.encode(), digestmod=hashlib.sha256)
    h.update(raw.encode())
    HEADERS["signature"] = h.hexdigest()

    logindata = {
        "email": EMAIL,
        "password": PASSWORD
    }

    url = "https://picaapi.picacomic.com/auth/sign-in"
    r = SESSION.post(url, data=json.dumps(logindata), headers=HEADERS)
    obj = r.json()
    HEADERS["authorization"] = obj.get("data", {}).get("token", {})

    global msg
    if (obj["code"] == 200):
        msg += [
            {"name": "登录信息", "value": "登录成功"}
        ]
        return True
    else:
        msg += [
            {"name": "登录信息", "value": f'登录失败，{obj["message"]}'}
        ]
        return False


# 签到
def check_in():
    url = "https://picaapi.picacomic.com/users/punch-in"
    r = SESSION.post(url, headers=HEADERS)
    obj = r.json()

    global msg
    if obj["code"] == 200:
        msg += [
            {"name": "签到信息", "value": "打卡成功"}
        ]
    else:
        msg += [
            {"name": "签到信息", "value": f'签到异常，{obj["error"]}'}
        ]


# 查询
def query():
    url = "https://picaapi.picacomic.com/users/profile"
    r = SESSION.get(url, headers=HEADERS)
    obj = r.json()

    global msg
    if (obj["code"] == 200 and obj["isPunched"]):
        msg += [
            {"name": "签到信息", "value": "打卡成功"}
        ]
    else:
        msg += [
            {"name": "签到信息", "value": f'签到失败，{obj["error"]}'}
        ]


def main():
    if login():
        check_in()
    global msg
    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == '__main__':
    print(" 哔咔漫画 签到开始 ".center(60, "="))
    print(main())
    print(" 哔咔漫画 签到结束 ".center(60, "="), "\n")
