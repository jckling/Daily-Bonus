# -*- coding: utf-8 -*-
# @File     : message.py
# @Time     : 2021/10/17 19:24
# @Author   : Jckling

import os

import requests

# info
TG_USER_ID = os.getenv("TG_USER_ID")
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHECKIN_LIST = ["BILIBILI", "V2EX", "YAMIBO", "MUSIC163"]

if __name__ == '__main__':
    content = "".join([os.getenv(e) for e in CHECKIN_LIST])
    data = {"chat_id": TG_USER_ID, "text": content, "disable_web_page_preview": "true"}
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

    print("Telegram 推送开始".center(60, "="))
    r = requests.post(url=url, data=data)
    print(r.text)
    print("Telegram 推送结束".center(60, "="), "\n")
