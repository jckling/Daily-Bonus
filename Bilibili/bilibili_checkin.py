# -*- coding: utf-8 -*-
# @File     : bilibili_checkin.py
# @Time     : 2021/04/07 15:10
# @Author   : Jckling

import os

import requests

# cookies
COOKIES = os.environ.get("BILIBILI_COOKIES")
SESSION = requests.Session()
msg = []

HEADERS = {
    "Host": "api.live.bilibili.com",
    "Connection": "keep-alive",
    "sec-ch-ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    "Accept": "application/json, text/plain, */*",
    "sec-ch-ua-mobile": "?0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "sec-ch-ua-platform": "Windows",
    "Origin": "https://live.bilibili.com",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://live.bilibili.com/",
    # "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8,ja;q=0.7,zh-TW;q=0.6",
    "Cookie": COOKIES,
}


# 直播间签到
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
        msg += [{"name": "check_in error", "value": e}]


def main():
    SESSION.headers.update(HEADERS)
    check_in()
    global msg
    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == '__main__':
    print(" Bilibili 签到开始 ".center(60, "="))
    print(main())
    print(" Bilibili 签到结束 ".center(60, "="), "\n")
