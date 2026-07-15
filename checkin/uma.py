# -*- coding: utf-8 -*-
# @File     : uma.py
# @Time     : 2026/07/14 14:30
# @Author   : Jckling

import hashlib
import os
import random
import string
import time
from datetime import datetime

import requests

# cookies
COOKIES = os.environ.get("UMA_COOKIES")
SESSION = requests.Session()
msg = []

# API constants
ACTIVITY_GROUP_ID = "1755595320481626"
ACTIVITY_ID = "10000244"
DRAW_ACTIVITY_ID = "10000385"
APP_ID = "6829"
APPKEY = "7200bfa761c94eae9ceb168bf4b129d0"
SECRET = "+RIq/MaHJf9h23eOdjyXB6lkXL0LjcTGuPiNRyTtZX4="

BASE_URL = "https://l11-activity-web-hk.komoejoy.com"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
    "cookie": COOKIES or "",
    "origin": "https://uma.komoejoy.com",
    "referer": "https://uma.komoejoy.com/",
    "sec-ch-ua": '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
}


def generate_nonce():
    """Generate nonce: timestamp + 10 random alphanumeric chars."""
    ts = int(time.time() * 1000)
    rand_str = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    return f"{ts}{rand_str}"


def sign_params(params):
    """Sign request params using MD5.

    Algorithm (from app.js):
    1. Sort params by key
    2. Build key=value pairs joined by &
    3. Append &secret=<SECRET>
    4. MD5 hash
    """
    sorted_keys = sorted(params.keys())
    pairs = []
    for k in sorted_keys:
        v = params[k]
        if v or v == 0:
            pairs.append(f"{k}={v}")
    query_str = "&".join(pairs)
    sign_str = f"{query_str}&secret={SECRET}"
    return hashlib.md5(sign_str.encode()).hexdigest()


def build_params(extra=None):
    """Build common params with nonce, ts, appkey and sign."""
    ts = int(time.time() * 1000)
    nonce = generate_nonce()
    params = {
        "activity_group_id": ACTIVITY_GROUP_ID,
        "activity_id": ACTIVITY_ID,
        "lang": "zh",
        "app_id": APP_ID,
        "nonce": nonce,
        "ts": ts,
        "appkey": APPKEY,
    }
    if extra:
        params.update(extra)
    params["sign"] = sign_params(params)
    return params


def get_status():
    """Query check-in status. data=0 means not signed, data=1 means already signed."""
    url = f"{BASE_URL}/activity/sign/v2/status"
    params = build_params()
    r = SESSION.get(url, headers=HEADERS, params=params)
    obj = r.json()
    if obj.get("code") == 0:
        return obj.get("data", -1)
    return -1


def check_in():
    """Execute daily check-in via POST to /activity/sign/v2/in."""
    url = f"{BASE_URL}/activity/sign/v2/in"
    params = build_params()
    r = SESSION.post(
        url,
        headers={**HEADERS, "content-type": "application/x-www-form-urlencoded;charset=UTF-8"},
        data=params,
    )
    return r.json()


def get_draw_assert():
    """Query point balance via draw_assert API.

    Returns dict with total, used, available, expiring or None on failure.
    """
    url = f"{BASE_URL}/activity/uma/sign/draw_assert"
    params = build_params({"activity_id": DRAW_ACTIVITY_ID})
    r = SESSION.get(url, headers=HEADERS, params=params)
    obj = r.json()
    if obj.get("code") == 0:
        return obj.get("data")
    return None


def get_config():
    """Query sign-in config for reward schedule.

    Returns dict with daily_sign_prize_list and total_sign_prize_list, or None on failure.
    """
    url = f"{BASE_URL}/activity/uma/sign/config"
    params = build_params()
    r = SESSION.get(url, headers=HEADERS, params=params)
    obj = r.json()
    if obj.get("code") == 0:
        return obj.get("data")
    return None


def get_today_reward(sign_count=None):
    """Get today's reward info from config.

    Uses sign_count (monthly sign-in count) as the key to look up rewards
    from the config's daily_sign_prize_list. If sign_count is not provided,
    falls back to the day of month.

    Returns (daily_reward_str, milestone_reward_str) or (None, None) if config unavailable.
    """
    config = get_config()
    if not config:
        return None, None

    today_key = str(sign_count) if sign_count else str(datetime.now().day)
    daily_list = config.get("daily_sign_prize_list", {})
    total_list = config.get("total_sign_prize_list", {})

    daily = daily_list.get(today_key, {})
    daily_str = None
    if daily:
        name = daily.get("prize_name", "").strip()
        num = daily.get("prize_num", 0)
        point = daily.get("add_point", 0)
        daily_str = f"{name} x{num} + {point} 积分"

    milestone = total_list.get(today_key, {})
    milestone_str = None
    if milestone:
        point = milestone.get("add_point", 0)
        name = (milestone.get("prize_name") or "").strip()
        num = milestone.get("prize_num", 0)
        if name:
            milestone_str = f"{name} x{num} + {point} 积分"
        elif point:
            milestone_str = f"+{point} 积分"

    return daily_str, milestone_str


def get_record():
    """Query sign-in records for the current month."""
    now = time.time()
    # Current month start (1st day, 00:00:00 local time)
    month_start = int(time.mktime(time.strptime(
        time.strftime("%Y-%m-01 00:00:00"), "%Y-%m-%d %H:%M:%S"
    )) * 1000)
    # Next month start - 1ms
    next_month = time.strftime("%Y-%m-01 00:00:00", time.localtime(now + 86400 * 32))
    month_end = int(time.mktime(time.strptime(next_month, "%Y-%m-%d %H:%M:%S")) * 1000) - 1

    url = f"{BASE_URL}/activity/sign/v2/record"
    params = build_params({
        "start_time": str(month_start),
        "end_time": str(month_end),
        "page_num": "1",
        "page_size": "31",
    })
    r = SESSION.get(url, headers=HEADERS, params=params)
    obj = r.json()
    if obj.get("code") == 0:
        data = obj.get("data", {})
        total = data.get("total", 0)
        records = data.get("data", [])
        latest_time = records[-1].get("signDateTimeString", "") if records else ""
        return total, latest_time
    return 0, ""


def main():
    global msg
    if not COOKIES:
        return "No UMA_COOKIES set"

    # Check status first
    status = get_status()
    if status == 1:
        msg.append({"name": "签到信息", "value": "今日已签到"})
        total, sign_time = get_record()
        daily, milestone = get_today_reward(total)
        if daily:
            msg.append({"name": "今日奖励", "value": daily})
        if milestone:
            msg.append({"name": "累计签到奖励", "value": milestone})
        if total > 0:
            sign_str = f"已签到 {total} 天"
            if sign_time:
                sign_str += f"（{sign_time}）"
            msg.append({"name": "本月签到", "value": sign_str})
    elif status == 0:
        result = check_in()
        if result.get("code") == 0:
            msg.append({"name": "签到信息", "value": "签到成功"})
            total, sign_time = get_record()
            daily, milestone = get_today_reward(total)
            if daily:
                msg.append({"name": "今日奖励", "value": daily})
            if milestone:
                msg.append({"name": "累计签到奖励", "value": milestone})
            if total > 0:
                sign_str = f"已签到 {total} 天"
                if sign_time:
                    sign_str += f"（{sign_time}）"
                msg.append({"name": "本月签到", "value": sign_str})
        else:
            msg.append({"name": "签到信息", "value": f'签到失败: {result.get("message", "unknown")}'})
    else:
        msg.append({"name": "签到信息", "value": "查询签到状态失败，Cookie 可能已失效"})

    # Query monthly record (if not already fetched)
    if "本月签到" not in [m["name"] for m in msg]:
        total, sign_time = get_record()
        if total > 0:
            msg.append({"name": "本月签到", "value": f"已签到 {total} 天"})

    # Query point balance
    points = get_draw_assert()
    if points:
        msg.append({"name": "积分余额", "value": f"可用 {points.get('available', '?')}，总计 {points.get('total', '?')}"})

    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == "__main__":
    print(" Uma 签到开始 ".center(60, "="))
    print(main())
    print(" Uma 签到结束 ".center(60, "="), "\n")
