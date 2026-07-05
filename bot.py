#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
print("===== Bot 四功能完整版 (超级鹰·增强超时) =====")

import os
import time
import json
import io
import tempfile
import re
import base64
import urllib.parse
import hashlib
import requests
import urllib3
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater, CommandHandler, ConversationHandler,
    MessageHandler, Filters, CallbackQueryHandler
)

# ---------- 禁用 SSL 警告 ----------
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
#  ⚠️ Telegram Bot Token
# ============================================================
BOT_TOKEN = "5849383582:AAGSJs4OWCs8pYd9oUFwHbZHpaUBM3CYgXw"

# ============================================================
#  ⚠️ 超级鹰配置（已填好你的信息）
# ============================================================
class Chaojiying_Client:
    def __init__(self, username, password, soft_id):
        self.username = username
        password = password.encode('utf-8')
        self.password = hashlib.md5(password).hexdigest()
        self.soft_id = soft_id
        self.base_params = {
            'user': self.username,
            'pass2': self.password,
            'softid': self.soft_id,
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }

    def PostPic(self, im, codetype):
        params = {
            'codetype': codetype,
        }
        params.update(self.base_params)
        files = {'userfile': ('captcha.jpg', im)}
        r = requests.post('http://upload.chaojiying.net/Upload/Processing.php', 
                          data=params, files=files, headers=self.headers, timeout=30)
        return r.json()

# 你的超级鹰账号信息
CJY_USERNAME = "202607055w661t38"
CJY_PASSWORD = "zxcvbnm369f"
CJY_SOFT_ID = "982408"
CJY_CODETYPE = 1004   # 4位英文数字混合

chaojiying = Chaojiying_Client(CJY_USERNAME, CJY_PASSWORD, CJY_SOFT_ID)

# 测试超级鹰API连通性
try:
    test_resp = requests.get("http://upload.chaojiying.net", timeout=10)
    print(f"[网络测试] 超级鹰API连通性: {test_resp.status_code}")
except Exception as e:
    print(f"[网络测试] 超级鹰API不可达: {e}")

# ============================================================
#  ⚠️ 海南系统配置（如不用可忽略）
# ============================================================
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

# ============================================================
#  gxdlys 网站配置
# ============================================================
GX_BASE_URL = "http://www.gxdlys.com"
GX_PASSWORD = "268428."
GX_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; Build/BP2A.250605.031.A3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.7680.119 Mobile Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Referer": "http://www.gxdlys.com/Wechat/User/Regist",
}
gx_session = requests.Session()

# ============================================================
#  SM4 加密函数（完整）
# ============================================================
SM4_KEY = "CatsPK0WWWRRhjkw"
SboxTable = [
    0xd6, 0x90, 0xe9, 0xfe, 0xcc, 0xe1, 0x3d, 0xb7, 0x16, 0xb6, 0x14, 0xc2, 0x28, 0xfb, 0x2c, 0x05,
    0x2b, 0x67, 0x9a, 0x76, 0x2a, 0xbe, 0x04, 0xc3, 0xaa, 0x44, 0x13, 0x26, 0x49, 0x86, 0x06, 0x99,
    0x9c, 0x42, 0x50, 0xf4, 0x91, 0xef, 0x98, 0x7a, 0x33, 0x54, 0x0b, 0x43, 0xed, 0xcf, 0xac, 0x62,
    0xe4, 0xb3, 0x1c, 0xa9, 0xc9, 0x08, 0xe8, 0x95, 0x80, 0xdf, 0x94, 0xfa, 0x75, 0x8f, 0x3f, 0xa6,
    0x47, 0x07, 0xa7, 0xfc, 0xf3, 0x73, 0x17, 0xba, 0x83, 0x59, 0x3c, 0x19, 0xe6, 0x85, 0x4f, 0xa8,
    0x68, 0x6b, 0x81, 0xb2, 0x71, 0x64, 0xda, 0x8b, 0xf8, 0xeb, 0x0f, 0x4b, 0x70, 0x56, 0x9d, 0x35,
    0x1e, 0x24, 0x0e, 0x5e, 0x63, 0x58, 0xd1, 0xa2, 0x25, 0x22, 0x7c, 0x3b, 0x01, 0x21, 0x78, 0x87,
    0xd4, 0x00, 0x46, 0x57, 0x9f, 0xd3, 0x27, 0x52, 0x4c, 0x36, 0x02, 0xe7, 0xa0, 0xc4, 0xc8, 0x9e,
    0xea, 0xbf, 0x8a, 0xd2, 0x40, 0xc7, 0x38, 0xb5, 0xa3, 0xf7, 0xf2, 0xce, 0xf9, 0x61, 0x15, 0xa1,
    0xe0, 0xae, 0x5d, 0xa4, 0x9b, 0x34, 0x1a, 0x55, 0xad, 0x93, 0x32, 0x30, 0xf5, 0x8c, 0xb1, 0xe3,
    0x1d, 0xf6, 0xe2, 0x2e, 0x82, 0x66, 0xca, 0x60, 0xc0, 0x29, 0x23, 0xab, 0x0d, 0x53, 0x4e, 0x6f,
    0xd5, 0xdb, 0x37, 0x45, 0xde, 0xfd, 0x8e, 0x2f, 0x03, 0xff, 0x6a, 0x72, 0x6d, 0x6c, 0x5b, 0x51,
    0x8d, 0x1b, 0xaf, 0x92, 0xbb, 0xdd, 0xbc, 0x7f, 0x11, 0xd9, 0x5c, 0x41, 0x1f, 0x10, 0x5a, 0xd8,
    0x0a, 0xc1, 0x31, 0x88, 0xa5, 0xcd, 0x7b, 0xbd, 0x2d, 0x74, 0xd0, 0x12, 0xb8, 0xe5, 0xb4, 0xb0,
    0x89, 0x69, 0x97, 0x4a, 0x0c, 0x96, 0x77, 0x7e, 0x65, 0xb9, 0xf1, 0x09, 0xc5, 0x6e, 0xc6, 0x84,
    0x18, 0xf0, 0x7d, 0xec, 0x3a, 0xdc, 0x4d, 0x20, 0x79, 0xee, 0x5f, 0x3e, 0xd7, 0xcb, 0x39, 0x48
]
FK = [0xa3b1bac6, 0x56aa3350, 0x677d9197, 0xb27022dc]
CK = [
    0x00070e15, 0x1c232a31, 0x383f464d, 0x545b6269,
    0x70777e85, 0x8c939aa1, 0xa8afb6bd, 0xc4cbd2d9,
    0xe0e7eef5, 0xfc030a11, 0x181f262d, 0x343b4249,
    0x50575e65, 0x6c737a81, 0x888f969d, 0xa4abb2b9,
    0xc0c7ced5, 0xdce3eaf1, 0xf8ff060d, 0x141b2229,
    0x30373e45, 0x4c535a61, 0x686f767d, 0x848b9299,
    0xa0a7aeb5, 0xbcc3cad1, 0xd8dfe6ed, 0xf4fb0209,
    0x10171e25, 0x2c333a41, 0x484f565d, 0x646b7279
]

def rotl(x, n):
    left = (x << n) & 0xffffffff
    signed_x = x - 0x100000000 if (x & 0x80000000) else x
    right = (signed_x >> (32 - n)) & 0xffffffff
    return left | right

def sm4_sbox(a):
    return (SboxTable[(a >> 24) & 0xFF] << 24) | \
           (SboxTable[(a >> 16) & 0xFF] << 16) | \
           (SboxTable[(a >> 8) & 0xFF] << 8) | \
           SboxTable[a & 0xFF]

def sm4_lt(ka):
    bb = sm4_sbox(ka)
    return bb ^ rotl(bb, 2) ^ rotl(bb, 10) ^ rotl(bb, 18) ^ rotl(bb, 24)

def sm4_calci_rk(ka):
    bb = sm4_sbox(ka)
    return bb ^ rotl(bb, 13) ^ rotl(bb, 23)

def sm4_f(x0, x1, x2, x3, rk):
    return x0 ^ sm4_lt(x1 ^ x2 ^ x3 ^ rk)

def pkcs7_pad(data: bytes, block_size=16) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len]) * pad_len

def sm4_encrypt_ecb(plain_text: str) -> str:
    data = plain_text.encode('utf-8')
    padded = pkcs7_pad(data, 16)
    key_bytes = SM4_KEY.encode('utf-8')
    mk = [0] * 4
    for i in range(4):
        mk[i] = (key_bytes[i*4] << 24) | (key_bytes[i*4+1] << 16) | (key_bytes[i*4+2] << 8) | key_bytes[i*4+3]
    k = [0] * 36
    for i in range(4):
        k[i] = mk[i] ^ FK[i]
    sk = [0] * 32
    for i in range(32):
        k[i+4] = k[i] ^ sm4_calci_rk(k[i+1] ^ k[i+2] ^ k[i+3] ^ CK[i])
        sk[i] = k[i+4]
    result = bytearray()
    for offset in range(0, len(padded), 16):
        block = padded[offset:offset+16]
        x = [0] * 36
        for i in range(4):
            x[i] = (block[i*4] << 24) | (block[i*4+1] << 16) | (block[i*4+2] << 8) | block[i*4+3]
        for i in range(32):
            x[i+4] = sm4_f(x[i], x[i+1], x[i+2], x[i+3], sk[i])
        out = bytearray(16)
        for i in range(4):
            val = x[35-i]
            out[i*4] = (val >> 24) & 0xFF
            out[i*4+1] = (val >> 16) & 0xFF
            out[i*4+2] = (val >> 8) & 0xFF
            out[i*4+3] = val & 0xFF
        result.extend(out)
    return base64.b64encode(result).decode('utf-8')

# ============================================================
#  /gx 核心功能（使用超级鹰识别验证码，增强超时与日志）
# ============================================================
GX_PHONE, GX_WAIT_SMS = range(20, 22)

def gx_get_captcha():
    """获取验证码，使用超级鹰识别，返回 (code, uuid)"""
    # 初始化 session
    try:
        gx_session.get(GX_BASE_URL, headers=GX_HEADERS, timeout=10)
        print("[gx] 首页初始化成功")
    except Exception as e:
        print(f"[gx] 首页初始化失败（可忽略）: {e}")

    for attempt in range(3):
        try:
            print(f"[gx] 第{attempt+1}次尝试获取验证码...")
            url = f"{GX_BASE_URL}/Wechat/FaceDetect/GetVerifyCode"
            resp = gx_session.get(url, headers=GX_HEADERS, timeout=30)
            if resp.status_code != 200:
                print(f"[gx] 第{attempt+1}次：HTTP {resp.status_code}")
                time.sleep(2)
                continue

            data = resp.json()
            if data.get("statusCode") != 200:
                print(f"[gx] 第{attempt+1}次：接口返回错误 {data.get('info')}")
                time.sleep(2)
                continue

            img_b64 = data.get("data", {}).get("img")
            uuid = data.get("data", {}).get("uuid")
            if not img_b64 or not uuid:
                print("[gx] 返回数据缺少 img 或 uuid")
                time.sleep(2)
                continue

            img_bytes = base64.b64decode(img_b64)
            print(f"[gx] 验证码图片获取成功，大小 {len(img_bytes)} 字节")

            # ---------- 使用超级鹰识别 ----------
            try:
                print("[gx] 正在调用超级鹰API...")
                result = chaojiying.PostPic(img_bytes, CJY_CODETYPE)
                print(f"[gx] 超级鹰返回: {result}")
                if result.get('err_no') == 0:
                    code = result.get('pic_str')
                    print(f"[gx] 超级鹰识别成功：{code}")
                else:
                    print(f"[gx] 超级鹰识别失败: {result.get('err_str')}")
                    code = None
            except requests.exceptions.Timeout:
                print("[gx] 超级鹰API超时，请检查网络")
                code = None
            except Exception as e:
                print(f"[gx] 超级鹰调用异常: {e}")
                code = None

            if code:
                code = re.sub(r'[^A-Z0-9]', '', code.upper())
                if len(code) == 4:
                    print(f"[gx] 最终验证码：{code}")
                    return code, uuid
                else:
                    print(f"[gx] 识别结果长度异常（{len(code)}），内容：{code}")
            else:
                print("[gx] 超级鹰未能识别，等待重试...")

            time.sleep(2)
        except requests.exceptions.Timeout:
            print(f"[gx] 第{attempt+1}次请求超时")
            time.sleep(2)
        except Exception as e:
            print(f"[gx] 第{attempt+1}次异常：{e}")
            import traceback
            traceback.print_exc()
            time.sleep(2)

    return None, None

def gx_send_sms(phone, captcha_code, uuid):
    data = {
        "phoneId": phone,
        "type": "10001",
        "IsEncryptPhoneId": "false",
        "verifyCode": captcha_code,
        "uuid": uuid
    }
    try:
        r = gx_session.post(
            f"{GX_BASE_URL}/System/SmsService/PostVerifyCode",
            data=data,
            headers={**GX_HEADERS, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
            timeout=60
        )
        if r.status_code == 200:
            res = r.json()
            return res.get("statusCode") == 200
        return False
    except Exception as e:
        print(f"[gx] 发送短信失败: {e}")
        return False

def gx_register(phone, sms_code, captcha_code, real_name, id_card):
    data = {
        "zipArea": "",
        "userType": "-1",
        "wechatUid": "",
        "realName": real_name,
        "iDCard": id_card,
        "loginName": id_card,
        "password": GX_PASSWORD,
        "idcardImg1Url": "218,8a785f252c8518",
        "idcardImg2Url": "216,8a7860c46589f3",
        "idcardImg3Url": "214,8a78664776227f",
        "idcardImg4Url": "",
        "ownerId": "",
        "tel": phone,
        "isTelEncrypted": "false",
        "validCode": sms_code,
        "verifyCode": captcha_code
    }
    try:
        r = gx_session.post(
            f"{GX_BASE_URL}/Wechat/User/RegistAdd",
            data=data,
            headers={**GX_HEADERS, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
            timeout=60
        )
        if r.status_code == 200:
            res = r.json()
            return res.get("statusCode") == 200
        return False
    except Exception as e:
        print(f"[gx] 注册异常: {e}")
        return False

def gx_login(id_card):
    encrypted_login_raw = sm4_encrypt_ecb(id_card)
    encrypted_pwd_raw = sm4_encrypt_ecb(GX_PASSWORD)
    encrypted_login = urllib.parse.quote(encrypted_login_raw)
    encrypted_pwd = urllib.parse.quote(encrypted_pwd_raw)
    data = f"loginName={encrypted_login}&password={encrypted_pwd}&wechatUid="
    login_headers = {
        **GX_HEADERS,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "http://www.gxdlys.com/Wechat/Home/Login",
        "Host": "www.gxdlys.com"
    }
    try:
        r = gx_session.post(
            "http://www.gxdlys.com/Wechat/Home/PostLogin",
            headers=login_headers,
            data=data,
            timeout=60
        )
        if r.status_code == 200:
            res = r.json()
            return res.get("statusCode") == 200
        return False
    except Exception as e:
        print(f"[gx] 登录异常: {e}")
        return False

def gx_query_id_photo(name, id_card):
    encoded_name = urllib.parse.quote(name)
    url = f"{GX_BASE_URL}/Wechat/FaceDetect/GetGAIDCardPhotoNew?idCard={id_card}&name={encoded_name}"
    query_headers = {
        **GX_HEADERS,
        "Referer": "http://www.gxdlys.com/Wechat/EcertCert/ECertApply?OperateType=0&BnsAcceptId=&ObjectId=&BasicBnsId=46011&Params=%E7%BB%8F%E8%90%A5%E6%80%A7%E9%81%93%E8%B7%AF%E8%B4%A7%E7%89%A9%E8%BF%90%E8%BE%93%E9%A9%BE%E9%A9%B6%E5%91%98&Step=1",
        "Host": "www.gxdlys.com"
    }
    try:
        r = gx_session.get(url, headers=query_headers, timeout=60)
        if r.status_code == 200:
            return r.json()
        return {}
    except Exception as e:
        print(f"[gx] 查询异常: {e}")
        return {}

def gx_download_photo(file_id):
    url = f"{GX_BASE_URL}/System/FileService/ShowFile?fileId={file_id}"
    try:
        r = gx_session.get(url, timeout=60)
        if r.status_code == 200 and 'image' in r.headers.get('Content-Type', ''):
            return r.content
        return None
    except Exception as e:
        print(f"[gx] 下载照片异常: {e}")
        return None

# ---------- /gx 对话处理 ----------
def gx_start(update, context):
    text = update.message.text
    match = re.match(r'/gx\s+(\S+)\s+(\S+)', text)
    if not match:
        update.message.reply_text("❌ 格式错误，请使用：/gx 姓名 身份证号")
        return ConversationHandler.END
    real_name = match.group(1).strip()
    id_card = match.group(2).strip()
    if not re.match(r'^\d{17}[\dXx]$', id_card):
        update.message.reply_text("❌ 身份证号格式不正确（18位数字或末尾X）")
        return ConversationHandler.END
    context.user_data['gx_real_name'] = real_name
    context.user_data['gx_id_card'] = id_card.upper()
    update.message.reply_text("📱 请发送您的手机号（11位数字）：")
    return GX_PHONE

def gx_get_phone(update, context):
    phone = update.message.text.strip()
    if not re.match(r'^1\d{10}$', phone):
        update.message.reply_text("❌ 手机号格式不正确，请重新输入（11位数字）：")
        return GX_PHONE
    context.user_data['gx_phone'] = phone

    update.message.reply_text("⏳ 正在获取图形验证码并识别（超级鹰）...")
    captcha_code, uuid = gx_get_captcha()
    if not captcha_code or not uuid:
        update.message.reply_text("❌ 获取验证码失败，请稍后重试。")
        return ConversationHandler.END

    context.user_data['gx_captcha'] = captcha_code
    context.user_data['gx_uuid'] = uuid
    update.message.reply_text(f"✅ 图形验证码已识别：`{captcha_code}`")

    update.message.reply_text("📤 正在发送短信验证码...")
    if gx_send_sms(phone, captcha_code, uuid):
        update.message.reply_text("📨 短信已发送，请查看手机，输入6位短信验证码：")
        return GX_WAIT_SMS
    else:
        update.message.reply_text("❌ 短信发送失败，请检查手机号或稍后重试。")
        return ConversationHandler.END

def gx_get_sms(update, context):
    sms_code = update.message.text.strip()
    if not re.match(r'^\d{6}$', sms_code):
        update.message.reply_text("❌ 验证码应为6位数字，请重新输入：")
        return GX_WAIT_SMS

    real_name = context.user_data['gx_real_name']
    id_card = context.user_data['gx_id_card']
    phone = context.user_data['gx_phone']
    captcha_code = context.user_data['gx_captcha']

    update.message.reply_text("⏳ 正在注册账户...")
    if gx_register(phone, sms_code, captcha_code, real_name, id_card):
        update.message.reply_text("✅ 注册成功！正在登录...")
        if gx_login(id_card):
            update.message.reply_text("✅ 登录成功，正在查询身份证信息...")
            result = gx_query_id_photo(real_name, id_card)
            if result and result.get("statusCode") == 200:
                data = result.get("data", {})
                item2 = data.get("item2", {})
                if item2:
                    xm = item2.get("xm", "")
                    sfz = item2.get("gmsfhm", "")
                    mz = item2.get("mz", "").replace("族", "")
                    qfjg = item2.get("issueD_UNIT", "")
                    zz = item2.get("fulladdr", "")
                    yxqq = item2.get("uL_FROM_DATE", "").replace("-", ".")
                    yxqz = item2.get("uL_END_DATE", "").replace("-", ".")
                    info = (
                        f"👤 姓名：{xm}\n"
                        f"🆔 身份证：{sfz}\n"
                        f"🌏 民族：{mz}\n"
                        f"🏛️ 签发机关：{qfjg}\n"
                        f"📍 住址：{zz}\n"
                        f"📅 有效期：{yxqq} 至 {yxqz}"
                    )
                    update.message.reply_text(f"📄 身份信息：\n{info}")
                file_id = data.get("item1")
                if file_id:
                    img_data = gx_download_photo(file_id)
                    if img_data:
                        update.message.reply_photo(
                            photo=img_data,
                            caption=f"{real_name} 的身份证照片"
                        )
                    else:
                        update.message.reply_text("⚠️ 照片下载失败。")
                else:
                    update.message.reply_text("⚠️ 未找到照片。")
            else:
                update.message.reply_text("❌ 查询身份信息失败。")
        else:
            update.message.reply_text("❌ 登录失败，可能密码错误或账户异常。")
    else:
        update.message.reply_text("❌ 注册失败，请检查信息是否正确或稍后重试。")

    context.user_data.clear()
    return ConversationHandler.END

def gx_cancel(update, context):
    update.message.reply_text("🚫 操作已取消。")
    context.user_data.clear()
    return ConversationHandler.END

# ============================================================
#  /hainansf 海南查询
# ============================================================
HEADERS1 = {
    "Host": "zwfw.dn.haikou.gov.cn",
    "Connection": "keep-alive",
    "sec-ch-ua-platform": "\"Android\"",
    "zwfw-token": ZWFW_TOKEN,
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; MEIZU 21 Build/UKQ1.230917.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/141.0.7390.97 Mobile Safari/537.36 AgentWeb/5.0.0  yssApp",
    "sec-ch-ua": "\"Android WebView\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
    "sec-ch-ua-mobile": "?1",
    "content-type": "application/json",
    "Accept": "*/*",
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

# ============================================================
#  /sfz 生成身份证
# ============================================================
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

# ============================================================
#  /plc 生成PLC模板
# ============================================================
def load_area_map():
    area_map = {}
    file_path = 'plc/地区.txt'
    if not os.path.exists(file_path):
        print("警告: 地区文件不存在 (plc/地区.txt)")
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
        print("已加载地区数据，共 {} 条记录".format(len(area_map)))
    except Exception as e:
        print("加载地区文件失败: " + str(e))
    return area_map

AREA_MAP = load_area_map()

def get_address_from_idcard(id_card):
    prefix = id_card[:6]
    return AREA_MAP.get(prefix, None)

def generate_plc_sync(name, id_card, address, avatar_path):
    if len(id_card) != 18:
        raise ValueError("身份证号必须为18位")
    gender = "男" if int(id_card[16]) % 2 == 1 else "女"

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

# ============================================================
#  Telegram 入口命令
# ============================================================
def start(update, context):
    update.message.reply_text(
        "小宇：\n"
        "/hainansf +空格+ 身份证→查询海南大头\n"
        "/sfz → 生成双面身份证·自动签发机关\n"
        "/plc → 生成PLC模板自动地址·按钮确认或手动输入\n"
        "/gx 姓名 身份证号 → 自动注册并查询身份证（gxdlys）\n"
        "/cancel → 取消当前操作"
    )

def hainansf(update, context):
    args = context.args
    if not args:
        update.message.reply_text("❌ 格式错误\n正确格式：/hainansf <身份证号>")
        return
    id_card = args[0].strip()
    if len(id_card) != 18:
        update.message.reply_text("❌ 身份证号必须为18位")
        return
    update.message.reply_text("⏳ 正在查询海南系统...")
    success, result = query_id_card_sync(id_card)
    if success:
        context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=io.BytesIO(result),
            filename=f"{id_card}.pdf",
            caption="✅ 查询成功"
        )
    else:
        update.message.reply_text(f"❌ 查询失败：{result}")

def cancel(update, context):
    update.message.reply_text("已取消")
    context.user_data.clear()
    return ConversationHandler.END

# ===== /sfz 对话 =====
SFZ_NAME, SFZ_ID, SFZ_NATION, SFZ_ADDR, SFZ_EXPIRY, SFZ_PHOTO = range(6)

def sfz_start(update, context):
    update.message.reply_text("📝 开始生成身份证（标准模板），请输入姓名：")
    return SFZ_NAME

def sfz_name(update, context):
    context.user_data['name'] = update.message.text.strip()
    update.message.reply_text("请输入18位身份证号：")
    return SFZ_ID

def sfz_id(update, context):
    id_card = update.message.text.strip().upper()
    if len(id_card) != 18 or not (id_card[:17].isdigit() and id_card[-1] in '0123456789X'):
        update.message.reply_text("格式错误，重新输入：")
        return SFZ_ID
    context.user_data['id_number'] = id_card
    update.message.reply_text("请输入民族：")
    return SFZ_NATION

def sfz_nation(update, context):
    context.user_data['nation'] = update.message.text.strip()
    update.message.reply_text("请输入地址：")
    return SFZ_ADDR

def sfz_address(update, context):
    context.user_data['address'] = update.message.text.strip()
    update.message.reply_text("请输入有效期（如 2020.01.01-2030.01.01）：")
    return SFZ_EXPIRY

def sfz_expiry(update, context):
    context.user_data['expiry'] = update.message.text.strip()
    update.message.reply_text("请发送一张本人照片：")
    return SFZ_PHOTO

def sfz_photo(update, context):
    if not update.message.photo:
        update.message.reply_text("请发送图片。")
        return SFZ_PHOTO
    photo = update.message.photo[-1]
    file = photo.get_file()
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        file.download(tmp.name)
        photo_path = tmp.name

    data = context.user_data
    if not all(k in data for k in ['name','id_number','nation','address','expiry']):
        update.message.reply_text("信息不完整，请重新 /sfz")
        return ConversationHandler.END

    update.message.reply_text("⏳ 生成中...")
    try:
        img, pdf = generate_id_card_sync(
            data['name'], data['id_number'], data['nation'],
            data['address'], data['expiry'], photo_path
        )
        update.message.reply_photo(photo=img, caption=f"✅ {data['name']} 的身份证")
        context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=pdf,
            filename=f"{data['name']}_身份证.pdf"
        )
    except Exception as e:
        update.message.reply_text(f"❌ 失败：{e}")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)
        context.user_data.clear()
    return ConversationHandler.END

# ===== /plc 对话 =====
PLC_NAME, PLC_ID, PLC_ADDR_CONFIRM, PLC_ADDR_MANUAL, PLC_PHOTO = range(10, 15)

def plc_start(update, context):
    update.message.reply_text("📝 开始生成身份证（PLC模板），请输入姓名：")
    return PLC_NAME

def plc_name(update, context):
    context.user_data['name'] = update.message.text.strip()
    update.message.reply_text("请输入18位身份证号：")
    return PLC_ID

def plc_id(update, context):
    id_card = update.message.text.strip().upper()
    if len(id_card) != 18 or not (id_card[:17].isdigit() and id_card[-1] in '0123456789X'):
        update.message.reply_text("格式错误，重新输入：")
        return PLC_ID
    context.user_data['id_number'] = id_card

    address = get_address_from_idcard(id_card)
    if address:
        context.user_data['auto_addr'] = address
        keyboard = [
            [InlineKeyboardButton("✅ 是，使用此地址", callback_data="plc_addr_yes")],
            [InlineKeyboardButton("❌ 否，手动输入", callback_data="plc_addr_no")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            f"✅ 自动匹配到地址：{address}\n请选择是否使用此地址：",
            reply_markup=reply_markup
        )
        return PLC_ADDR_CONFIRM
    else:
        if not AREA_MAP:
            update.message.reply_text("⚠️ 地区文件为空或未加载，请手动输入详细地址：")
        else:
            update.message.reply_text("⚠️ 无法自动匹配地址，请手动输入详细地址：")
        return PLC_ADDR_MANUAL

def plc_addr_confirm_callback(update, context):
    query = update.callback_query
    query.answer()
    data = query.data
    if data == "plc_addr_yes":
        address = context.user_data.get('auto_addr')
        if address:
            context.user_data['address'] = address
            query.edit_message_text(f"✅ 已使用地址：{address}\n请发送一张本人照片：")
            return PLC_PHOTO
        else:
            query.edit_message_text("未找到自动匹配地址，请手动输入：")
            return PLC_ADDR_MANUAL
    elif data == "plc_addr_no":
        query.edit_message_text("请输入详细地址（手动输入）：")
        return PLC_ADDR_MANUAL

def plc_addr_manual(update, context):
    address = update.message.text.strip()
    if not address:
        update.message.reply_text("地址不能为空，请重新输入：")
        return PLC_ADDR_MANUAL
    context.user_data['address'] = address
    update.message.reply_text("请发送一张本人照片：")
    return PLC_PHOTO

def plc_photo(update, context):
    if not update.message.photo:
        update.message.reply_text("请发送图片。")
        return PLC_PHOTO
    photo = update.message.photo[-1]
    file = photo.get_file()
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        file.download(tmp.name)
        photo_path = tmp.name

    data = context.user_data
    if not all(k in data for k in ['name','id_number','address']):
        update.message.reply_text("信息不完整，请重新 /plc")
        return ConversationHandler.END

    update.message.reply_text("⏳ 生成中...")
    try:
        img, pdf = generate_plc_sync(
            data['name'], data['id_number'], data['address'], photo_path
        )
        update.message.reply_photo(photo=img, caption=f"✅ {data['name']} 的身份证（PLC模板）")
        context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=pdf,
            filename=f"{data['name']}_身份证_PLC.pdf"
        )
    except FileNotFoundError as e:
        update.message.reply_text(f"❌ 文件缺失：{e}\n请确保 plc/ 目录下有 mb.jpg 和 10.ttf")
    except Exception as e:
        update.message.reply_text(f"❌ 生成失败：{e}")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)
        context.user_data.clear()
    return ConversationHandler.END

# ============================================================
#  主程序
# ============================================================
def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    # 普通命令
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("hainansf", hainansf))
    dp.add_handler(CommandHandler("cancel", cancel))

    # /sfz 对话
    conv_sfz = ConversationHandler(
        entry_points=[CommandHandler('sfz', sfz_start)],
        states={
            SFZ_NAME: [MessageHandler(Filters.text & ~Filters.command, sfz_name)],
            SFZ_ID: [MessageHandler(Filters.text & ~Filters.command, sfz_id)],
            SFZ_NATION: [MessageHandler(Filters.text & ~Filters.command, sfz_nation)],
            SFZ_ADDR: [MessageHandler(Filters.text & ~Filters.command, sfz_address)],
            SFZ_EXPIRY: [MessageHandler(Filters.text & ~Filters.command, sfz_expiry)],
            SFZ_PHOTO: [MessageHandler(Filters.photo, sfz_photo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dp.add_handler(conv_sfz)

    # /plc 对话
    conv_plc = ConversationHandler(
        entry_points=[CommandHandler('plc', plc_start)],
        states={
            PLC_NAME: [MessageHandler(Filters.text & ~Filters.command, plc_name)],
            PLC_ID: [MessageHandler(Filters.text & ~Filters.command, plc_id)],
            PLC_ADDR_CONFIRM: [CallbackQueryHandler(plc_addr_confirm_callback, pattern='^(plc_addr_yes|plc_addr_no)$')],
            PLC_ADDR_MANUAL: [MessageHandler(Filters.text & ~Filters.command, plc_addr_manual)],
            PLC_PHOTO: [MessageHandler(Filters.photo, plc_photo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dp.add_handler(conv_plc)

    # /gx 对话（使用超级鹰）
    conv_gx = ConversationHandler(
        entry_points=[CommandHandler('gx', gx_start)],
        states={
            GX_PHONE: [MessageHandler(Filters.text & ~Filters.command, gx_get_phone)],
            GX_WAIT_SMS: [MessageHandler(Filters.text & ~Filters.command, gx_get_sms)],
        },
        fallbacks=[CommandHandler('cancel', gx_cancel)],
    )
    dp.add_handler(conv_gx)

    print("🤖 机器人已启动（四功能完整版，验证码使用超级鹰，增强超时）")
    updater.start_polling(drop_pending_updates=True)
    updater.idle()

if __name__ == "__main__":
    main()
