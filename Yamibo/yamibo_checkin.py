# -*- coding: utf-8 -*-
# @File     : yamibo_checkin.py
# @Time     : 2021/04/07 15:48
# @Author   : Jckling

import os

import cloudscraper
import requests
from bs4 import BeautifulSoup
from lxml import html

# cookies
COOKIES = {
    "EeqY_2132_saltkey": os.environ.get("YAMIBO_EEQY_2132_SALTKEY"),
    "EeqY_2132_auth": os.environ.get("YAMIBO_EEQY_2132_AUTH"),
}

# session
SESSION = requests.Session()

# Bypass Cloudflare
scraper = cloudscraper.create_scraper(sess=SESSION)

# message
msg = []


# 登录
def fhash():
    url = "https://bbs.yamibo.com"
    r = scraper.get(url)
    tree = html.fromstring(r.text)

    try:
        hash = tree.xpath('//input[@name="formhash"]')[0].attrib['value']
        return hash
    except Exception as e:
        print("no form hash")
        print(r.headers)
        return ""


# 签到
def check_in():
    url = "https://bbs.yamibo.com/plugin.php?id=zqlj_sign&sign=" + fhash()
    r = scraper.get(url)
    tree = html.fromstring(r.text)

    global msg
    if "打卡成功" in r.text:
        msg += [
            {"name": "账户信息", "value": tree.xpath('//*[@id="avtnav_menu"]/a[1]/text()')[0]},
            {"name": "签到信息", "value": "签到成功"}
        ]
    elif "打过卡" in r.text:
        msg += [
            {"name": "账户信息", "value": tree.xpath('//*[@id="avtnav_menu"]/a[1]/text()')[0]},
            {"name": "签到信息", "value": "已签到"}
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
    url = "https://bbs.yamibo.com/home.php?mod=spacecp&ac=credit"
    r = SESSION.get(url)

    soup = BeautifulSoup(r.text, "lxml")
    tree = html.fromstring(str(soup))
    credit = tree.xpath('//ul[@class="creditl mtm bbda cl"]/li/text()')

    global msg
    data = [i.strip() for i in credit]
    msg += [
        {"name": "对象", "value": data[1]},
        {"name": "积分", "value": data[2]},
        {"name": "总积分", "value": data[3]},
        {"name": "规则", "value": "总积分 = 积分 + 对象/3"},
    ]


def main():
    SESSION.cookies.update(COOKIES)
    if check_in():
        query_credit()
    global msg
    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == '__main__':
    print(" 300 签到开始 ".center(60, "="))
    print(main())
    print(" 300 签到结束 ".center(60, "="), "\n")
