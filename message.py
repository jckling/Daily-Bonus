# -*- coding: utf-8 -*-
# @File     : message.py
# @Time     : 2021/10/17 19:24
# @Author   : Jckling

import asyncio
import os
import time

from datetime import datetime, timedelta, timezone
from checkin import bilibili, pica, uma, v2ex, yamibo, yurifans
from telegram import Bot

# info
TG_USER_ID = os.environ.get("TG_USER_ID")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")

if __name__ == '__main__':
    start_time = time.time()
    utc_time = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    content_lst = []

    if os.environ.get("UMA_COOKIES"):
        content_lst.append(f"「賽馬娘每日簽到」\n{uma.main()}")
    if os.environ.get("YAMIBO_COOKIES"):
        content_lst.append(f"「Yamibo」\n{yamibo.main()}")
    if os.environ.get("YURIFANS_EMAIL") and os.environ.get("YURIFANS_PASSWORD"):
        content_lst.append(f"「Yurifans」\n{yurifans.main()}")
    if os.environ.get("V2EX_COOKIES"):
        content_lst.append(f"「V2EX」\n{v2ex.main()}")
    if os.environ.get("BILIBILI_COOKIES"):
        content_lst.append(f"「Bilibili」\n{bilibili.main()}")
    if os.environ.get("PICA_USERNAME") and os.environ.get("PICA_PASSWORD"):
        content_lst.append(f"「哔咔漫画」\n{pica.main()}")

    content_lst.append(
        f"开始时间: {utc_time}\n"
        f"任务用时: {int(time.time() - start_time)} 秒\n"
    )
    content = "\n————————————\n\n".join(content_lst)

    if TG_BOT_TOKEN:
        bot = Bot(token=TG_BOT_TOKEN)
        asyncio.run(bot.send_message(
            chat_id=TG_USER_ID,
            text=content,
            parse_mode="HTML"
        ))

    print(content)
