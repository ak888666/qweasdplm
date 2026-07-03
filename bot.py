#!/usr/bin/env python3
import sys
print("===== Bot starting (稳定版，plc永不消失) =====")

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

# ====================================================================
# 1. 查询功能（/hainansf）-- 完整保留
# ====================================================================
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

# ====================================================================
# 2. 通用去白底函数
# ====================================================================
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

# ====================================================================
# 3. 生成功能1：/sfz（使用 empty.png 模板）
# ====================================================================
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

# ====================================================================
# 4. 生成功能2：/plc（稳定版，所有资源加载都在 try 中）
# ====================================================================
def load_area_map():
    area_map = {}
    file_path = 'plc/地区.txt'
    if not os.path.exists(file_path):
        return area_map
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(',', 1)
                if len(parts) == 2:
                    code, name = parts[0].strip(), parts[1].strip()
                    area_map[code] = name
    except:
        pass
    return area_map

AREA_MAP = load_area_map()

def get_address_from_idcard(id_card):
    prefix = id_card[:6]
    return AREA_MAP.get(prefix, None)

def generate_plc_sync(name, id_card, address, avatar_path):
    # 所有资源加载放在 try 中，任何失败直接抛出异常（由上层捕获）
    if len(id_card) != 18:
        raise ValueError("身份证号必须为18位")
    gender = "男" if int(id_card[16]) % 2 == 1 else "女"

    # 检查 plc/ 目录下的文件是否存在
    if not os.path.exists('plc/mb.jpg'):
        raise FileNotFoundError("PLC模板文件 mb.jpg 不存在")
    if not os.path.exists('plc/10.ttf'):
        raise FileNotFoundError("PLC字体文件 10.ttf 不存在")

    template = Image.open('plc/mb.jpg').convert("RGBA")
    avatar = Image.open(avatar_path).convert("RGBA")
    avatar = remove_white_background(avatar, threshold=240)
    avatar = avatar.resize((416, 500))
    template.paste(avatar, (26, 333), mask=avatar)

    draw = ImageDraw.Draw(template)
    font = ImageFont.truetype('plc/10.ttf', 55)

    year = id_card[6:10]
    month = id_card[10:12]
    day = id_card[12:14]
    birth_str = year + "年" + month + "月" + day + "日"

    draw.text((598, 314), name, font=font, fill=(0, 0, 0))
    draw.text((598, 398), gender, font=font, fill=(0, 0, 0))
    draw.text((474, 641), id_card, font=font, fill=(0, 0, 0))
    draw.text((718, 482), birth_str, font=font, fill=(0, 0, 0))

    address_lines = [address[i:i+11] for i in range(0, len(address), 11)]
    for i, line in enumerate(address_lines):
        draw.text((473, 782 + i * 60), line, font=font, fill=(0, 0, 0))

    img_bytes = io.BytesIO()
    template.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    pdf_bytes = io.BytesIO()
    c = canvas.Canvas(pdf_bytes, pagesize=A4)
    w, h = template.size
    scale = min(A4[0]/w, A4[1]/h)
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp_path = tmp.name
        template.save(tmp_path, format='PNG')
    c.drawImage(tmp_path, (A4[0]-w*scale)/2, (A4[1]-h*scale)/2, w*scale, h*scale)
    c.save()
    pdf_bytes.seek(0)
    os.remove(tmp_path)

    return img_bytes, pdf_bytes

# ====================================================================
# 5. Telegram 命令处理
# ====================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "小宇：\n"
        "/hainansf +空格+身份证号→查询海南大头\n"
        "/sfz → 加工生成身份证\n"
        "/plc → 生成（PLC模板自动匹配地址）\n"
        "/cancel → 取消当前操作"
    )

async def hainansf(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("已取消")
    context.user_data.clear()
    return ConversationHandler.END

# ===== /sfz 对话 =====
SFZ_NAME, SFZ_ID, SFZ_NATION, SFZ_ADDR, SFZ_EXPIRY, SFZ_PHOTO = range(6)

async def sfz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 开始生成身份证（标准模板），请输入姓名：")
    return SFZ_NAME

async def sfz_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text("请输入18位身份证号：")
    return SFZ_ID

async def sfz_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_card = update.message.text.strip().upper()
    if len(id_card) != 18 or not (id_card[:17].isdigit() and id_card[-1] in '0123456789X'):
        await update.message.reply_text("格式错误，重新输入：")
        return SFZ_ID
    context.user_data['id_number'] = id_card
    await update.message.reply_text("请输入民族：")
    return SFZ_NATION

async def sfz_nation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nation'] = update.message.text.strip()
    await update.message.reply_text("请输入地址：")
    return SFZ_ADDR

async def sfz_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text.strip()
    await update.message.reply_text("请输入有效期（如 2020.01.01-2030.01.01）：")
    return SFZ_EXPIRY

async def sfz_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['expiry'] = update.message.text.strip()
    await update.message.reply_text("请发送一张本人照片：")
    return SFZ_PHOTO

async def sfz_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("请发送图片。")
        return SFZ_PHOTO
    photo = update.message.photo[-1]
    file = await photo.get_file()
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        photo_path = tmp.name

    data = context.user_data
    if not all(k in data for k in ['name','id_number','nation','address','expiry']):
        await update.message.reply_text("信息不完整，请重新 /sfz")
        return ConversationHandler.END

    await update.message.reply_text("⏳ 生成中...")
    loop = asyncio.get_event_loop()
    try:
        img, pdf = await loop.run_in_executor(
            None, generate_id_card_sync,
            data['name'], data['id_number'], data['nation'],
            data['address'], data['expiry'], photo_path
        )
        await update.message.reply_photo(photo=img, caption=f"✅ {data['name']} 的身份证")
        await update.message.reply_document(document=pdf, filename=f"{data['name']}_身份证.pdf")
    except Exception as e:
        await update.message.reply_text(f"❌ 失败：{e}")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)
        context.user_data.clear()
    return ConversationHandler.END

# ===== /plc 对话（已加异常保护）=====
PLC_NAME, PLC_ID, PLC_ADDR_MANUAL, PLC_PHOTO = range(10, 14)

async def plc_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 开始生成身份证（PLC模板），请输入姓名：")
    return PLC_NAME

async def plc_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text("请输入18位身份证号：")
    return PLC_ID

async def plc_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_card = update.message.text.strip().upper()
    if len(id_card) != 18 or not (id_card[:17].isdigit() and id_card[-1] in '0123456789X'):
        await update.message.reply_text("格式错误，重新输入：")
        return PLC_ID
    context.user_data['id_number'] = id_card

    address = get_address_from_idcard(id_card)
    if address:
        context.user_data['address'] = address
        await update.message.reply_text(f"✅ 已自动匹配地址：{address}\n请发送一张本人照片：")
        return PLC_PHOTO
    else:
        # 检查地区文件是否加载成功，若没有数据则提醒
        if not AREA_MAP:
            await update.message.reply_text("⚠️ 地区文件为空或未加载，请手动输入详细地址：")
        else:
            await update.message.reply_text("⚠️ 无法自动匹配地址，请手动输入详细地址：")
        return PLC_ADDR_MANUAL

async def plc_addr_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    if not address:
        await update.message.reply_text("地址不能为空，请重新输入：")
        return PLC_ADDR_MANUAL
    context.user_data['address'] = address
    await update.message.reply_text("请发送一张本人照片：")
    return PLC_PHOTO

async def plc_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("请发送图片。")
        return PLC_PHOTO
    photo = update.message.photo[-1]
    file = await photo.get_file()
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        photo_path = tmp.name

    data = context.user_data
    if not all(k in data for k in ['name','id_number','address']):
        await update.message.reply_text("信息不完整，请重新 /plc")
        return ConversationHandler.END

    await update.message.reply_text("⏳ 生成中...")
    loop = asyncio.get_event_loop()
    try:
        # 尝试执行生成，所有异常在此捕获，不会导致进程崩溃
        img, pdf = await loop.run_in_executor(
            None, generate_plc_sync,
            data['name'], data['id_number'], data['address'], photo_path
        )
        await update.message.reply_photo(photo=img, caption=f"✅ {data['name']} 的身份证（PLC模板）")
        await update.message.reply_document(document=pdf, filename=f"{data['name']}_身份证_PLC.pdf")
    except FileNotFoundError as e:
        await update.message.reply_text(f"❌ 文件缺失：{e}\n请确保 plc/ 目录下有 mb.jpg 和 10.ttf")
    except Exception as e:
        await update.message.reply_text(f"❌ 生成失败：{e}")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)
        context.user_data.clear()
    return ConversationHandler.END

# ====================================================================
# 6. 主程序（带6小时自动退出）
# ====================================================================
async def main():
    # 启动时检查 plc/ 目录文件，给出提示但不退出
    if not os.path.exists('plc/mb.jpg'):
        print("警告: plc/mb.jpg 不存在，/plc 功能可能无法使用")
    if not os.path.exists('plc/10.ttf'):
        print("警告: plc/10.ttf 不存在，/plc 功能可能无法使用")
    if not os.path.exists('plc/地区.txt'):
        print("警告: plc/地区.txt 不存在，/plc 自动匹配地址可能失败")
    else:
        # 检查地区文件是否有内容
        try:
            with open('plc/地区.txt', 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if not first_line:
                    print("警告: plc/地区.txt 文件为空，/plc 自动匹配地址可能失败")
        except:
            pass

    RUN_DURATION_SECONDS = 350 * 60
    start_time = asyncio.get_event_loop().time()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('hainansf', hainansf))
    app.add_handler(CommandHandler('cancel', cancel))

    # 注册 /sfz 对话
    conv_sfz = ConversationHandler(
        entry_points=[CommandHandler('sfz', sfz_start)],
        states={
            SFZ_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, sfz_name)],
            SFZ_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, sfz_id)],
            SFZ_NATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, sfz_nation)],
            SFZ_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, sfz_address)],
            SFZ_EXPIRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, sfz_expiry)],
            SFZ_PHOTO: [MessageHandler(filters.PHOTO, sfz_photo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    app.add_handler(conv_sfz)

    # 注册 /plc 对话（所有异常已在内部捕获）
    conv_plc = ConversationHandler(
        entry_points=[CommandHandler('plc', plc_start)],
        states={
            PLC_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, plc_name)],
            PLC_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, plc_id)],
            PLC_ADDR_MANUAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, plc_addr_manual)],
            PLC_PHOTO: [MessageHandler(filters.PHOTO, plc_photo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    app.add_handler(conv_plc)

    print("🤖 机器人已启动（命令：/hainansf, /sfz, /plc）")
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
