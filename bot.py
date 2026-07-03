# bot.py
import asyncio
import os
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 导入封装好的查询函数
from query_helper import query_id_card_async

# 从环境变量读取 Bot Token
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ 未设置 BOT_TOKEN 环境变量")
    sys.exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 欢迎！发送一个 18 位身份证号码，我将为你查询并返回委托书 PDF。\n"
        "命令：\n/start - 显示帮助"
    )

async def handle_id_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(" ", "")
    if len(text) != 18 or not (text[:17].isdigit() and text[-1] in '0123456789Xx'):
        await update.message.reply_text("❌ 请输入有效的 18 位身份证号（最后一位可为 X）")
        return

    progress_msg = await update.message.reply_text("⏳ 正在查询，请稍候...")

    try:
        success, result_msg = await query_id_card_async(text)
    except Exception as e:
        await progress_msg.edit_text(f"❌ 查询异常: {str(e)}")
        return

    if not success:
        await progress_msg.edit_text(f"❌ {result_msg}")
        return

    # 提取文件路径
    file_path = result_msg.split("文件已保存至: ")[-1].strip()
    if not os.path.exists(file_path):
        await progress_msg.edit_text("❌ 文件生成后丢失，请重试")
        return

    # 发送 PDF
    try:
        with open(file_path, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=f"{text}.pdf",
                caption=f"✅ 身份证 {text[:6]}********{text[-4:]} 的委托书"
            )
        await progress_msg.delete()
    except Exception as e:
        await progress_msg.edit_text(f"❌ 文件发送失败: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# ========== 带 6 小时自动退出的主程序 ==========
async def main():
    # 设置运行时长：5小时50分钟（350分钟），避开 GitHub 6 小时限制
    RUN_DURATION_SECONDS = 350 * 60
    start_time = asyncio.get_event_loop().time()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_id_card))

    print("🤖 机器人已启动，正在轮询...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # 循环检查运行时间
    while True:
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed >= RUN_DURATION_SECONDS:
            print("🕒 已运行 5小时50分，主动退出，等待下一次 Actions 触发...")
            break
        await asyncio.sleep(60)

    # 优雅关闭
    await app.updater.stop()
    await app.stop()
    await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
