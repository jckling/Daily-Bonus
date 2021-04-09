# -*- coding: utf-8 -*-
# @File     : bilibili_checkin.py
# @Time     : 2021/04/07 15:10
# @Author   : Jckling

import os

import requests

COOKIES = os.environ.get("BILIBILI_COOKIES")

SESSION = requests.Session()


# 签到
def check_in():
    headers = {
        "Host": "api.live.bilibili.com",
        "Connection": "keep-alive",
        "sec-ch-ua": '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
        "Accept": "application/json, text/plain, */*",
        "sec-ch-ua-mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
        "Origin": "https://link.bilibili.com",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://link.bilibili.com/p/center/index",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,zh-TW;q=0.6,da;q=0.5",
        "Cookie": COOKIES
    }

    url = "https://api.live.bilibili.com/xlive/web-ucenter/v1/sign/DoSign"
    r = SESSION.get(url, headers=headers)

    try:
        obj = r.json()
        if obj["code"] == 0:
            print(obj["data"]["text"])
            print(obj["data"]["specialText"])
            print("本月已签到 %d 天" % obj["data"]["hadSignDays"])
        elif obj["code"] == 1011040:
            print(obj["message"])
        else:
            print("签到失败")
    except Exception as e:
        print("签到异常", e)
    else:
        return False


if __name__ == '__main__':
    check_in()
