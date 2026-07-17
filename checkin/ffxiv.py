# -*- coding: utf-8 -*-
# @File     : ffxiv.py
# @Time     : 2021/03/24 15:43
# @Author   : Jckling

import base64
import json
import os
import re
import time

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from curl_cffi import requests as cffi_requests

# info
USERNAME = os.environ.get("FFXIV_USERNAME")
PASSWORD = os.environ.get("FFXIV_PASSWORD")
msg = []

BASE_URL = "https://sqmallservice.u.sdo.com"
MERCHANT_ID = "1"
SESSION = cffi_requests.Session()

# RSA public key from SDO login page (jsencrypt_helper.js)
PUBLIC_KEY_B64 = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCrLCvPQVj1dYDdtb34bUGrxAYHLDMQdsjbk7+pY/ugKdHKhxQo1E43gt4HMgjFuirvaGfh1NJ2FCX9thillLZlHhkNOUcEQSbpcJycQ9wq7FBtOk7lE0dBBA9t3Zk/qBx2A2xPVvVNf9lNdNDDp2vXhQ549H9hg1s1TPHFEags3QIDAQAB"

LOGIN_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
    "referer": "https://login.u.sdo.com/",
    "sec-ch-ua": "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "script",
    "sec-fetch-mode": "no-cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
}

API_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://qu.sdo.com",
    "qu-deploy-platform": "1",
    "qu-hardware-platform": "3",
    "qu-merchant-id": MERCHANT_ID,
    "qu-software-platform": "1",
    "qu-web-host": "qu.sdo.com",
    "referer": "https://qu.sdo.com/",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
}


def login():
    """Login with username and password via SDO CAS.

    Returns True if login succeeds.
    """
    ts = str(int(time.time() * 1000))
    common_params = {
        "appId": "6666", "areaId": "-1", "serviceUrl": "https://qu.sdo.com/game/1",
        "productVersion": "v5", "frameType": "3", "locale": "zh_CN", "version": "21",
        "tag": "20", "authenSource": "2", "productId": "2", "scene": "login",
        "usage": "aliCode", "bizType": "", "source": "pc", "extendInfo": "{}", "_": ts,
    }

    # Step 1: ssoLogin
    SESSION.get(
        "https://w.cas.sdo.com/authen/ssoLogin.jsonp",
        headers=LOGIN_HEADERS,
        params={**common_params, "callback": "ssoLogin_JSONPMethod"},
        impersonate="chrome",
    )

    # Step 2: getSystemConfig (get bizContext)
    r2 = SESSION.get(
        "https://n2.cas.sdo.com/authen/v2/getSystemConfig.jsonp",
        headers=LOGIN_HEADERS,
        params={**common_params, "callback": "getSystemConfig_JSONPMethod", "scene": "sendSms"},
        impersonate="chrome",
    )
    json_str = r2.text[r2.text.find("(") + 1:r2.text.rfind(")")]
    biz_context = json.loads(json_str)["data"]["bizContext"]
    extend_info = json.dumps({"bizContext": biz_context})

    # Step 3: checkAccountType
    SESSION.get(
        "https://w.cas.sdo.com/authen/checkAccountType.jsonp",
        headers=LOGIN_HEADERS,
        params={**common_params, "callback": "checkAccountType_JSONPMethod", "inputUserId": USERNAME, "extendInfo": extend_info},
        impersonate="chrome",
    )

    # Step 4: staticLogin (RSA encrypt password)
    rsa_key = RSA.import_key(base64.b64decode(PUBLIC_KEY_B64))
    cipher = PKCS1_v1_5.new(rsa_key)
    encrypted_pwd = base64.b64encode(cipher.encrypt(PASSWORD.encode())).decode()

    r4 = SESSION.get(
        "https://w.cas.sdo.com/authen/staticLogin.jsonp",
        headers=LOGIN_HEADERS,
        params={**common_params, "callback": "staticLogin_JSONPMethod", "inputUserId": USERNAME, "password": encrypted_pwd, "isEncrypt": "1", "autoLoginFlag": "0", "extendInfo": extend_info},
        impersonate="chrome",
    )

    global msg
    # Check for captcha
    if "captchaParams" in r4.text and "ticket" not in r4.text:
        msg.append({"name": "登录信息", "value": "登录需要验证码，请稍后重试或手动登录"})
        return False

    ticket_match = re.search(r'"ticket"\s*:\s*"([^"]+)"', r4.text)
    if not ticket_match:
        error_match = re.search(r'"return_message"\s*:\s*"([^"]*)"', r4.text)
        error_msg = error_match.group(1) if error_match else "unknown error"
        msg.append({"name": "登录信息", "value": f"登录失败，{error_msg}"})
        return False

    ticket = ticket_match.group(1)

    # Step 5: Visit qu.sdo.com with ticket to establish session
    SESSION.get(
        f"https://qu.sdo.com/game/1?ticket={ticket}",
        headers={**LOGIN_HEADERS, "origin": "https://qu.sdo.com", "referer": "https://qu.sdo.com/"},
        impersonate="chrome",
    )

    # Step 6: Login at sqmallservice with ticket
    ts2 = str(int(time.time() * 1000))
    r6 = SESSION.get(
        f"{BASE_URL}/api/us/login?ticket={ticket}&_={ts2}",
        headers={**LOGIN_HEADERS, "origin": "https://qu.sdo.com", "referer": "https://qu.sdo.com/"},
        impersonate="chrome",
    )
    obj = r6.json()
    if obj.get("resultCode") == 0:
        nick = obj.get("data", {}).get("sndaAccount", {}).get("nickName", "")
        masked = "█" * len(nick) if nick else "?"
        msg.append({"name": "登录信息", "value": masked})
        return True
    else:
        msg.append({"name": "登录信息", "value": "登录失败，session 建立失败"})
        return False


def get_check_in_status():
    """Get check-in status. Returns True if already signed in today."""
    r = SESSION.get(
        f"{BASE_URL}/api/us/checkIn/getStatus?merchantId={MERCHANT_ID}",
        headers=API_HEADERS,
        impersonate="chrome",
    )
    obj = r.json()

    global msg
    if obj.get("resultCode") == 0:
        data = obj.get("data", {})
        is_check_in = data.get("isCheckIn", 0)
        recent = data.get("recentDetails", [])
        if is_check_in:
            sign_time = recent[0] if recent else ""
            for m in msg:
                if m["name"] == "签到信息":
                    m["value"] = f"签到成功（{sign_time}）" if "签到成功" in m.get("value", "") else f"今日已签到（{sign_time}）"
                    return True
            msg.append({"name": "签到信息", "value": f"今日已签到（{sign_time}）"})
            return True
    return False


def check_in():
    """Perform daily check-in."""
    r = SESSION.put(
        f"{BASE_URL}/api/us/integration/checkIn",
        headers=API_HEADERS,
        data=f"merchantId={MERCHANT_ID}",
        impersonate="chrome",
    )
    obj = r.json()

    global msg
    result_code = obj.get("resultCode", 0)
    result_msg = obj.get("resultMsg", "")

    if result_code == 0:
        data = obj.get("data", {})
        reward = data.get("acquireIntegration", 0)
        msg.append({"name": "签到信息", "value": f"签到成功，获得 {reward} 积分"})
    elif "今日已签到" in result_msg or "重复" in result_msg:
        msg.append({"name": "签到信息", "value": "今日已签到"})
    else:
        msg.append({"name": "签到信息", "value": f"签到失败，{result_msg}"})


def get_balance():
    """Get integral balance."""
    r = SESSION.get(
        f"{BASE_URL}/api/rs/member/integral/balance?merchantId={MERCHANT_ID}",
        headers=API_HEADERS,
        impersonate="chrome",
    )
    obj = r.json()

    global msg
    if obj.get("resultCode") == 0:
        data = obj.get("data", {})
        balance = data.get("balance", 0)
        name = data.get("integralName", "积分")
        msg.append({"name": "积分余额", "value": f"{balance} {name}"})


def main():
    global msg
    if not USERNAME or not PASSWORD:
        return "No FFXIV_USERNAME or FFXIV_PASSWORD set"

    if not login():
        return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])

    already_signed = get_check_in_status()
    if not already_signed:
        check_in()
        get_check_in_status()

    get_balance()

    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == "__main__":
    print(" FF14 签到开始 ".center(60, "="))
    print(main())
    print(" FF14 签到结束 ".center(60, "="), "\n")
