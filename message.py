# -*- coding: utf-8 -*-
# @File     : message.py
# @Time     : 2021/10/17 19:24
# @Author   : Jckling

import os

from Bilibili import bilibili_checkin
from Music163 import music_checkin
from V2EX import v2ex_checkin
from Yamibo import yamibo_checkin
from telegram import Bot

# info
TG_USER_ID = os.environ.get("TG_USER_ID")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")

if __name__ == '__main__':
    content = "\n————————————\n\n".join([
        f"「Bilibili」\n{bilibili_checkin.main()}",
        f"「网易云音乐」\n{music_checkin.main()}",
        f"「V2EX」\n{v2ex_checkin.main()}",
        f"「Yamibo」\n{yamibo_checkin.main()}"
    ])

    bot = Bot(token=TG_BOT_TOKEN)
    bot.sendMessage(
        chat_id=TG_USER_ID,
        text=content,
        parse_mode="HTML"
    )
