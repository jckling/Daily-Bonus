# -*- coding: utf-8 -*-
# @File     : yamibo.py
# @Time     : 2021/04/07 15:48
# @Author   : Jckling

import os

import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from bs4 import BeautifulSoup
from lxml import html

# cookies
COOKIES = os.environ.get("YAMIBO_COOKIES") or 'EeqY_2132_newemail=689055%091335176598%40qq.com%091750428435; EeqY_2132_nofavfid=1; EeqY_2132_smile=4D1; EeqY_2132_saltkey=eU8I8vZ0; EeqY_2132_lastvisit=1772084200; acw_tc=af0c62a917732990851864817e7b150e59eefc65cc5e3a91856c4f90cd; cdn_sec_tc=af0c62a917732990851864817e7b150e59eefc65cc5e3a91856c4f90cd; EeqY_2132_ulastactivity=4ded%2BZWgwmeHAefFCCJAKniJSpdYh33wrjZXV3nGy3mKzujv25iF; EeqY_2132_auth=2643Zuf%2F1N%2FsuUX%2BuwZjSzx1iP1Mtk%2FjB7bV0h30uMNqct%2FCEVRoU%2BFF6WwT2aUwqZQhAx75hXcHxzvn8%2Bh6xQWFI3s; EeqY_2132_lastcheckfeed=243370%7C1773299081; EeqY_2132_member_login_status=1; EeqY_2132_visitedfid=30; EeqY_2132_sid=kmLo8q; EeqY_2132_lip=175.12.98.169%2C1773299081; EeqY_2132_st_t=243370%7C1773302406%7C21476c826de848db92e43f6d8f39524b; EeqY_2132_forum_lastvisit=D_30_1773302406; EeqY_2132_checkpm=1; EeqY_2132_lastact=1773302407%09home.php%09misc; EeqY_2132_sendmail=1'
msg = []

HEADERS = {
    "Host": "bbs.yamibo.com",
    "Connection": "keep-alive",
    # "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    # "sec-ch-ua-mobile": "?0",
    # "sec-ch-ua-platform": "macOS",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    # "Sec-Fetch-Site": "none",
    # "Sec-Fetch-Mode": "navigate",
    # "Sec-Fetch-User": "?1",
    # "Sec-Fetch-Dest": "document",
    "Referer": "https://bbs.yamibo.com/plugin.php?id=zqlj_sign",
    # "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8,ja;q=0.7,zh-TW;q=0.6",
    "Cookie": COOKIES,
}

# Bypass Cloudflare
SESSION = requests.Session()

# 登录
def fhash():
    with Stealth().use_sync(sync_playwright()) as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://bbs.yamibo.com/plugin.php?id=zqlj_sign")
        page.wait_for_load_state("networkidle")
        
        # Check if we got in
        if "Just a moment" in page.title():
            print("Still blocked by Cloudflare")
        else:
            print("Success! Page content:")
            print(page.content())
            
        browser.close()
    return ""
        

    # tree = html.fromstring(r.text)

    # try:
    #     hash = tree.xpath('//*[@id="scbar_form"]/input[2]')[0].attrib['value']
    #     return hash
    # except Exception as e:
    #     global msg
    #     msg += [{"name": "get form fhash error", "value": e}]
    #     return ""


# 签到
def check_in():
    code = fhash()
    if code == "":
        return False

    url = "https://bbs.yamibo.com/plugin.php?id=zqlj_sign&sign=" + code
    r = SESSION.get(url)
    tree = html.fromstring(r.text)

    global msg
    try:
        message = tree.xpath('//*[@id="messagetext"]/p[1]/text()')[0]
        if "打卡成功" in message:
            msg += [{"name": "签到信息", "value": "签到成功"}]
        elif "打过卡" in message:
            msg += [{"name": "签到信息", "value": "已签到"}]
        elif "登录" in message:
            msg += [{"name": "签到信息", "value": "登录失败，Cookie 可能已失效"}]
            return False
        else:
            msg += [{"name": "签到信息", "value": message}]
            return False
        return True
    except Exception as e:
        msg += [{"name": "check_in error", "value": e}]
        return False


# 查询
def query_credit():
    # 对象信息
    r = SESSION.get("https://bbs.yamibo.com/plugin.php?id=zqlj_sign")
    tree = html.fromstring(r.text)

    global msg
    try:
        checkin_msg = tree.xpath('//div[@class="bm signbtn cl"]/a/text()')[0]
        stat = tree.xpath('//*[@id="wp"]/div[2]/div[2]/div[3]/div[2]/ul/li/text()')
        msg += [{"name": s.split("：")[0], "value": s.split("：")[1]} for s in stat]
    except Exception as e:
        msg += [{"name": "查询对象失败", "value": e}]

    # 积分信息
    r = SESSION.get("https://bbs.yamibo.com/home.php?mod=spacecp&ac=credit")
    soup = BeautifulSoup(r.text, "lxml")
    tree = html.fromstring(str(soup))
    try:
        credit = tree.xpath('//ul[@class="creditl mtm bbda cl"]/li/text()')
        data = [i.strip() for i in credit]
        msg += [
            {"name": "对象", "value": data[1]},
            {"name": "积分", "value": data[2]},
            {"name": "总积分", "value": data[3]},
            {"name": "规则", "value": "总积分 = 积分 + 对象/3"}
        ]
    except Exception as e:
        msg += [{"name": "查询积分失败", "value": e}]


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
