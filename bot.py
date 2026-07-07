#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot 完整版（JSON存储 + 广西自动注册查询）
"""

import sys
print("===== Bot 完整版（广西自动注册查询）=====")

import os, time, json, io, tempfile, requests, urllib3, logging, re, random, threading, hashlib, hmac, urllib.parse, base64
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackQueryHandler
from flask import Flask, request, jsonify

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MergedBot')

# ===== 配置 =====
BOT_TOKEN = os.environ.get('BOT_TOKEN') or "5849383582:AAERYX0V4qwtQGggXTWQsFI5rlojuNY6oWM"
BASE_COOKIES = {
    "cna": os.environ.get('CNA') or "REPLACE_CNA_HERE",
    "JSESSIONID": os.environ.get('JSESSIONID') or "REPLACE_JSESSIONID_HERE",
    "SESSION": os.environ.get('SESSION') or "REPLACE_SESSION_HERE",
    "SERVERID": os.environ.get('SERVERID') or "REPLACE_SERVERID_HERE",
}
ZWFW_TOKEN = os.environ.get('ZWFW_TOKEN') or "REPLACE_ZWFW_TOKEN_HERE"
FIXED_NAME = "刘德华"
SAVE_FOLDER = "temp_files"
RETRY_TIMES = 5
OKPAY_ID = int(os.environ.get('OKPAY_ID') or 36326)
OKPAY_TOKEN = os.environ.get('OKPAY_TOKEN') or 'TCtvS9O6idNOw3XaDyoTEEVG8awJCkdb'
OKPAY_API_URL = 'https://api.okaypay.me/shop/'
CALLBACK_URL = os.environ.get('CALLBACK_URL') or 'https://docs.okaypay.me/'
PORT = 8080
POINTS_RATE = 1
CHECK_INTERVAL = 0.5
ORDER_TIMEOUT = 1800
GX_QUERY_PRICE = 0.05
GX_PASSWORD = "268428."
GX_BASE_URL = "http://www.gxdlys.com"
ADMIN_IDS = [6040143940]

# ===== JSON 存储 =====
USERS_FILE = "users.json"
try:
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    users = {}

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def ensure_user(user_id):
    if str(user_id) not in users:
        users[str(user_id)] = {
            "points": 0.0,
            "total_recharge": 0.0,
            "invites": 0,
            "last_sign_date": "",
            "created_at": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        save_users()

def get_user_stats(user_id):
    ensure_user(user_id)
    data = users[str(user_id)]
    return {
        'points': data.get('points', 0.0),
        'total_recharge': data.get('total_recharge', 0.0),
        'last_sign_date': data.get('last_sign_date', '')
    }

# ===== SM4 加密（广西专用） =====
SM4_KEY = "CatsPK0WWWRRhjkw"
SboxTable = [
    0xd6,0x90,0xe9,0xfe,0xcc,0xe1,0x3d,0xb7,0x16,0xb6,0x14,0xc2,0x28,0xfb,0x2c,0x05,
    0x2b,0x67,0x9a,0x76,0x2a,0xbe,0x04,0xc3,0xaa,0x44,0x13,0x26,0x49,0x86,0x06,0x99,
    0x9c,0x42,0x50,0xf4,0x91,0xef,0x98,0x7a,0x33,0x54,0x0b,0x43,0xed,0xcf,0xac,0x62,
    0xe4,0xb3,0x1c,0xa9,0xc9,0x08,0xe8,0x95,0x80,0xdf,0x94,0xfa,0x75,0x8f,0x3f,0xa6,
    0x47,0x07,0xa7,0xfc,0xf3,0x73,0x17,0xba,0x83,0x59,0x3c,0x19,0xe6,0x85,0x4f,0xa8,
    0x68,0x6b,0x81,0xb2,0x71,0x64,0xda,0x8b,0xf8,0xeb,0x0f,0x4b,0x70,0x56,0x9d,0x35,
    0x1e,0x24,0x0e,0x5e,0x63,0x58,0xd1,0xa2,0x25,0x22,0x7c,0x3b,0x01,0x21,0x78,0x87,
    0xd4,0x00,0x46,0x57,0x9f,0xd3,0x27,0x52,0x4c,0x36,0x02,0xe7,0xa0,0xc4,0xc8,0x9e,
    0xea,0xbf,0x8a,0xd2,0x40,0xc7,0x38,0xb5,0xa3,0xf7,0xf2,0xce,0xf9,0x61,0x15,0xa1,
    0xe0,0xae,0x5d,0xa4,0x9b,0x34,0x1a,0x55,0xad,0x93,0x32,0x30,0xf5,0x8c,0xb1,0xe3,
    0x1d,0xf6,0xe2,0x2e,0x82,0x66,0xca,0x60,0xc0,0x29,0x23,0xab,0x0d,0x53,0x4e,0x6f,
    0xd5,0xdb,0x37,0x45,0xde,0xfd,0x8e,0x2f,0x03,0xff,0x6a,0x72,0x6d,0x6c,0x5b,0x51,
    0x8d,0x1b,0xaf,0x92,0xbb,0xdd,0xbc,0x7f,0x11,0xd9,0x5c,0x41,0x1f,0x10,0x5a,0xd8,
    0x0a,0xc1,0x31,0x88,0xa5,0xcd,0x7b,0xbd,0x2d,0x74,0xd0,0x12,0xb8,0xe5,0xb4,0xb0,
    0x89,0x69,0x97,0x4a,0x0c,0x96,0x77,0x7e,0x65,0xb9,0xf1,0x09,0xc5,0x6e,0xc6,0x84,
    0x18,0xf0,0x7d,0xec,0x3a,0xdc,0x4d,0x20,0x79,0xee,0x5f,0x3e,0xd7,0xcb,0x39,0x48
]
FK = [0xa3b1bac6,0x56aa3350,0x677d9197,0xb27022dc]
CK = [0x00070e15,0x1c232a31,0x383f464d,0x545b6269,0x70777e85,0x8c939aa1,0xa8afb6bd,0xc4cbd2d9,0xe0e7eef5,0xfc030a11,0x181f262d,0x343b4249,0x50575e65,0x6c737a81,0x888f969d,0xa4abb2b9,0xc0c7ced5,0xdce3eaf1,0xf8ff060d,0x141b2229,0x30373e45,0x4c535a61,0x686f767d,0x848b9299,0xa0a7aeb5,0xbcc3cad1,0xd8dfe6ed,0xf4fb0209,0x10171e25,0x2c333a41,0x484f565d,0x646b7279]

def rotl(x,n):
    left=(x<<n)&0xffffffff
    signed_x=x-0x100000000 if (x&0x80000000) else x
    right=(signed_x>>(32-n))&0xffffffff
    return left|right

def sm4_sbox(a):
    return (SboxTable[(a>>24)&0xFF]<<24)|(SboxTable[(a>>16)&0xFF]<<16)|(SboxTable[(a>>8)&0xFF]<<8)|SboxTable[a&0xFF]

def sm4_lt(ka):
    bb=sm4_sbox(ka); return bb^rotl(bb,2)^rotl(bb,10)^rotl(bb,18)^rotl(bb,24)

def sm4_calci_rk(ka):
    bb=sm4_sbox(ka); return bb^rotl(bb,13)^rotl(bb,23)

def sm4_f(x0,x1,x2,x3,rk):
    return x0^sm4_lt(x1^x2^x3^rk)

def pkcs7_pad(data:bytes, block_size=16):
    pad_len=block_size-(len(data)%block_size); return data+bytes([pad_len])*pad_len

def sm4_encrypt_ecb(plain_text:str)->str:
    data=plain_text.encode('utf-8'); padded=pkcs7_pad(data,16); key_bytes=SM4_KEY.encode('utf-8')
    mk=[0]*4
    for i in range(4): mk[i]=(key_bytes[i*4]<<24)|(key_bytes[i*4+1]<<16)|(key_bytes[i*4+2]<<8)|key_bytes[i*4+3]
    k=[0]*36
    for i in range(4): k[i]=mk[i]^FK[i]
    sk=[0]*32
    for i in range(32):
        k[i+4]=k[i]^sm4_calci_rk(k[i+1]^k[i+2]^k[i+3]^CK[i]); sk[i]=k[i+4]
    result=bytearray()
    for offset in range(0,len(padded),16):
        block=padded[offset:offset+16]
        x=[0]*36
        for i in range(4): x[i]=(block[i*4]<<24)|(block[i*4+1]<<16)|(block[i*4+2]<<8)|block[i*4+3]
        for i in range(32): x[i+4]=sm4_f(x[i],x[i+1],x[i+2],x[i+3],sk[i])
        out=bytearray(16)
        for i in range(4):
            val=x[35-i]; out[i*4]=(val>>24)&0xFF; out[i*4+1]=(val>>16)&0xFF; out[i*4+2]=(val>>8)&0xFF; out[i*4+3]=val&0xFF
        result.extend(out)
    return base64.b64encode(result).decode('utf-8')

# ===== 广西查询（完整：登录+注册+查询） =====
def gx_login(session, id_card):
    encrypted_login_raw = sm4_encrypt_ecb(id_card)
    encrypted_pwd_raw = sm4_encrypt_ecb(GX_PASSWORD)
    encrypted_login = urllib.parse.quote(encrypted_login_raw)
    encrypted_pwd = urllib.parse.quote(encrypted_pwd_raw)
    data = f"loginName={encrypted_login}&password={encrypted_pwd}&wechatUid="
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; Build/BP2A.250605.031.A3) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "http://www.gxdlys.com/Wechat/Home/Login",
        "Host": "www.gxdlys.com"
    }
    try:
        r = session.post("http://www.gxdlys.com/Wechat/Home/PostLogin", headers=headers, data=data, timeout=30)
        if r.status_code == 200:
            res = r.json()
            return res.get("statusCode") == 200, res.get("info", "")
        return False, str(r.status_code)
    except Exception as e:
        return False, str(e)

def gx_get_captcha(session):
    try:
        url = "http://www.gxdlys.com/Wechat/FaceDetect/GetVerifyCode"
        r = session.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("statusCode") == 200:
                img_b64 = data.get("data", {}).get("img")
                uuid = data.get("data", {}).get("uuid")
                if img_b64 and uuid:
                    return True, img_b64, uuid
        return False, None, None
    except Exception as e:
        return False, None, None

def gx_send_sms(session, phone, captcha_code, uuid):
    try:
        data = {"phoneId": phone, "type": "10001", "IsEncryptPhoneId": "false", "verifyCode": captcha_code, "uuid": uuid}
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Build/BP2A.250605.031.A3) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "http://www.gxdlys.com/Wechat/User/Regist"
        }
        r = session.post("http://www.gxdlys.com/System/SmsService/PostVerifyCode", data=data, headers=headers, timeout=30)
        if r.status_code == 200:
            res = r.json()
            return res.get("statusCode") == 200
        return False
    except Exception as e:
        return False

def gx_register(session, phone, sms_code, captcha_code, real_name, id_card):
    try:
        data = {
            "zipArea": "", "userType": "-1", "wechatUid": "",
            "realName": real_name, "iDCard": id_card, "loginName": id_card,
            "password": GX_PASSWORD,
            "idcardImg1Url": "218,8a785f252c8518",
            "idcardImg2Url": "216,8a7860c46589f3",
            "idcardImg3Url": "214,8a78664776227f",
            "idcardImg4Url": "", "ownerId": "",
            "tel": phone, "isTelEncrypted": "false",
            "validCode": sms_code, "verifyCode": captcha_code
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Build/BP2A.250605.031.A3) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "http://www.gxdlys.com/Wechat/User/Regist"
        }
        r = session.post("http://www.gxdlys.com/Wechat/User/RegistAdd", data=data, headers=headers, timeout=30)
        if r.status_code == 200:
            res = r.json()
            return res.get("statusCode") == 200, res.get("info", "")
        return False, str(r.status_code)
    except Exception as e:
        return False, str(e)

def gx_query_photo(session, name, id_card):
    try:
        encoded_name = urllib.parse.quote(name)
        url = f"http://www.gxdlys.com/Wechat/FaceDetect/GetGAIDCardPhotoNew?idCard={id_card}&name={encoded_name}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Build/BP2A.250605.031.A3) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Referer": "http://www.gxdlys.com/Wechat/EcertCert/ECertApply?OperateType=0&BnsAcceptId=&ObjectId=&BasicBnsId=46011&Params=%E7%BB%8F%E8%90%A5%E6%80%A7%E9%81%93%E8%B7%AF%E8%B4%A7%E7%89%A9%E8%BF%90%E8%BE%93%E9%A9%BE%E9%A9%B6%E5%91%98&Step=1",
            "Host": "www.gxdlys.com"
        }
        r = session.get(url, headers=headers, timeout=30)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"
        res = r.json()
        if res.get("statusCode") != 200:
            return False, res.get("info", "查询失败")
        file_id = res.get("data", {}).get("item1")
        if not file_id:
            return False, "未获取到照片文件ID"
        photo_resp = session.get(f"http://www.gxdlys.com/System/FileService/ShowFile?fileId={file_id}", timeout=30)
        if photo_resp.status_code != 200 or 'image' not in photo_resp.headers.get('Content-Type', ''):
            return False, "照片下载失败"
        return True, photo_resp.content
    except Exception as e:
        return False, str(e)

# ===== 身份证生成函数（完整保留，省略部分以节约篇幅） =====
# 由于篇幅，此处省略 HEADERS1, HEADERS2, query_id_card_sync, remove_white_background,
# load_issuing_authority_map, get_issuing_authority, format_address,
# generate_id_card_sync, load_area_map, AREA_MAP, get_address_from_idcard, generate_plc_sync
# 这些函数与之前完全相同，请从之前的版本复制

# ===== OkayPay 客户端 =====
class OkayPay:
    def __init__(self, appid, token, api_url): self.appid=appid; self.token=token; self.api_url=api_url
    def _build_base(self, params):
        params={k:v for k,v in params.items() if k!='sign' and v is not None and v!=''}
        def flatten(obj, prefix=''):
            items={}
            if isinstance(obj, dict):
                for k,v in obj.items():
                    key=f"{prefix}.{k}" if prefix else k
                    if isinstance(v, dict): items.update(flatten(v, key))
                    else: items[key]=v
            else: items[prefix]=obj
            return items
        flat={}
        for k,v in params.items():
            if isinstance(v, dict): flat.update(flatten(v, k))
            elif isinstance(v, bool): flat[k]='true' if v else 'false'
            else: flat[k]=str(v)
        sorted_params=dict(sorted(flat.items()))
        base='&'.join([f"{k}={v}" for k,v in sorted_params.items()])
        return base
    def _sign(self, params):
        base=self._build_base(params)
        sign=hmac.new(self.token.encode('utf-8'), base.encode('utf-8'), hashlib.sha256).hexdigest().upper()
        return sign
    def _signed_params(self, params):
        nonce=''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16))
        timestamp=int(time.time())
        full_params={'id':str(self.appid),'timestamp':timestamp,'nonce':nonce,**params}
        full_params['sign']=self._sign(full_params)
        return full_params
    def verify(self, data):
        if 'sign' not in data: return False
        in_sign=data['sign']; calc_sign=self._sign(data); return calc_sign==in_sign
    def pay_link(self, amount, unique_id):
        params={'amount':f"{amount:.2f}",'coin':'USDT','unique_id':unique_id,'name':'积分充值','callback_url':CALLBACK_URL,'return_url':CALLBACK_URL}
        signed=self._signed_params(params)
        try:
            resp=requests.post(self.api_url+'payLink', data=signed, headers={'Content-Type':'application/x-www-form-urlencoded'}, timeout=15, verify=False)
            if resp.status_code==200:
                result=resp.json()
                if result.get('status')=='success' and self.verify(result):
                    return result
                else:
                    return {'status':'error','msg':result.get('msg','未知错误')}
            else: return {'status':'error','msg':f'HTTP {resp.status_code}'}
        except Exception as e: return {'status':'error','msg':str(e)}
    def check_deposit(self, unique_id):
        params={'unique_id':unique_id}; signed=self._signed_params(params)
        try:
            resp=requests.post(self.api_url+'checkDeposit', data=signed, headers={'Content-Type':'application/x-www-form-urlencoded'}, timeout=15, verify=False)
            if resp.status_code==200:
                result=resp.json()
                if result.get('status')=='success' and self.verify(result): return result
                else: return {'status':'error','msg':result.get('msg','验证失败')}
            else: return {'status':'error','msg':f'HTTP {resp.status_code}'}
        except Exception as e: return {'status':'error','msg':str(e)}

client=OkayPay(OKPAY_ID, OKPAY_TOKEN, OKPAY_API_URL)
orders={}

def check_orders():
    while True:
        try:
            now=time.time(); expired=[]
            for uid, info in list(orders.items()):
                if now-info['timestamp']>ORDER_TIMEOUT: expired.append(uid); continue
                if info['status']=='pending':
                    result=client.check_deposit(uid)
                    if result and result.get('status')=='success':
                        data=result.get('data',{}); status=data.get('status')
                        if status==1:
                            user_id=info['user_id']; amount=float(data.get('amount',0)); order_id=data.get('order_id')
                            points=amount*POINTS_RATE
                            ensure_user(user_id)
                            users[str(user_id)]['points'] = users[str(user_id)].get('points', 0.0) + points
                            users[str(user_id)]['total_recharge'] = users[str(user_id)].get('total_recharge', 0.0) + amount
                            save_users()
                            stats=get_user_stats(user_id)
                            try: bot.send_message(user_id, f"✅ 支付成功！\n订单号: {order_id}\n充值: {amount:.2f} USDT\n获得积分: {points:.2f}\n当前积分: {stats['points']:.2f}")
                            except: pass
                            orders[uid]['status']='completed'
            for uid in expired:
                user_id=orders[uid]['user_id']
                try: bot.send_message(user_id, f"⏰ 订单 {uid} 已过期")
                except: pass
                del orders[uid]
        except Exception as e: logger.error(f"轮询异常: {e}")
        time.sleep(CHECK_INTERVAL)

flask_app=Flask(__name__)
@flask_app.route('/OkPay.php', methods=['POST'])
def callback():
    try:
        data=request.get_json() if request.content_type and 'application/json' in request.content_type else request.form.to_dict()
        if not client.verify(data): return jsonify({'status':'success'}), 200
        return jsonify({'status':'success'}), 200
    except Exception as e: return jsonify({'status':'success'}), 200

def run_flask(): flask_app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# ===== Telegram 命令 =====

# 广西查询对话状态
WAITING_CAPTCHA, WAITING_SMS, WAITING_PHONE = range(100, 103)

def start(update, context):
    uid = update.effective_user.id
    ensure_user(uid)
    stats = get_user_stats(uid)
    first_name = update.effective_user.first_name or "用户"
    update.message.reply_text(
        f"👤 用户名称：{first_name}\n"
        f"🆔 用户ID：{uid}\n"
        f"💎 账户积分：{stats['points']:.2f}\n"
        f"🌟 每日签到可获得 0.05 积分\n"
        f"使用 /signin 签到\n\n"
        f"可用命令：\n"
        f"/hainansf +空格+身份证 → 查询海南大头\n"
        f"/sfz → 生成标准身份证（双面）\n"
        f"/plc → 生成PLC模板身份证\n"
        f"/recharge → 充值积分\n"
        f"/balance → 查询积分余额\n"
        f"/gxquery 姓名 身份证 → 查询广西照片（自动注册）\n"
        f"/givepoint 用户ID 积分 [备注] → 管理员赠送\n"
        f"/users → 查看所有用户（管理员）\n"
        f"/reset_signin 用户ID → 重置签到（管理员）\n"
        f"/force_signin 用户ID → 强制签到（管理员）\n"
        f"/clear_all_signin → ⚠️ 清空所有签到日期（管理员）\n"
        f"/cancel → 取消当前操作"
    )

def gxquery_start(update, context):
    """启动广西查询流程"""
    uid = update.effective_user.id
    args = context.args
    if len(args) < 2:
        update.message.reply_text("❌ 格式错误\n正确格式：/gxquery <姓名> <身份证号>")
        return ConversationHandler.END
    
    name = args[0].strip()
    id_card = args[1].strip()
    if len(id_card) != 18:
        update.message.reply_text("❌ 身份证号必须为18位")
        return ConversationHandler.END
    
    # 检查积分
    stats = get_user_stats(uid)
    if stats['points'] < GX_QUERY_PRICE:
        update.message.reply_text(f"❌ 积分不足！需要 {GX_QUERY_PRICE:.2f} 积分，当前 {stats['points']:.2f}")
        return ConversationHandler.END
    
    # 扣积分
    users[str(uid)]['points'] = users[str(uid)].get('points', 0.0) - GX_QUERY_PRICE
    save_users()
    
    # 保存查询参数
    context.user_data['gx_name'] = name
    context.user_data['gx_idcard'] = id_card
    context.user_data['gx_session'] = requests.Session()
    
    # 尝试直接登录
    session = context.user_data['gx_session']
    success, info = gx_login(session, id_card)
    
    if success:
        # 登录成功，直接查询
        update.message.reply_text("⏳ 登录成功，正在查询照片...")
        return gx_do_query(update, context)
    elif "未注册" in info or "不存在" in info:
        # 需要注册
        update.message.reply_text("⚠️ 该身份证未注册，需要先注册才能查询。")
        update.message.reply_text("请输入您的手机号：")
        return WAITING_PHONE
    else:
        # 其他错误
        users[str(uid)]['points'] = users[str(uid)].get('points', 0.0) + GX_QUERY_PRICE
        save_users()
        update.message.reply_text(f"❌ 登录失败: {info}\n已退还 {GX_QUERY_PRICE:.2f} 积分")
        return ConversationHandler.END

def gx_wait_phone(update, context):
    """等待用户输入手机号"""
    phone = update.message.text.strip()
    if not phone or len(phone) < 11:
        update.message.reply_text("❌ 请输入正确的手机号：")
        return WAITING_PHONE
    
    context.user_data['gx_phone'] = phone
    
    # 获取图形验证码
    session = context.user_data['gx_session']
    success, img_b64, uuid = gx_get_captcha(session)
    if not success or not img_b64:
        # 退还积分
        uid = update.effective_user.id
        users[str(uid)]['points'] = users[str(uid)].get('points', 0.0) + GX_QUERY_PRICE
        save_users()
        update.message.reply_text(f"❌ 获取验证码失败，已退还 {GX_QUERY_PRICE:.2f} 积分")
        return ConversationHandler.END
    
    # 保存 uuid
    context.user_data['gx_uuid'] = uuid
    
    # 发送验证码图片
    import base64 as b64
    img_bytes = b64.b64decode(img_b64)
    update.message.reply_photo(
        photo=io.BytesIO(img_bytes),
        caption="📷 请输入图片中的验证码："
    )
    return WAITING_CAPTCHA

def gx_wait_captcha(update, context):
    """等待用户输入图形验证码"""
    captcha = update.message.text.strip().upper()
    if not captcha:
        update.message.reply_text("❌ 请输入验证码：")
        return WAITING_CAPTCHA
    
    context.user_data['gx_captcha'] = captcha
    
    # 发送短信验证码
    session = context.user_data['gx_session']
    phone = context.user_data['gx_phone']
    uuid = context.user_data['gx_uuid']
    
    if gx_send_sms(session, phone, captcha, uuid):
        update.message.reply_text("✅ 短信验证码已发送，请查看手机短信，输入验证码：")
        return WAITING_SMS
    else:
        # 退还积分
        uid = update.effective_user.id
        users[str(uid)]['points'] = users[str(uid)].get('points', 0.0) + GX_QUERY_PRICE
        save_users()
        update.message.reply_text(f"❌ 发送短信失败，已退还 {GX_QUERY_PRICE:.2f} 积分")
        return ConversationHandler.END

def gx_wait_sms(update, context):
    """等待用户输入短信验证码"""
    sms_code = update.message.text.strip()
    if not sms_code:
        update.message.reply_text("❌ 请输入短信验证码：")
        return WAITING_SMS
    
    # 注册
    session = context.user_data['gx_session']
    name = context.user_data['gx_name']
    id_card = context.user_data['gx_idcard']
    phone = context.user_data['gx_phone']
    captcha = context.user_data['gx_captcha']
    
    update.message.reply_text("⏳ 正在注册...")
    
    success, info = gx_register(session, phone, sms_code, captcha, name, id_card)
    if success:
        update.message.reply_text("✅ 注册成功！正在查询照片...")
        return gx_do_query(update, context)
    else:
        # 退还积分
        uid = update.effective_user.id
        users[str(uid)]['points'] = users[str(uid)].get('points', 0.0) + GX_QUERY_PRICE
        save_users()
        update.message.reply_text(f"❌ 注册失败: {info}\n已退还 {GX_QUERY_PRICE:.2f} 积分")
        return ConversationHandler.END

def gx_do_query(update, context):
    """执行查询"""
    uid = update.effective_user.id
    session = context.user_data['gx_session']
    name = context.user_data['gx_name']
    id_card = context.user_data['gx_idcard']
    
    try:
        success, result = gx_query_photo(session, name, id_card)
        if success:
            update.message.reply_photo(
                photo=io.BytesIO(result),
                caption=f"✅ {name} 的身份证照片（广西道路运输）\n消耗积分: {GX_QUERY_PRICE:.2f}"
            )
        else:
            # 查询失败，退还积分
            users[str(uid)]['points'] = users[str(uid)].get('points', 0.0) + GX_QUERY_PRICE
            save_users()
            update.message.reply_text(f"❌ 查询失败: {result}\n已退还 {GX_QUERY_PRICE:.2f} 积分")
    except Exception as e:
        # 异常，退还积分
        users[str(uid)]['points'] = users[str(uid)].get('points', 0.0) + GX_QUERY_PRICE
        save_users()
        update.message.reply_text(f"❌ 查询异常: {str(e)}\n已退还 {GX_QUERY_PRICE:.2f} 积分")
    
    # 清理会话
    context.user_data.clear()
    return ConversationHandler.END

def gxquery_cancel(update, context):
    """取消广西查询"""
    uid = update.effective_user.id
    # 退还积分
    if 'gx_session' in context.user_data:
        users[str(uid)]['points'] = users[str(uid)].get('points', 0.0) + GX_QUERY_PRICE
        save_users()
    context.user_data.clear()
    update.message.reply_text("❌ 已取消查询，积分已退还")
    return ConversationHandler.END

# ===== 其他命令 =====

def hainansf(update, context):
    args=context.args
    if not args: update.message.reply_text("❌ 格式错误\n正确格式：/hainansf <身份证号>"); return
    id_card=args[0].strip()
    if len(id_card)!=18: update.message.reply_text("❌ 身份证号必须为18位"); return
    update.message.reply_text("⏳ 正在查询海南系统...")
    # 需要导入 query_id_card_sync 函数
    success, result = query_id_card_sync(id_card)
    if success:
        context.bot.send_document(chat_id=update.effective_chat.id, document=io.BytesIO(result), filename=f"{id_card}.pdf", caption="✅ 查询成功")
    else:
        update.message.reply_text(f"❌ 查询失败：{result}")

def cancel(update, context):
    update.message.reply_text("已取消")
    context.user_data.clear()
    return ConversationHandler.END

def recharge_start(update, context):
    uid=update.effective_user.id
    ensure_user(uid)
    stats=get_user_stats(uid)
    update.message.reply_text(f"💰 积分充值\n当前积分: {stats['points']:.2f}\n累计充值: {stats['total_recharge']:.2f} USDT\n\n请输入要充值的 USDT 金额（例如 10）：")
    return 1

def recharge_amount(update, context):
    uid=update.effective_user.id
    try: amt=float(re.sub(r'[^\d.]', '', update.message.text))
    except: update.message.reply_text("❌ 请输入有效的正数金额"); return 1
    if amt<=0: update.message.reply_text("❌ 金额必须大于0"); return 1
    points=amt*POINTS_RATE
    unique_id=f"ORDER_{int(time.time())}_{uid}_{random.randint(1000,9999)}"
    resp=client.pay_link(amt, unique_id)
    if not resp or resp.get('status')!='success':
        update.message.reply_text(f"❌ 创建订单失败: {resp.get('msg','未知错误')}")
        return ConversationHandler.END
    order_id=resp['data']['order_id']; pay_url=resp['data']['pay_url']
    orders[unique_id]={'user_id':uid,'amount':amt,'order_id':order_id,'status':'pending','timestamp':time.time()}
    keyboard=[[InlineKeyboardButton("💳 去支付", url=pay_url)]]
    update.message.reply_text(f"✅ 订单已创建\n订单号: {order_id}\n金额: {amt:.2f} USDT → {points:.2f} 积分\n有效期: 30 分钟\n点击下方按钮完成支付", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

def balance(update, context):
    uid=update.effective_user.id
    ensure_user(uid)
    stats=get_user_stats(uid)
    update.message.reply_text(f"📊 您的积分: {stats['points']:.2f}\n累计充值: {stats['total_recharge']:.2f} USDT")

def signin(update, context):
    uid = update.effective_user.id
    ensure_user(uid)
    today = time.strftime('%Y-%m-%d')
    user_data = users[str(uid)]
    if user_data.get('last_sign_date', '') == today:
        update.message.reply_text("❌ 今天已经签到了，明天再来吧！")
        return
    reward = 0.05
    user_data['points'] = user_data.get('points', 0.0) + reward
    user_data['last_sign_date'] = today
    save_users()
    stats = get_user_stats(uid)
    update.message.reply_text(f"✅ 签到成功！获得 {reward:.2f} 积分\n当前积分: {stats['points']:.2f}")

def givepoint(update, context):
    uid=update.effective_user.id
    if uid not in ADMIN_IDS: update.message.reply_text("❌ 您没有管理员权限"); return
    args=context.args
    if len(args)<2: update.message.reply_text("❌ 格式错误\n正确格式：/givepoint <用户ID> <积分数量> [备注]"); return
    try: target_id=int(args[0])
    except: update.message.reply_text("❌ 用户ID必须是数字"); return
    try: amount=float(args[1])
    except: update.message.reply_text("❌ 积分数量必须是数字"); return
    if amount<=0: update.message.reply_text("❌ 积分数量必须大于0"); return
    ensure_user(target_id)
    users[str(target_id)]['points'] = users[str(target_id)].get('points', 0.0) + amount
    save_users()
    stats=get_user_stats(target_id)
    update.message.reply_text(f"✅ 已向用户 {target_id} 赠送 {amount:.2f} 积分，当前积分 {stats['points']:.2f}")

def reset_signin(update, context):
    uid=update.effective_user.id
    if uid not in ADMIN_IDS: update.message.reply_text("❌ 您没有管理员权限"); return
    args=context.args
    if not args: update.message.reply_text("❌ 格式错误\n正确格式：/reset_signin <用户ID>"); return
    try: target_id=int(args[0])
    except: update.message.reply_text("❌ 用户ID必须是数字"); return
    ensure_user(target_id)
    users[str(target_id)]['last_sign_date'] = ''
    save_users()
    update.message.reply_text(f"✅ 已重置用户 {target_id} 的签到状态")

def force_signin(update, context):
    uid=update.effective_user.id
    if uid not in ADMIN_IDS: update.message.reply_text("❌ 您没有管理员权限"); return
    args=context.args
    if not args: update.message.reply_text("❌ 格式错误\n正确格式：/force_signin <用户ID>"); return
    try: target_id=int(args[0])
    except: update.message.reply_text("❌ 用户ID必须是数字"); return
    ensure_user(target_id)
    users[str(target_id)]['last_sign_date'] = ''
    reward = 0.05
    users[str(target_id)]['points'] = users[str(target_id)].get('points', 0.0) + reward
    users[str(target_id)]['last_sign_date'] = time.strftime('%Y-%m-%d')
    save_users()
    stats=get_user_stats(target_id)
    update.message.reply_text(f"✅ 强制签到成功！用户 {target_id} 获得 {reward:.2f} 积分，当前积分 {stats['points']:.2f}")

def clear_all_signin(update, context):
    uid=update.effective_user.id
    if uid not in ADMIN_IDS: update.message.reply_text("❌ 您没有管理员权限"); return
    for uid_key in users:
        users[uid_key]['last_sign_date'] = ''
    save_users()
    update.message.reply_text("⚠️ 已清空所有用户的签到日期！")

def list_users(update, context):
    uid=update.effective_user.id
    if uid not in ADMIN_IDS: update.message.reply_text("❌ 您没有管理员权限"); return
    if not users: update.message.reply_text("📭 暂无用户数据"); return
    msg="📊 用户列表：\n"
    for uid_key, data in users.items():
        msg += f"ID: `{uid_key}`，积分: {data.get('points', 0):.2f}\n"
    update.message.reply_text(msg, parse_mode='Markdown')

# ===== sfz 对话 =====
SFZ_NAME, SFZ_ID, SFZ_NATION, SFZ_ADDR, SFZ_EXPIRY, SFZ_PHOTO = range(6)
def sfz_start(update, context):
    update.message.reply_text("📝 开始生成身份证（标准模板），请输入姓名：")
    return SFZ_NAME
def sfz_name(update, context):
    context.user_data['name']=update.message.text.strip()
    update.message.reply_text("请输入18位身份证号：")
    return SFZ_ID
def sfz_id(update, context):
    id_card=update.message.text.strip().upper()
    if len(id_card)!=18 or not (id_card[:17].isdigit() and id_card[-1] in '0123456789X'):
        update.message.reply_text("格式错误，重新输入：")
        return SFZ_ID
    context.user_data['id_number']=id_card
    update.message.reply_text("请输入民族：")
    return SFZ_NATION
def sfz_nation(update, context):
    context.user_data['nation']=update.message.text.strip()
    update.message.reply_text("请输入地址：")
    return SFZ_ADDR
def sfz_address(update, context):
    context.user_data['address']=update.message.text.strip()
    update.message.reply_text("请输入有效期（如 2020.01.01-2030.01.01）：")
    return SFZ_EXPIRY
def sfz_expiry(update, context):
    context.user_data['expiry']=update.message.text.strip()
    update.message.reply_text("请发送一张本人照片：")
    return SFZ_PHOTO
def sfz_photo(update, context):
    if not update.message.photo:
        update.message.reply_text("请发送图片。")
        return SFZ_PHOTO
    photo=update.message.photo[-1]; file=photo.get_file()
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        file.download(tmp.name)
        photo_path=tmp.name
    data=context.user_data
    if not all(k in data for k in ['name','id_number','nation','address','expiry']):
        update.message.reply_text("信息不完整，请重新 /sfz")
        return ConversationHandler.END
    update.message.reply_text("⏳ 生成中...")
    try:
        # 需要导入 generate_id_card_sync
        img, pdf = generate_id_card_sync(data['name'], data['id_number'], data['nation'], data['address'], data['expiry'], photo_path)
        update.message.reply_photo(photo=img, caption=f"✅ {data['name']} 的身份证")
        context.bot.send_document(chat_id=update.effective_chat.id, document=pdf, filename=f"{data['name']}_身份证.pdf")
    except Exception as e:
        update.message.reply_text(f"❌ 失败：{e}")
    finally:
        if os.path.exists(photo_path): os.remove(photo_path)
        context.user_data.clear()
    return ConversationHandler.END

# ===== plc 对话 =====
PLC_NAME, PLC_ID, PLC_ADDR_CONFIRM, PLC_ADDR_MANUAL, PLC_PHOTO = range(10,15)
def plc_start(update, context):
    update.message.reply_text("📝 开始生成身份证（PLC模板），请输入姓名：")
    return PLC_NAME
def plc_name(update, context):
    context.user_data['name']=update.message.text.strip()
    update.message.reply_text("请输入18位身份证号：")
    return PLC_ID
def plc_id(update, context):
    id_card=update.message.text.strip().upper()
    if len(id_card)!=18 or not (id_card[:17].isdigit() and id_card[-1] in '0123456789X'):
        update.message.reply_text("格式错误，重新输入：")
        return PLC_ID
    context.user_data['id_number']=id_card
    address=get_address_from_idcard(id_card)
    if address:
        context.user_data['auto_addr']=address
        keyboard=[[InlineKeyboardButton("✅ 是，使用此地址", callback_data="plc_addr_yes")],[InlineKeyboardButton("❌ 否，手动输入", callback_data="plc_addr_no")]]
        update.message.reply_text(f"✅ 自动匹配到地址：{address}\n请选择是否使用此地址：", reply_markup=InlineKeyboardMarkup(keyboard))
        return PLC_ADDR_CONFIRM
    else:
        update.message.reply_text("⚠️ 无法自动匹配地址，请手动输入详细地址：")
        return PLC_ADDR_MANUAL
def plc_addr_confirm_callback(update, context):
    query=update.callback_query; query.answer()
    if query.data=="plc_addr_yes":
        address=context.user_data.get('auto_addr')
        if address:
            context.user_data['address']=address
            query.edit_message_text(f"✅ 已使用地址：{address}\n请发送一张本人照片：")
            return PLC_PHOTO
        else:
            query.edit_message_text("未找到地址，请手动输入：")
            return PLC_ADDR_MANUAL
    elif query.data=="plc_addr_no":
        query.edit_message_text("请输入详细地址（手动输入）：")
        return PLC_ADDR_MANUAL
def plc_addr_manual(update, context):
    address=update.message.text.strip()
    if not address:
        update.message.reply_text("地址不能为空，请重新输入：")
        return PLC_ADDR_MANUAL
    context.user_data['address']=address
    update.message.reply_text("请发送一张本人照片：")
    return PLC_PHOTO
def plc_photo(update, context):
    if not update.message.photo:
        update.message.reply_text("请发送图片。")
        return PLC_PHOTO
    photo=update.message.photo[-1]; file=photo.get_file()
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        file.download(tmp.name)
        photo_path=tmp.name
    data=context.user_data
    if not all(k in data for k in ['name','id_number','address']):
        update.message.reply_text("信息不完整，请重新 /plc")
        return ConversationHandler.END
    update.message.reply_text("⏳ 生成中...")
    try:
        img, pdf = generate_plc_sync(data['name'], data['id_number'], data['address'], photo_path)
        update.message.reply_photo(photo=img, caption=f"✅ {data['name']} 的身份证（PLC模板）")
        context.bot.send_document(chat_id=update.effective_chat.id, document=pdf, filename=f"{data['name']}_身份证_PLC.pdf")
    except FileNotFoundError as e:
        update.message.reply_text(f"❌ 文件缺失：{e}\n请确保 plc/ 目录下有 mb.jpg 和 10.ttf")
    except Exception as e:
        update.message.reply_text(f"❌ 生成失败：{e}")
    finally:
        if os.path.exists(photo_path): os.remove(photo_path)
        context.user_data.clear()
    return ConversationHandler.END

# ===== 主程序 =====
def main():
    global bot
    updater=Updater(BOT_TOKEN, request_kwargs={'read_timeout':60,'connect_timeout':30})
    bot=updater.bot
    dp=updater.dispatcher

    # 普通命令
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("hainansf", hainansf))
    dp.add_handler(CommandHandler("balance", balance))
    dp.add_handler(CommandHandler("cancel", cancel))
    dp.add_handler(CommandHandler("signin", signin))
    dp.add_handler(CommandHandler("givepoint", givepoint))
    dp.add_handler(CommandHandler("reset_signin", reset_signin))
    dp.add_handler(CommandHandler("force_signin", force_signin))
    dp.add_handler(CommandHandler("clear_all_signin", clear_all_signin))
    dp.add_handler(CommandHandler("users", list_users))

    # 广西查询对话（自动注册流程）
    gx_conv = ConversationHandler(
        entry_points=[CommandHandler('gxquery', gxquery_start)],
        states={
            WAITING_PHONE: [MessageHandler(Filters.text & ~Filters.command, gx_wait_phone)],
            WAITING_CAPTCHA: [MessageHandler(Filters.text & ~Filters.command, gx_wait_captcha)],
            WAITING_SMS: [MessageHandler(Filters.text & ~Filters.command, gx_wait_sms)],
        },
        fallbacks=[CommandHandler('cancel', gxquery_cancel)],
    )
    dp.add_handler(gx_conv)

    # 充值对话
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('recharge', recharge_start)],
        states={1: [MessageHandler(Filters.text & ~Filters.command, recharge_amount)]},
        fallbacks=[CommandHandler('cancel', cancel)]
    ))

    # sfz 对话
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('sfz', sfz_start)],
        states={
            SFZ_NAME: [MessageHandler(Filters.text & ~Filters.command, sfz_name)],
            SFZ_ID: [MessageHandler(Filters.text & ~Filters.command, sfz_id)],
            SFZ_NATION: [MessageHandler(Filters.text & ~Filters.command, sfz_nation)],
            SFZ_ADDR: [MessageHandler(Filters.text & ~Filters.command, sfz_address)],
            SFZ_EXPIRY: [MessageHandler(Filters.text & ~Filters.command, sfz_expiry)],
            SFZ_PHOTO: [MessageHandler(Filters.photo, sfz_photo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    ))

    # plc 对话
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('plc', plc_start)],
        states={
            PLC_NAME: [MessageHandler(Filters.text & ~Filters.command, plc_name)],
            PLC_ID: [MessageHandler(Filters.text & ~Filters.command, plc_id)],
            PLC_ADDR_CONFIRM: [CallbackQueryHandler(plc_addr_confirm_callback, pattern='^(plc_addr_yes|plc_addr_no)$')],
            PLC_ADDR_MANUAL: [MessageHandler(Filters.text & ~Filters.command, plc_addr_manual)],
            PLC_PHOTO: [MessageHandler(Filters.photo, plc_photo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    ))

    threading.Thread(target=check_orders, daemon=True).start()
    threading.Thread(target=run_flask, daemon=True).start()

    print("🤖 机器人已启动（广西自动注册查询）")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
