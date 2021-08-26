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

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,zh-TW;q=0.6,da;q=0.5",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    "Referer": "https://bbs.yamibo.com/forum.php",
    "sec-ch-ua": '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
    "sec-ch-ua-mobile": "?0",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Connection": "keep-alive",
    "Host": "bbs.yamibo.com",
    "Cookie": COOKIES
}


def fhash():
    url = "https://bbs.yamibo.com/forum.php"
    r = SESSION.get(url, headers=HEADERS)
    tree = html.fromstring(r.text)
    hash = tree.xpath('//input[@name="formhash"]')[0].attrib['value']
    return hash


# 签到
def check_in():
    url = "https://bbs.yamibo.com/plugin.php?id=study_daily_attendance:daily_attendance&fhash=" + fhash()
    r = SESSION.get(url, headers=HEADERS)

    if "签到成功" in r.text:
        tree = html.fromstring(r.text)
        print(tree.xpath('//div[@id="messagetext"]/text()'))
    elif "登录" in r.text:
        print("登录失败，Cookie 可能已经失效")
        return False
    else:
        print("今日已签到")

    return True


# 查询
def query_credit():
    url = "https://bbs.yamibo.com/home.php?mod=spacecp&ac=credit&op=base"
    r = SESSION.get(url, headers=HEADERS)

    soup = BeautifulSoup(r.text, "lxml")
    tree = html.fromstring(str(soup))
    credit = tree.xpath('//ul[@class="creditl mtm bbda cl"]/li/text()')
    print("对象:\t %s\t\n"
          "积分:\t %s\t\n"
          "总积分:\t %s 点\t\n"
          "规则：总积分 = 积分 + 对象/3" % tuple([i.strip() for i in credit]))


if __name__ == '__main__':
    print(" 300 签到开始 ".center(60, "="))
    if check_in():
        query_credit()
    print(" 300 签到结束 ".center(60, "="), "\n")
