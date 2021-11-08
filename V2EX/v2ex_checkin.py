# -*- coding: utf-8 -*-
# @File     : v2ex_checkin.py
# @Time     : 2021/04/08 09:43
# @Author   : Jckling

import os
import re
import time
from datetime import date, datetime

import requests
from lxml import html

# cookies
COOKIES = os.environ.get("V2EX_COOKIES")
SESSION = requests.Session()
msg = []

HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,zh-TW;q=0.6,da;q=0.5",
    "cache-control": "no-cache",
    "Cookie": COOKIES,
    "pragma": "no-cache",
    "Referer": "https://www.v2ex.com/",
    "sec-ch-ua": '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
    "x-requested-with": "X",
}


# 获取 once
def get_once():
    url = "https://www.v2ex.com/mission/daily"
    r = SESSION.get(url, headers=HEADERS)

    global msg
    if "你要查看的页面需要先登录" in r.text:
        msg += [
            {"name": "登录信息", "value": "登录失败，Cookie 可能已经失效"}
        ]
        return "", False
    elif "每日登录奖励已领取" in r.text:
        msg += [
            {"name": "登录信息", "value": "每日登录奖励已领取，" + re.search(r"已连续登录 \d+ 天", r.text)[0]}
        ]
        return "", True

    once = re.search(r"once=(\d+)", r.text).group(1)
    msg += [
        {"name": "登录信息", "value": "登录成功"}
    ]
    return once, True


# 签到
def check_in(once):
    # 无内容返回
    url = "https://www.v2ex.com/mission/daily/redeem?once=" + once
    SESSION.get(url, headers=HEADERS)


# 查询
def query_balance():
    url = "https://www.v2ex.com/balance"
    r = SESSION.get(url, headers=HEADERS)
    tree = html.fromstring(r.content)

    # 签到结果
    global msg
    checkin_day_str = tree.xpath('//small[@class="gray"]/text()')[0]
    checkin_day = datetime.now().astimezone().strptime(checkin_day_str, '%Y-%m-%d %H:%M:%S %z')
    print(checkin_day.date(), date.today())
    if checkin_day.date() == date.today():
        # 签到奖励
        bonus = re.search('\d+ 的每日登录奖励 \d+ 铜币', r.text)[0]
        msg += [
            {"name": "签到信息", "value": bonus}
        ]

        # 余额
        balance = tree.xpath('//div[@class="balance_area bigger"]/text()')
        if len(balance) == 2:
            balance = ['0'] + balance

        golden, silver, bronze = [s.strip() for s in balance]
        msg += [
            {"name": "账户余额", "value": f"{golden} 金币，{silver} 银币，{bronze} 铜币"}
        ]
    else:
        msg += [
            {"name": "签到信息", "value": "签到失败"},
            {"name": "账户余额", "value": "获取失败"}
        ]


def main():
    for i in range(3):
        try:
            once, success = get_once()
        except AttributeError:
            if i < 3:
                time.sleep(3)
                continue
            else:
                raise
        break
    if once:
        check_in(once)
    if success:
        query_balance()
    global msg
    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == '__main__':
    print(" V2EX 签到开始 ".center(60, "="))
    print(main())
    print(" V2EX 签到结束 ".center(60, "="), "\n")
