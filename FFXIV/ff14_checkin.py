# -*- coding: utf-8 -*-
# @File     : ff14_checkin.py
# @Time     : 2021/03/24 15:43
# @Author   : Jckling

import json
import os
import time

import requests

# info
USERNAME = os.environ.get('FFXIV_USERNAME')
PASSWORD = os.environ.get('FFXIV_PASSWORD')
AREA_NAME = os.environ.get('FFXIV_AREA_NAME')
SERVER_NAME = os.environ.get('FFXIV_SERVER_NAME')
ROLE_NAME = os.environ.get('FFXIV_ROLE_NAME')

# cookies
COOKIES = {}


# 设置 cookies
def set_cookies(items):
    global COOKIES
    for i in items:
        COOKIES.setdefault(i[0], i[1])


# 登录
def login():
    headers = {
        "Host": "cas.sdo.com",
        "Connection": "keep-alive",
        "sec-ch-ua": '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
        "Accept": "*/*",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Dest": "script",
        "Referer": "https://login.u.sdo.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,zh-TW;q=0.6,da;q=0.5",
        "Cookie": "CASCID=CIDF4FE36AE09944418AEBD8394F75B8ED3; hasAdsr=1",
    }

    params = {
        "_": int(round(time.time() * 1000)),
        "appId": "100001900",
        "areaId": "1",
        "authenSource": "2",
        "autoLoginFlag": "0",
        "callback": "staticLogin_JSONPMethod",
        # "customSecurityLevel": "2",
        "frameType": "3",
        "inputUserId": USERNAME,
        # "isEncrypt": "1",
        "locale": "zh_CN",
        "password": PASSWORD,
        "productId": "2",
        "productVersion": "v5",
        "scene": "login",
        "serviceUrl": "https://actff1.web.sdo.com/20180707jifen/Server/SDOLogin.ashx?returnPage=index.html",
        "tag": "20",
        "usage": "aliCode",
        "version": "21",
    }

    url = "https://cas.sdo.com/authen/staticLogin.jsonp"
    r = requests.get(url, headers=headers, params=params)
    set_cookies(r.cookies.items())

    # 获取 ticket 字段
    text = r.text
    text = text[text.find("(") + 1: text.rfind(")")]
    obj = json.loads(text)
    if "ticket" in obj["data"]:
        print('登录成功')
        return obj["data"]["ticket"]
    elif "captchaParams" in obj["data"]:
        print("登录失败次数过多，要求通过验证码")
    else:
        print(obj["data"]["failReason"])
    return ""


# 获取 cookies
def get_cookies(ticket):
    params = {
        "_": "1617715671699",
        "appId": "100001900",
        "areaId": "1",
        "authenSource": "2",
        "callback": "getPromotionInfo_JSONPMethod",
        "frameType": "3",
        "locale": "zh_CN",
        "productId": "2",
        "productVersion": "v5",
        "scene": "login",
        "serviceUrl": "https://actff1.web.sdo.com/20180707jifen/Server/SDOLogin.ashx?returnPage=index.html",
        "tag": "20",
        "usage": "aliCode",
        "version": "21",
        "customSecurityLevel": "2",
    }

    url = "https://cas.sdo.com/authen/getPromotionInfo.jsonp"
    r = requests.get(url, params=params, cookies=COOKIES)
    set_cookies(r.cookies.items())


# 认证
def auth(ticket):
    params = {
        "returnPage": "index.html",
        "ticket": ticket,
    }

    url = "https://actff1.web.sdo.com//20180707jifen/Server/SDOLogin.ashx"
    r = requests.get(url, params=params, cookies=COOKIES)
    set_cookies(r.cookies.items())


# 选择角色
def select_role():
    if AREA_NAME == "陆行鸟":
        ipid = "1"
    elif AREA_NAME == "莫古力":
        ipid = "6"
    elif AREA_NAME == "猫小胖":
        ipid = "7"
    elif AREA_NAME == "豆豆柴":
        ipid = "8"

    params = {
        "method": "queryff14rolelist",
        "ipid": ipid,
        "i": "0.6531217873613295",
    }

    url = "http://act.ff.sdo.com/20180707jifen/Server/ff14/HGetRoleList.ashx"
    r = requests.get(url, params=params, cookies=COOKIES)

    # 获取角色 id
    obj = r.json()
    attach = obj["Attach"]
    role = "{0}|{1}|{2}"
    for r in attach:
        if r["worldnameZh"] == SERVER_NAME and r["name"] == ROLE_NAME:
            role = role.format(r["cicuid"], r["worldname"], r["groupid"])
            break

    # 选择角色
    areaid = ipid
    params = {
        "method": "setff14role",
        "AreaId": areaid,
        "AreaName": AREA_NAME,
        "RoleName": "[%s]%s" % (SERVER_NAME, ROLE_NAME),
        "Role": role,
        "i": "0.16795254979041618",
    }

    r = requests.post(url, params=params, cookies=COOKIES)
    obj = r.json()
    if obj["Success"]:
        print("角色选定成功")
    else:
        print(obj["Message"])


# 签到
def check_in():
    params = {
        "method": "signin",
        "i": "0.8613162421160268"
    }

    url = "http://act.ff.sdo.com/20180707jifen/Server/User.ashx"
    r = requests.post(url, params=params, cookies=COOKIES)

    obj = r.json()
    if obj["Success"]:
        print("签到成功")
    else:
        print(obj["Message"])


# 查询积分
def query_points():
    params = {
        "method": "querymystatus",
        "i": "0.6792009762893907"
    }

    url = "http://act.ff.sdo.com/20180707jifen/Server/User.ashx"
    r = requests.post(url, params=params, cookies=COOKIES)

    obj = r.json()
    points = json.loads(obj["Attach"])["Jifen"]
    print("当前积分为: %d" % points)


if __name__ == "__main__":
    print(" FF14 签到开始 ".center(60, "="))
    ticket = login()
    if ticket != "":
        get_cookies(ticket)
        auth(ticket)
        select_role()
        check_in()
        query_points()
    print(" FF14 签到结束 ".center(60, "="), "\n")
