# -*- coding: utf-8 -*-
# @File     : yurifans_checkin.py
# @Time     : 2023/04/25 12:17
# @Author   : Cloudac7

# %%
import os
import requests
from time import sleep

# session
SESSION = requests.session()

# info
USERNAME = os.environ.get('YURIFANS_EMAIL')
PASSWORD = os.environ.get('YURIFANS_PASSWORD')

# message
msg = []

# 登录
def login():
    url = "https://yuri.website/wp-json/jwt-auth/v1/token"
    headers = {
        "accept": "application/json, text/plain, */*",
        "referer": "https://yuri.website/",
        "content-type": "application/x-www-form-urlencoded",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
    }
    form_data = {
        "username": USERNAME,
        "password": PASSWORD,
    }

    try:
        req = SESSION.post(
            url, 
            headers=headers,
            data=form_data
        )
        b2_token = req.cookies.get("b2_token")
        return b2_token
    except Exception as e:
        print("登录失败, 请检查账号密码是否正确")
        return ""

# 获取用户信息
def check_user_info(b2_token):
    url = "https://yuri.website/wp-json/b2/v1/getUserInfo"
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f'Bearer {b2_token}',
        "content-type": "application/x-www-form-urlencoded",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
    }
    req = SESSION.post(url, headers=headers)
    if req.status_code != 200:
        print('获取用户信息失败')
        return False
    else:
        try:
            user_data = req.json()["user_data"]
        except Exception as e:
            print('获取用户信息失败')
            print(req.json())
            return False
    
    global msg
    msg += [
        {"name": "账户信息", "value": user_data.get("name")},
    ]
    return True
    

# 查询
def query_credit(b2_token):
    url = "https://yuri.website/wp-json/b2/v1/getUserMission"

    headers = {
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "authorization": 'Bearer ' + b2_token
    }
    
    global msg

    req = SESSION.post(url, headers=headers)
    
    if req.status_code != 200:
        return True
    
    mission = req.json().get("mission")
    date = mission.get("date")
    my_credit = mission.get("my_credit", 0)
    msg += [{"name": "当前积分", "value": my_credit}]
    if date == "":
        return True
    else:
        credit = mission.get("credit", 0) 
        msg += [{"name": "签到信息", "value": "今日已经签到"}]
        msg += [{"name": "今日获取积分", "value": credit}]
        return False


# 签到
def check_in(b2_token):
    headers = {
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "authorization": 'Bearer ' + b2_token
    }
    url = "https://yuri.website/wp-json/b2/v1/userMission"

    req = SESSION.post(
        url, 
        headers=headers
    )

    global msg
    
    if req.status_code != 200:
        msg += [{"name": "签到信息", "value": "签到失败"}]
        return False
    else:
        try:
          data = req.json()["mission"]
        # 防止查询签到失败但已签到导致无法get到json数据
        except Exception as e:
          data = req.text
          msg += [
              {"name": "签到信息", "value": "今日已签到"},
              {"name": "今日获取积分", "value": data[1:-1]}
          ]
          return True
    msg += [
        {"name": "签到信息", "value": "签到成功"},
        {"name": "今日获取积分", "value": credit},
    ]
    return True

def logout(b2_token):
    url = "https://yuri.website/wp-json/b2/v1/loginOut"
    headers = {
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "authorization": 'Bearer ' + b2_token
    }
    req = SESSION.get(url, headers=headers)
    if req.status_code != 200:
        print("退出登录失败")
    else:
        print("退出登录成功")

# %%
def main():
    b2_token = login()
    sleep(2)
    if b2_token != "":
        if check_user_info(b2_token):
            if query_credit(b2_token):
                check_in(b2_token)
        logout(b2_token)
    global msg
    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == '__main__':
    print(" Yurifans 签到开始 ".center(60, "="))
    print(main())
    print(" Yurifans 签到结束 ".center(60, "="), "\n")
