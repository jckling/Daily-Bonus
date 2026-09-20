# -*- coding: utf-8 -*-
# @File     : message.py
# @Time     : 2021/10/17 19:24
# @Author   : Jckling

import asyncio
import os
import sys
import time

from datetime import datetime, timedelta, timezone
from checkin import bilibili, netease, pica, uma, v2ex, yamibo, yurifans
from telegram import Bot

# info
TG_USER_ID = os.environ.get("TG_USER_ID")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")


def run_module(main, attempts=3, delay=10):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return main()
        except Exception as e:
            last_error = e
            if attempt < attempts:
                time.sleep(delay)
    return f"模块异常（重试 {attempts} 次后仍失败）：{last_error}"


def send_message(content, attempts=3, delay=15):
    bot = Bot(token=TG_BOT_TOKEN)
    for attempt in range(1, attempts + 1):
        try:
            asyncio.run(bot.send_message(chat_id=TG_USER_ID, text=content))
            return True
        except Exception as e:
            if attempt < attempts:
                time.sleep(delay)
            else:
                print(f"Telegram 发送失败：{e}")
    return False


if __name__ == "__main__":
    start_time = time.time()
    utc_time = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    content_lst = []

    if os.environ.get("UMA_COOKIES"):
        content_lst.append(f"「賽馬娘每日簽到」\n{run_module(uma.main)}")
    if os.environ.get("YAMIBO_USERNAME") and os.environ.get("YAMIBO_PASSWORD"):
        content_lst.append(f"「Yamibo」\n{run_module(yamibo.main)}")
    if os.environ.get("YURIFANS_EMAIL") and os.environ.get("YURIFANS_PASSWORD"):
        content_lst.append(f"「Yurifans」\n{run_module(yurifans.main)}")
    if os.environ.get("V2EX_COOKIES"):
        content_lst.append(f"「V2EX」\n{run_module(v2ex.main)}")
    if os.environ.get("BILIBILI_COOKIES"):
        content_lst.append(f"「Bilibili」\n{run_module(bilibili.main)}")
    if os.environ.get("PICA_USERNAME") and os.environ.get("PICA_PASSWORD"):
        content_lst.append(f"「哔咔漫画」\n{run_module(pica.main)}")
    if os.environ.get("NETEASE_MUSIC_COOKIES"):
        content_lst.append(f"「网易云音乐」\n{run_module(netease.main)}")

    content_lst.append(
        f"开始时间: {utc_time}\n" f"任务用时: {int(time.time() - start_time)} 秒\n"
    )
    content = "\n————————————\n\n".join(content_lst)

    print(content)

    if TG_BOT_TOKEN:
        if not send_message(content):
            sys.exit(1)
