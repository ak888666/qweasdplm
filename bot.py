#!/usr/bin/env python3
import sys
print("===== 极简测试版 (Updater 同步方式) =====")

from telegram.ext import Updater, CommandHandler

# ============================================================
# 只修改这一行：填你的 Bot Token
# ============================================================
BOT_TOKEN = "5849383582:AAF7VKPb6rzyv0Xk5AL2YypQxunktRaTJHw"

def start(update, context):
    update.message.reply_text(
        "👋 测试版命令：\n"
        "/plc → 测试命令（回复一条消息）\n"
        "如果这个命令出现了，说明机器人启动正常。"
    )

def plc_test(update, context):
    update.message.reply_text("✅ /plc 命令已识别！这是测试回复。")

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("plc", plc_test))
    print("🤖 测试机器人已启动，正在轮询...")
    updater.start_polling()
    updater.idle()  # 保持运行，直到按 Ctrl+C

if __name__ == "__main__":
    main()
