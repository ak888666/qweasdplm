# bot.py
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os

# 导入封装好的查询函数
from query_helper import query_id_card_async

BOT_TOKEN = "5849383582:AAF7VKPb6rzyv0Xk5AL2YypQxunktRaTJHw"

# 临时存储文件路径，用于清理（可选）
TEMPORARY_FILES = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 欢迎！发送一个 18 位身份证号码，我将为你查询并返回委托书 PDF。\n"
        "命令：\n/start - 显示帮助"
    )

async def handle_id_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip().replace(" ", "")
    if len(text) != 18 or not (text[:17].isdigit() and text[-1] in '0123456789Xx'):
        await update.message.reply_text("❌ 请输入有效的 18 位身份证号（最后一位可为 X）")
        return

    # 发送“处理中”提示
    progress_msg = await update.message.reply_text("⏳ 正在查询，请稍候...")

    try:
        # 异步执行查询（会在线程池中运行同步函数）
        success, result_msg = await query_id_card_async(text)
    except Exception as e:
        await progress_msg.edit_text(f"❌ 查询异常: {str(e)}")
        return

    if not success:
        await progress_msg.edit_text(f"❌ {result_msg}")
        return

    # 如果成功，result_msg 格式为 "成功! 文件已保存至: 海南/xxxx.pdf"
    # 提取文件路径
    file_path = result_msg.split("文件已保存至: ")[-1].strip()
    if not os.path.exists(file_path):
        await progress_msg.edit_text("❌ 文件生成后丢失，请重试")
        return

    # 发送 PDF 文件
    try:
        with open(file_path, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=f"{text}.pdf",
                caption=f"✅ 身份证 {text[:6]}********{text[-4:]} 的委托书"
            )
        await progress_msg.delete()  # 删除“处理中”消息
    except Exception as e:
        await progress_msg.edit_text(f"❌ 文件发送失败: {str(e)}")
    finally:
        # 清理临时文件（可选）
        if os.path.exists(file_path):
            os.remove(file_path)

async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    # 处理纯文本消息（只处理 18 位数字/X 内容）
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_id_card))

    print("🤖 机器人已启动，正在轮询...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
