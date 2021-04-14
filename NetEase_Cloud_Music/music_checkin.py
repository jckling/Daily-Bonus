# -*- coding: utf-8 -*-
# @File     : music_checkin.py
# @Time     : 2021/04/07 20:46
# @Author   : Jckling

import base64
import hashlib
import json
import os

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

CELLPHONE = os.environ.get('MUSIC_CELLPHONE')
PASSWORD = os.environ.get('MUSIC_PASSWORD')


# MD5 哈希
def md5(text):
    h = hashlib.md5()
    h.update(text.encode(encoding='utf-8'))
    return h.hexdigest()


# AES-CBC 加密
def encrypt(key, text):
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key.encode('utf8')), modes.CBC(b'0102030405060708'), backend=backend)
    encryptor = cipher.encryptor()
    length = 16
    count = len(text.encode('utf-8'))
    if count % length != 0:
        add = length - (count % length)
    else:
        add = 16
    pad = chr(add)
    text1 = text + (pad * add)
    ciphertext = encryptor.update(text1.encode('utf-8')) + encryptor.finalize()
    crypted_str = str(base64.b64encode(ciphertext), encoding='utf-8')
    return crypted_str


# 加密数据
def protect(text):
    return {"params": encrypt('TA3YiYCfY2dDJQgg', encrypt('0CoJUm6Qyw8W8jud', text)),
            "encSecKey": "84ca47bca10bad09a6b04c5c927ef077d9b9f1e37098aa3eac6ea70eb59df0aa28b691b7e75e4f1f9831754919ea7"
                         "84c8f74fbfadf2898b0be17849fd656060162857830e241aba44991601f137624094c114ea8d17bce815b0cd4e5b8"
                         "e2fbaba978c6d1d14dc3d1faf852bdd28818031ccdaaa13a6018e1024e2aae98844210"}


HEADERS = {
    "Host": "music.163.com",
    "Connection": "keep-alive",
    "sec-ch-ua": '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
    "Nm-GCore-Status": "1",
    "sec-ch-ua-mobile": "?0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "*/*",
    "Origin": "https://music.163.com",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://music.163.com/",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,zh-TW;q=0.6,da;q=0.5",
}

SESSION = requests.Session()


# 登录
def login():
    headers = dict({"Cookie": "os=pc;"}, **HEADERS)

    logindata = {
        "phone": CELLPHONE,
        "countrycode": "86",
        "password": md5(PASSWORD),
        "rememberLogin": "true",
    }

    url = "https://music.163.com/weapi/login/cellphone"
    r = SESSION.post(url, data=protect(json.dumps(logindata)), headers=headers)

    obj = r.json()
    if obj["code"] == 200:
        print("登录成功")
        return True
    else:
        print(obj["message"])
        return False


# 签到
def check_in():
    url = "https://music.163.com/weapi/point/dailyTask"
    r = SESSION.post(url, data=protect('{"type":0}'), headers=HEADERS)

    obj = r.json()
    if obj["code"] == 200:
        print("签到成功，获得 %s 积分" % obj["point"])
    elif obj["code"] == -2:
        print(obj["msg"])
    else:
        print("签到失败：", obj["message"])


if __name__ == '__main__':
    print("=" * 20, " 网易云 签到开始 ", "=" * 20)
    if login():
        check_in()
    print("=" * 20, " 网易云 签到结束 ", "=" * 20, "\n")
