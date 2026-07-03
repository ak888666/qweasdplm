#!/usr/bin/env python3
import sys
print("===== Bot starting (海南查询 + 身份证生成) =====")

import asyncio
import io
import os
import time
import json
import tempfile
import requests
import urllib3
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
#  ⚠️ 所有敏感信息从环境变量读取（不要硬编码）
# ============================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ZWFW_TOKEN = os.environ.get("ZWFW_TOKEN")
BASE_COOKIES = {
    "cna": os.environ.get("CNA"),
    "JSESSIONID": os.environ.get("JSESSIONID"),
    "SESSION": os.environ.get("SESSION"),
    "SERVERID": os.environ.get("SERVERID"),
}

# 检查环境变量是否齐全
missing = []
if not BOT_TOKEN:
    missing.append("BOT_TOKEN")
if not ZWFW_TOKEN:
    missing.append("ZWFW_TOKEN")
for key, value in BASE_COOKIES.items():
    if not value:
        missing.append(key)
if missing:
    print("=" * 60)
    print("❌ 环境变量缺失，请设置以下变量：")
    for m in missing:
        print(f"  - {m}")
    print("=" * 60)
    sys.exit(1)

# 固定参数
FIXED_NAME = "刘德华"
SAVE_FOLDER = "temp_files"
RETRY_TIMES = 5

# ============================================================================
#  查询功能（来自原 hainansf）
# ============================================================================
HEADERS1 = {
    "Host": "zwfw.dn.haikou.gov.cn",
    "Connection": "keep-alive",
    "sec-ch-ua-platform": "\"Android\"",
    "zwfw-token": ZWFW_TOKEN,
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; MEIZU 21 Build/UKQ1.230917.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/141.0.7390.97 Mobile Safari/537.36 AgentWeb/5.0.0  yssApp",
    "sec-ch-ua": "\"Android WebView\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
    "content-type": "application/json",
    "sec-ch-ua-mobile": "?1",
    "Accept": "*/*",
    "Origin": "https://zwfw.dn.haikou.gov.cn",
    "X-Requested-With": "com.hanweb.hnzwfw.android.activity",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://zwfw.dn.haikou.gov.cn/portal_h5/wsbl?id=1047370300041120912&step=B&certifyId=undefined",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}

HEADERS2 = {
    "Host": "zwfw.dn.haikou.gov.cn",
    "Connection": "keep-alive",
    "sec-ch-ua-platform": "\"Android\"",
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; MEIZU 21 Build/UKQ1.230917.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/141.0.7390.97 Mobile Safari/537.36 AgentWeb/5.0.0  yssApp",
    "sec-ch-ua": "\"Android WebView\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
    "sec-ch-ua-mobile": "?1",
    "Accept": "*/*",
    "X-Requested-With": "com.hanweb.hnzwfw.android.activity",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://zwfw.dn.haikou.gov.cn/portal_h5/wsbl?id=1047370300041120912&step=B&certifyId=undefined",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}

def query_id_card_sync(id_card):
    id_card = id_card.strip().upper()
    if len(id_card) != 18:
        return False, "身份证号必须为18位"
    if not id_card[:17].isdigit():
        return False, "前17位必须为数字"
    if id_card[17] not in '0123456789X':
        return False, "最后一位必须是数字或X"

    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)

    session = requests.Session()
    session.cookies.update(BASE_COOKIES)
    session.verify = False

    url1 = "https://zwfw.dn.haikou.gov.cn/rest/materialshare/canShareMaterial"
    data = {
        "itemMaterialId": "1498591712970792960",
        "materialCode": "1173207393439670272",
        "materialName": "委托书原件及委托代理人的身份证明",
        "interfaceParam": "ztmc,zzbh,dzzz_name,cardid,dzzz_type",
        "interfaceParamName": "身份证",
        "canShare": False,
        "isSignature": "N",
        "appInterfaceId": "136",
        "param": {
            "ztmc": FIXED_NAME,
            "zzbh": "",
            "dzzz_name": "随便起个名",
            "cardid": id_card,
            "dzzz_type": "1"
        },
        "itemId": "1047370300041120912",
        "userId": "1547878749006024704"
    }

    for attempt in range(RETRY_TIMES):
        try:
            res1 = session.post(url1, headers=HEADERS1, json=data, timeout=30)
            result1 = res1.json()
        except Exception as e:
            print(f"[{attempt+1}/{RETRY_TIMES}] 请求异常: {e}")
            time.sleep(2)
            continue

        print(f"[{attempt+1}/{RETRY_TIMES}] 服务端返回: {json.dumps(result1, ensure_ascii=False, indent=2)}")

        if result1.get("code") == "1":
            try:
                attachment_id = result1["resultDatas"]["result"]["resultDatas"]["attachmentList"][0]["id"]
                url2 = f"https://zwfw.dn.haikou.gov.cn/rest/attachment/{attachment_id}"
                res2 = session.get(url2, headers=HEADERS2, timeout=30)
                if res2.status_code == 200:
                    return True, res2.content
                else:
                    return False, f"下载附件失败，HTTP {res2.status_code}"
            except (KeyError, IndexError, AttributeError) as e:
                return False, f"解析下载数据失败: {e}, 返回内容: {result1}"
        else:
            msg = result1.get('message', '未知错误')
            print(f"[{attempt+1}/{RETRY_TIMES}] 查询失败: {msg}")
            time.sleep(2)

    return False, f"连续 {RETRY_TIMES} 次查询均失败，请检查 Cookie/Token 是否有效"

# ============================================================================
#  身份证生成功能（来自板子.py，改造为返回 BytesIO）
# ============================================================================
def load_issuing_authority_map(file_path):
    issuing_authority_map = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line:
                area_code, authority = line.split(':')
                issuing_authority_map[area_code] = authority
    return issuing_authority_map

def get_issuing_authority(id_number, issuing_authority_map):
    area_code = id_number[:6]
    return issuing_authority_map.get(area_code, "未知签发机关")

def format_address(address, max_chars_per_line=11):
    lines = []
    for i in range(0, len(address), max_chars_per_line):
        lines.append(address[i:i + max_chars_per_line])
    return lines

def generate_id_card_sync(name, id_number, nation, address, expiration_date, user_photo_path):
    if len(id_number) < 18:
        raise ValueError("身份证号码格式不正确，必须至少18位。")

    birth_date = id_number[6:14]
    gender_code = int(id_number[-2])  # 倒数第二位，即使最后一位是X也不影响
    gender = '女' if gender_code % 2 == 0 else '男'

    issuing_authority_map = load_issuing_authority_map('fonts/签发机关.txt')
    issuing_authority = get_issuing_authority(id_number, issuing_authority_map)
    print(f"自动识别签发机关: {issuing_authority}")

    id_card_template = Image.open('fonts/empty.png').convert("RGBA")

    name_font = ImageFont.truetype('fonts/hei.ttf', 72)
    other_font = ImageFont.truetype('fonts/hei.ttf', 64)
    birth_date_font = ImageFont.truetype('fonts/fzhei.ttf', 60)
    id_font = ImageFont.truetype('fonts/ocrb10bt.ttf', 90)

    draw = ImageDraw.Draw(id_card_template)
    draw.text((630, 690), name, font=name_font, fill='black')
    draw.text((630, 840), gender, font=other_font, fill='black')
    draw.text((1030, 840), nation, font=other_font, fill='black')
    draw.text((630, 975), birth_date[:4], font=birth_date_font, fill='black')
    draw.text((950, 975), birth_date[4:6], font=birth_date_font, fill='black')
    draw.text((1150, 975), birth_date[6:], font=birth_date_font, fill='black')

    address_lines = format_address(address)
    y_position = 1115
    for line in address_lines:
        draw.text((630, y_position), line, fill=(0, 0, 0), font=other_font)
        y_position += 85

    draw.text((900, 1475), id_number, fill=(0, 0, 0), font=id_font)
    draw.text((1050, 2750), issuing_authority, fill=(0, 0, 0), font=other_font)
    draw.text((1050, 2895), expiration_date, fill=(0, 0, 0), font=other_font)

    user_photo = Image.open(user_photo_path).convert("RGBA")
    user_photo_resized = user_photo.resize((500, 670))
    id_card_template.paste(user_photo_resized, (1500, 670), mask=user_photo_resized)

    # 保存图片到内存
    img_bytes = io.BytesIO()
    id_card_template.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    # 生成 PDF 到内存
    pdf_bytes = io.BytesIO()
    c = canvas.Canvas(pdf_bytes, pagesize=A4)
    img_width, img_height = id_card_template.size
    scale = min(A4[0] / img_width, A4[1] / img_height)
    new_width = img_width * scale
    new_height = img_height * scale
    x = (A4[0] - new_width) / 2
    y = (A4[1] - new_height) / 2
    # 需要将图片保存为临时文件供 reportlab 读取，因为 reportlab 不支持直接从 BytesIO 读取
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp_name = tmp.name
        id_card_template.save(tmp_name, format='PNG')
    c.drawImage(tmp_name, x, y, width=new_width, height=new_height)
    c.save()
    os.remove(tmp_name)
    pdf_bytes.seek(0)

    return img_bytes, pdf_bytes

# ============================================================================
#  Telegram 命令处理
# ============================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 可用命令：\n"
        "/hainansf <身份证号> → 查询海南委托书（PDF）\n"
        "/genid → 生成身份证图片和PDF（交互式）\n"
        "/cancel → 取消当前操作"
    )

# ----- 查询功能 -----
async def hainansf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ 格式错误\n正确格式：/hainansf <身份证号>"
        )
        return
    id_card = args[0].strip()
    if len(id_card) != 18:
        await update.message.reply_text("❌ 身份证号必须为18位")
        return
    await update.message.reply_text("⏳ 正在查询海南系统，请稍候...")
    loop = asyncio.get_event_loop()
    success, result = await loop.run_in_executor(None, query_id_card_sync, id_card)
    if success:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=io.BytesIO(result),
            filename=f"{id_card}.pdf",
            caption="✅ 查询成功，附件如下："
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ 查询失败：{result}"
        )

# ----- 生成身份证（对话）-----
# 定义状态
NAME, ID_NUMBER, NATION, ADDRESS, EXPIRY, PHOTO = range(6)

async def genid_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 开始生成身份证，请按提示输入信息。\n输入 /cancel 可取消。")
    await update.message.reply_text("请输入姓名：")
    return NAME

async def genid_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text("请输入18位身份证号：")
    return ID_NUMBER

async def genid_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_card = update.message.text.strip().upper()
    if len(id_card) != 18 or not (id_card[:17].isdigit() and id_card[-1] in '0123456789X'):
        await update.message.reply_text("格式错误，请重新输入18位身份证号：")
        return ID_NUMBER
    context.user_data['id_number'] = id_card
    await update.message.reply_text("请输入民族（如：汉族）：")
    return NATION

async def genid_nation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nation'] = update.message.text.strip()
    await update.message.reply_text("请输入地址：")
    return ADDRESS

async def genid_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text.strip()
    await update.message.reply_text("请输入有效期（如：2020.01.01-2030.01.01）：")
    return EXPIRY

async def genid_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['expiry'] = update.message.text.strip()
    await update.message.reply_text("请发送一张本人照片（请选择清晰正面照）：")
    return PHOTO

async def genid_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("请发送一张图片（照片）。")
        return PHOTO
    photo = update.message.photo[-1]
    file = await photo.get_file()
    # 下载到临时文件
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        photo_path = tmp.name

    name = context.user_data.get('name')
    id_number = context.user_data.get('id_number')
    nation = context.user_data.get('nation')
    address = context.user_data.get('address')
    expiry = context.user_data.get('expiry')

    if not all([name, id_number, nation, address, expiry]):
        await update.message.reply_text("❌ 信息不完整，请重新开始 /genid")
        return ConversationHandler.END

    await update.message.reply_text("⏳ 正在生成身份证，请稍候...")

    loop = asyncio.get_event_loop()
    try:
        img_bytes, pdf_bytes = await loop.run_in_executor(
            None, generate_id_card_sync, name, id_number, nation, address, expiry, photo_path
        )
        # 发送图片
        await update.message.reply_photo(
            photo=img_bytes,
            caption=f"✅ 生成成功！{name} 的身份证"
        )
        # 发送PDF
        await update.message.reply_document(
            document=pdf_bytes,
            filename=f"{name}_身份证.pdf"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ 生成失败：{str(e)}")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)
        # 清除用户数据
        context.user_data.clear()

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("已取消当前操作。")
    context.user_data.clear()
    return ConversationHandler.END

# ============================================================================
#  主程序（带6小时自动退出）
# ============================================================================
async def main():
    RUN_DURATION_SECONDS = 350 * 60
    start_time = asyncio.get_event_loop().time()

    app = Application.builder().token(BOT_TOKEN).build()

    # 普通命令
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('hainansf', hainansf))

    # 生成身份证的对话
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('genid', genid_start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, genid_name)],
            ID_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, genid_id)],
            NATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, genid_nation)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, genid_address)],
            EXPIRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, genid_expiry)],
            PHOTO: [MessageHandler(filters.PHOTO, genid_photo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    app.add_handler(conv_handler)

    print("🤖 机器人已启动，正在轮询...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed >= RUN_DURATION_SECONDS:
            print("🕒 已运行 5小时50分，主动退出，等待下一次 Actions 触发...")
            break
        await asyncio.sleep(60)

    await app.updater.stop()
    await app.stop()
    await app.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
