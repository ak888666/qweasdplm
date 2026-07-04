#!/usr/bin/env python3
import sys
print("===== 最小化测试版 (仅 /start 和 /plc) =====")

import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ============================================================
# 只修改这一行：填你的 Bot Token
# ============================================================
BOT_TOKEN = "你的真实BOT_TOKEN"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 测试版命令：\n"
        "/plc → 测试命令（回复一条消息）\n"
        "如果这个命令出现了，说明机器人启动正常。"
    )

async def plc_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ /plc 命令已识别！这是测试回复。")

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('plc', plc_test))
    print("🤖 测试机器人已启动，正在轮询...")
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
