#!/usr/bin/env python3
import sys
print("===== Bot starting (双功能完整版-命令改为sfz) =====")

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

# ============================================================
# ⚠️ 必填项：请将下方 "你的真实..." 替换为真实数据
# ============================================================
BOT_TOKEN = "5849383582:AAF7VKPb6rzyv0Xk5AL2YypQxunktRaTJHw"

BASE_COOKIES = {
    "cna": "REPLACE_CNA_HERE",
    "JSESSIONID": "REPLACE_JSESSIONID_HERE",
    "SESSION": "REPLACE_SESSION_HERE",
    "SERVERID": "REPLACE_SERVERID_HERE",
}
ZWFW_TOKEN = "REPLACE_ZWFW_TOKEN_HERE"

FIXED_NAME = "刘德华"
SAVE_FOLDER = "temp_files"
RETRY_TIMES = 5

# ========== 查询功能（保持不变） ==========
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
    # 与之前完全一致，省略中间代码（保持完整）
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

# ========== 生成功能（含去白底） ==========
def remove_white_background(img, threshold=240):
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    data = img.getdata()
    new_data = []
    for item in data:
        r, g, b, a = item
        if r > threshold and g > threshold and b > threshold and a != 0:
            new_data.append((r, g, b, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    return img

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
        raise ValueError("身份证号码格式不正确")
    birth_date = id_number[6:14]
    gender = '女' if int(id_number[-2]) % 2 == 0 else '男'

    issuing_authority_map = load_issuing_authority_map('fonts/签发机关.txt')
    issuing_authority = get_issuing_authority(id_number, issuing_authority_map)

    template = Image.open('fonts/empty.png').convert("RGBA")
    name_font = ImageFont.truetype('fonts/hei.ttf', 72)
    other_font = ImageFont.truetype('fonts/hei.ttf', 64)
    birth_font = ImageFont.truetype('fonts/fzhei.ttf', 60)
    id_font = ImageFont.truetype('fonts/ocrb10bt.ttf', 90)

    draw = ImageDraw.Draw(template)
    draw.text((630, 690), name, font=name_font, fill='black')
    draw.text((630, 840), gender, font=other_font, fill='black')
    draw.text((1030, 840), nation, font=other_font, fill='black')
    draw.text((630, 975), birth_date[:4], font=birth_font, fill='black')
    draw.text((950, 975), birth_date[4:6], font=birth_font, fill='black')
    draw.text((1150, 975), birth_date[6:], font=birth_font, fill='black')

    y = 1115
    for line in format_address(address):
        draw.text((630, y), line, font=other_font, fill='black')
        y += 85

    draw.text((900, 1475), id_number, font=id_font, fill='black')
    draw.text((1050, 2750), issuing_authority, font=other_font, fill='black')
    draw.text((1050, 2895), expiration_date, font=other_font, fill='black')

    photo = Image.open(user_photo_path).convert("RGBA")
    photo = remove_white_background(photo, threshold=240)
    photo = photo.resize((500, 670))
    template.paste(photo, (1500, 670), mask=photo)

    img_bytes = io.BytesIO()
    template.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_img:
        tmp_img_path = tmp_img.name
        template.save(tmp_img_path, format='PNG')

    pdf_bytes = io.BytesIO()
    c = canvas.Canvas(pdf_bytes, pagesize=A4)
    w, h = template.size
    scale = min(A4[0]/w, A4[1]/h)
    c.drawImage(tmp_img_path, (A4[0]-w*scale)/2, (A4[1]-h*scale)/2, w*scale, h*scale)
    c.save()
    pdf_bytes.seek(0)
    os.remove(tmp_img_path)

    return img_bytes, pdf_bytes

# ========== Telegram 命令（已修改命令为 /sfz） ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 可用命令：\n"
        "/hainansf +空格+身份证号 → 查询海南头（PDF）\n"
        "/sfz → 生成加工身份证图片和PDF\n"   # 修改了提示
        "/cancel → 取消当前操作"
    )

async def hainansf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 不变
    args = context.args
    if not args:
        await update.message.reply_text("❌ 格式错误\n正确格式：/hainansf <身份证号>")
        return
    id_card = args[0].strip()
    if len(id_card) != 18:
        await update.message.reply_text("❌ 身份证号必须为18位")
        return
    await update.message.reply_text("⏳ 正在查询海南系统...")
    loop = asyncio.get_event_loop()
    success, result = await loop.run_in_executor(None, query_id_card_sync, id_card)
    if success:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=io.BytesIO(result),
            filename=f"{id_card}.pdf",
            caption="✅ 查询成功"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ 查询失败：{result}"
        )

NAME, ID_NUMBER, NATION, ADDRESS, EXPIRY, PHOTO = range(6)

async def sfz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):   # 改名
    await update.message.reply_text("📝 开始生成身份证，请输入姓名：")
    return NAME

async def genid_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text("请输入18位身份证号：")
    return ID_NUMBER

async def genid_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_card = update.message.text.strip().upper()
    if len(id_card) != 18 or not (id_card[:17].isdigit() and id_card[-1] in '0123456789X'):
        await update.message.reply_text("格式错误，重新输入：")
        return ID_NUMBER
    context.user_data['id_number'] = id_card
    await update.message.reply_text("请输入民族：")
    return NATION

async def genid_nation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nation'] = update.message.text.strip()
    await update.message.reply_text("请输入地址：")
    return ADDRESS

async def genid_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text.strip()
    await update.message.reply_text("请输入有效期（如 2020.01.01-2030.01.01）：")
    return EXPIRY

async def genid_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['expiry'] = update.message.text.strip()
    await update.message.reply_text("请发送一张本人照片：")
    return PHOTO

async def genid_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("请发送图片。")
        return PHOTO
    photo = update.message.photo[-1]
    file = await photo.get_file()
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        photo_path = tmp.name

    name = context.user_data.get('name')
    id_number = context.user_data.get('id_number')
    nation = context.user_data.get('nation')
    address = context.user_data.get('address')
    expiry = context.user_data.get('expiry')
    if not all([name, id_number, nation, address, expiry]):
        await update.message.reply_text("信息不完整，请重新 /sfz")
        return ConversationHandler.END

    await update.message.reply_text("⏳ 生成中...")
    loop = asyncio.get_event_loop()
    try:
        img_bytes, pdf_bytes = await loop.run_in_executor(
            None, generate_id_card_sync, name, id_number, nation, address, expiry, photo_path
        )
        await update.message.reply_photo(photo=img_bytes, caption=f"✅ {name} 的身份证")
        await update.message.reply_document(document=pdf_bytes, filename=f"{name}_身份证.pdf")
    except Exception as e:
        await update.message.reply_text(f"❌ 失败：{e}")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)
        context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("已取消")
    context.user_data.clear()
    return ConversationHandler.END

# ========== 主程序 ==========
async def main():
    RUN_DURATION_SECONDS = 350 * 60
    start_time = asyncio.get_event_loop().time()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('hainansf', hainansf))
    app.add_handler(CommandHandler('cancel', cancel))

    conv = ConversationHandler(
        entry_points=[CommandHandler('sfz', sfz_start)],   # 修改入口命令为 sfz
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
    app.add_handler(conv)

    print("🤖 机器人已启动（命令：/sfz）")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed >= RUN_DURATION_SECONDS:
            print("🕒 运行5小时50分，自动退出")
            break
        await asyncio.sleep(60)

    await app.updater.stop()
    await app.stop()
    await app.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
