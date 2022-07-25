# -*- coding: utf-8 -*-
# @File     : yamibo_checkin.py
# @Time     : 2021/04/07 15:48
# @Author   : Jckling

import os

import requests
from bs4 import BeautifulSoup
from lxml import html

# cookies
COOKIES = os.environ.get("YAMIBO_COOKIES")
SESSION = requests.Session()
msg = []

HEADERS = {
    "Host": "bbs.yamibo.com",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "sec-ch-ua": '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8,ja;q=0.7,zh-TW;q=0.6,da;q=0.5",
    "Cookie": COOKIES
}


# 登录
def fhash():
    url = "https://bbs.yamibo.com/forum.php"
    r = SESSION.get(url)
    tree = html.fromstring(r.text)

    try:
        hash = tree.xpath('//input[@name="formhash"]')[0].attrib['value']
        return hash
    except Exception as e:
        return ""


# 签到
def check_in():
    url = "https://bbs.yamibo.com/plugin.php?id=study_daily_attendance:daily_attendance&fhash=" + fhash()
    r = SESSION.get(url)
    tree = html.fromstring(r.text)

    global msg
    if "签到成功" in r.text or "已签到" in r.text:
        msg += [
            {"name": "账户信息", "value": tree.xpath('//ul[@id="mycp1_menu"]/a/text()')[0]},
            {"name": "签到信息", "value": tree.xpath('//div[@id="messagetext"]/p/text()')[0]}
        ]
    elif "登录" in r.text:
        msg += [
            {"name": "签到信息", "value": "登录失败，Cookie 可能已经失效"},
        ]
        return False
    else:
        msg += [
            {"name": "签到信息", "value": "未知错误"},
        ]
        return False
    return True


# 查询
def query_credit():
    url = "https://bbs.yamibo.com/home.php?mod=spacecp&ac=credit&op=base"
    r = SESSION.get(url)

    soup = BeautifulSoup(r.text, "lxml")
    tree = html.fromstring(str(soup))
    credit = tree.xpath('//ul[@class="creditl mtm bbda cl"]/li/text()')

    global msg
    data = [i.strip() for i in credit]
    msg += [
        {"name": "对象", "value": data[0]},
        {"name": "积分", "value": data[1]},
        {"name": "总积分", "value": data[2]},
        {"name": "规则", "value": "总积分 = 积分 + 对象/3"},
    ]


def main():
    SESSION.headers.update(HEADERS)
    if check_in():
        query_credit()
    global msg
    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == '__main__':
    print(" 300 签到开始 ".center(60, "="))
    print(main())
    print(" 300 签到结束 ".center(60, "="), "\n")
