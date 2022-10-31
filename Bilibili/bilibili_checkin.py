# -*- coding: utf-8 -*-
# @File     : bilibili_checkin.py
# @Time     : 2021/04/07 15:10
# @Author   : Jckling

import os
import uuid

import requests

# cookies
COOKIES = {
    "bili_jct": os.environ.get("BILIBILI_BILI_JCT"),
    "DedeUserID": os.environ.get("BILIBILI_DEDEUSERID"),
    "SESSDATA": os.environ.get("BILIBILI_SESSDATA"),
}
SESSION = requests.Session()
msg = []

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,zh-TW;q=0.6,da;q=0.5",
    "Referer": "https://www.bilibili.com/",
    "Connection": "keep-alive",
}


# 登录
def login():
    url = "https://api.bilibili.com/x/web-interface/nav"
    r = SESSION.get(url)

    global msg
    try:
        obj = r.json()
        data = obj.get("data", {})
        if data:
            if data["isLogin"]:
                msg += [
                    {"name": "登录信息", "value": "登录成功"},
                    {"name": "账户信息", "value": data["uname"]},
                ]
                return True
            else:
                msg += [
                    {"name": "登录信息", "value": "登录失败"}
                ]
    except Exception as e:
        msg += [
            {"name": "登录信息", "value": "登录异常，" + str(e)}
        ]
    return False


# 签到
def check_in():
    url = "https://api.live.bilibili.com/xlive/web-ucenter/v1/sign/DoSign"
    r = SESSION.get(url)

    global msg
    try:
        obj = r.json()
        if obj["code"] == 0:
            msg += [
                {"name": "签到信息", "value": obj["data"]["text"]},
                {"name": "特别信息", "value": f'本月已签到 {obj["data"]["hadSignDays"]} 天' +
                                              (f'，{obj["data"]["specialText"]}' if obj["data"]["specialText"] else '')},
            ]
        elif obj["code"] == 1011040:
            msg += [
                {"name": "签到信息", "value": "今日已签到，无法重复签到"}
            ]
        else:
            msg += [
                {"name": "签到信息", "value": "签到失败"}
            ]
    except Exception as e:
        msg += [
            {"name": "签到信息", "value": "签到异常，" + str(e)}
        ]
    else:
        return False


def main():
    COOKIES["buvid3"] = str(uuid.uuid1())
    SESSION.headers.update(HEADERS)
    SESSION.cookies.update(COOKIES)
    if login():
        check_in()
    global msg
    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == '__main__':
    print(" Bilibili 签到开始 ".center(60, "="))
    print(main())
    print(" Bilibili 签到结束 ".center(60, "="), "\n")
