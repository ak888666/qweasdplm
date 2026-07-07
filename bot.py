#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
print("===== Bot 最终版（广西修复-参考源码重写）=====")

import os, time, json, io, tempfile, requests, urllib3, logging, re, random, threading, hashlib, hmac, urllib.parse, base64
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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

# ===== JSON存储 =====
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
        users[str(user_id)] = {"points":0.0, "total_recharge":0.0, "invites":0, "last_sign_date":"", "created_at":time.strftime('%Y-%m-%d %H:%M:%S')}
        save_users()

def get_user_stats(user_id):
    ensure_user(user_id)
    d = users[str(user_id)]
    return {'points': d.get('points',0.0), 'total_recharge': d.get('total_recharge',0.0), 'last_sign_date': d.get('last_sign_date','')}

# ===== SM4加密（广西） =====
SM4_KEY="CatsPK0WWWRRhjkw"
SboxTable=[0xd6,0x90,0xe9,0xfe,0xcc,0xe1,0x3d,0xb7,0x16,0xb6,0x14,0xc2,0x28,0xfb,0x2c,0x05,0x2b,0x67,0x9a,0x76,0x2a,0xbe,0x04,0xc3,0xaa,0x44,0x13,0x26,0x49,0x86,0x06,0x99,0x9c,0x42,0x50,0xf4,0x91,0xef,0x98,0x7a,0x33,0x54,0x0b,0x43,0xed,0xcf,0xac,0x62,0xe4,0xb3,0x1c,0xa9,0xc9,0x08,0xe8,0x95,0x80,0xdf,0x94,0xfa,0x75,0x8f,0x3f,0xa6,0x47,0x07,0xa7,0xfc,0xf3,0x73,0x17,0xba,0x83,0x59,0x3c,0x19,0xe6,0x85,0x4f,0xa8,0x68,0x6b,0x81,0xb2,0x71,0x64,0xda,0x8b,0xf8,0xeb,0x0f,0x4b,0x70,0x56,0x9d,0x35,0x1e,0x24,0x0e,0x5e,0x63,0x58,0xd1,0xa2,0x25,0x22,0x7c,0x3b,0x01,0x21,0x78,0x87,0xd4,0x00,0x46,0x57,0x9f,0xd3,0x27,0x52,0x4c,0x36,0x02,0xe7,0xa0,0xc4,0xc8,0x9e,0xea,0xbf,0x8a,0xd2,0x40,0xc7,0x38,0xb5,0xa3,0xf7,0xf2,0xce,0xf9,0x61,0x15,0xa1,0xe0,0xae,0x5d,0xa4,0x9b,0x34,0x1a,0x55,0xad,0x93,0x32,0x30,0xf5,0x8c,0xb1,0xe3,0x1d,0xf6,0xe2,0x2e,0x82,0x66,0xca,0x60,0xc0,0x29,0x23,0xab,0x0d,0x53,0x4e,0x6f,0xd5,0xdb,0x37,0x45,0xde,0xfd,0x8e,0x2f,0x03,0xff,0x6a,0x72,0x6d,0x6c,0x5b,0x51,0x8d,0x1b,0xaf,0x92,0xbb,0xdd,0xbc,0x7f,0x11,0xd9,0x5c,0x41,0x1f,0x10,0x5a,0xd8,0x0a,0xc1,0x31,0x88,0xa5,0xcd,0x7b,0xbd,0x2d,0x74,0xd0,0x12,0xb8,0xe5,0xb4,0xb0,0x89,0x69,0x97,0x4a,0x0c,0x96,0x77,0x7e,0x65,0xb9,0xf1,0x09,0xc5,0x6e,0xc6,0x84,0x18,0xf0,0x7d,0xec,0x3a,0xdc,0x4d,0x20,0x79,0xee,0x5f,0x3e,0xd7,0xcb,0x39,0x48]
FK=[0xa3b1bac6,0x56aa3350,0x677d9197,0xb27022dc]
CK=[0x00070e15,0x1c232a31,0x383f464d,0x545b6269,0x70777e85,0x8c939aa1,0xa8afb6bd,0xc4cbd2d9,0xe0e7eef5,0xfc030a11,0x181f262d,0x343b4249,0x50575e65,0x6c737a81,0x888f969d,0xa4abb2b9,0xc0c7ced5,0xdce3eaf1,0xf8ff060d,0x141b2229,0x30373e45,0x4c535a61,0x686f767d,0x848b9299,0xa0a7aeb5,0xbcc3cad1,0xd8dfe6ed,0xf4fb0209,0x10171e25,0x2c333a41,0x484f565d,0x646b7279]
def rotl(x,n): return ((x<<n)&0xffffffff)|(((x-0x100000000 if x&0x80000000 else x)>>(32-n))&0xffffffff)
def sm4_sbox(a): return (SboxTable[(a>>24)&0xFF]<<24)|(SboxTable[(a>>16)&0xFF]<<16)|(SboxTable[(a>>8)&0xFF]<<8)|SboxTable[a&0xFF]
def sm4_lt(ka): bb=sm4_sbox(ka); return bb^rotl(bb,2)^rotl(bb,10)^rotl(bb,18)^rotl(bb,24)
def sm4_calci_rk(ka): bb=sm4_sbox(ka); return bb^rotl(bb,13)^rotl(bb,23)
def sm4_f(x0,x1,x2,x3,rk): return x0^sm4_lt(x1^x2^x3^rk)
def pkcs7_pad(data:bytes, block_size=16): pad_len=block_size-(len(data)%block_size); return data+bytes([pad_len])*pad_len
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

# ===== 广西函数（完全参考源码重写） =====
GX_HEADERS_VERIFY = {
    "Host": "www.gxdlys.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.62(0x18003e37) NetType/4G Language/zh_CN",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "http://www.gxdlys.com/Wechat/User/Regist",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}

GX_HEADERS_LOGIN = {
    "Host": "www.gxdlys.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 14; zh-cn; 22041216C Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 XiaoMi/MiuiBrowser/19.8.550718",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "http://www.gxdlys.com",
    "Referer": "http://www.gxdlys.com/Wechat/Home/Login",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}

GX_HEADERS_QUERY = {
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 14; zh-cn; 22041216C Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 XiaoMi/MiuiBrowser/19.8.550718",
    "Referer": "http://www.gxdlys.com/Wechat/User/Regist"
}

GX_HEADERS_FILE = {
    "Host": "www.gxdlys.com",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 14; zh-cn; 22041216C Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 XiaoMi/MiuiBrowser/19.8.550718",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "x-miorigin": "s",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}

def gx_init_session():
    """初始化广西Session"""
    session = requests.Session()
    # 先访问首页获取基础Cookie
    try:
        session.get("http://www.gxdlys.com", timeout=10)
    except:
        pass
    return session

def gx_get_captcha(session):
    """获取验证码（参考源码）"""
    url = "http://www.gxdlys.com/Wechat/FaceDetect/GetVerifyCode"
    for attempt in range(3):
        try:
            response = session.get(url, headers=GX_HEADERS_VERIFY, timeout=15)
            if response.status_code == 200:
                result = response.json()
                if result.get("statusCode") == 200 and "data" in result:
                    uuid = result["data"].get("uuid")
                    img_b64 = result["data"].get("img")
                    if uuid and img_b64:
                        return True, img_b64, uuid
            time.sleep(1)
        except Exception as e:
            logger.error(f"获取验证码尝试{attempt+1}失败: {e}")
    return False, None, None

def gx_login(session, id_card):
    """登录（参考源码）"""
    enc_login = urllib.parse.quote(sm4_encrypt_ecb(id_card))
    enc_pwd = urllib.parse.quote(sm4_encrypt_ecb(GX_PASSWORD))
    data = f"loginName={enc_login}&password={enc_pwd}&wechatUid="
    try:
        response = session.post(
            "http://www.gxdlys.com/Wechat/Home/PostLogin",
            headers=GX_HEADERS_LOGIN,
            data=data,
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("statusCode") == 200 and result.get("info") == "登录成功":
                return True, "登录成功"
            else:
                return False, result.get("info", "登录失败")
        return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def gx_query_photo(session, name, id_card, uuid, code):
    """查询照片（参考源码）"""
    url = f"http://www.gxdlys.com/Wechat/FaceDetect/GetGAIDCardPhotoNew?idCard={id_card}&name={name}&uuid={uuid}&code={code}"
    try:
        response = session.get(url, headers=GX_HEADERS_QUERY, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get("statusCode") == 200:
                file_id = result.get("data", {}).get("item1")
                if file_id:
                    return True, file_id, None
                return False, None, "未获取到照片ID"
            else:
                return False, None, result.get("info", "查询失败")
        return False, None, f"HTTP {response.status_code}"
    except Exception as e:
        return False, None, str(e)

def gx_download_photo(session, file_id):
    """下载照片（参考源码）"""
    url = f"http://www.gxdlys.com/System/FileService/ShowFile?fileId={file_id}"
    try:
        response = session.get(url, headers=GX_HEADERS_FILE, timeout=30)
        if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
            return True, response.content
        return False, "下载失败"
    except Exception as e:
        return False, str(e)

def gx_send_sms(session, phone, captcha_code, uuid):
    data = {"phoneId": phone, "type": "10001", "IsEncryptPhoneId": "false", "verifyCode": captcha_code, "uuid": uuid}
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.62(0x18003e37) NetType/4G Language/zh_CN",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "http://www.gxdlys.com/Wechat/User/Regist"
    }
    try:
        r = session.post("http://www.gxdlys.com/System/SmsService/PostVerifyCode", data=data, headers=headers, timeout=30)
        if r.status_code == 200:
            res = r.json()
            return res.get("statusCode") == 200
        return False
    except:
        return False

def gx_register(session, phone, sms_code, captcha_code, real_name, id_card):
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
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.62(0x18003e37) NetType/4G Language/zh_CN",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "http://www.gxdlys.com/Wechat/User/Regist"
    }
    try:
        r = session.post("http://www.gxdlys.com/Wechat/User/RegistAdd", data=data, headers=headers, timeout=30)
        if r.status_code == 200:
            res = r.json()
            return res.get("statusCode") == 200, res.get("info", "")
        return False, str(r.status_code)
    except Exception as e:
        return False, str(e)

# ===== 身份证生成函数（完整保留，与之前相同） =====
# 由于篇幅，省略 HEADERS1, HEADERS2, query_id_card_sync, remove_white_background,
# load_issuing_authority_map, get_issuing_authority, format_address,
# generate_id_card_sync, load_area_map, AREA_MAP, get_address_from_idcard, generate_plc_sync
# 这些函数与之前完全相同，请从之前的版本复制

# ===== OkayPay =====
class OkayPay:
    def __init__(self,appid,token,api_url): self.appid=appid; self.token=token; self.api_url=api_url
    def _build_base(self,params):
        params={k:v for k,v in params.items() if k!='sign' and v is not None and v!=''}
        def flatten(obj,prefix=''):
            items={}
            if isinstance(obj,dict):
                for k,v in obj.items():
                    key=f"{prefix}.{k}" if prefix else k
                    if isinstance(v,dict): items.update(flatten(v,key))
                    else: items[key]=v
            else: items[prefix]=obj
            return items
        flat={}
        for k,v in params.items():
            if isinstance(v,dict): flat.update(flatten(v,k))
            elif isinstance(v,bool): flat[k]='true' if v else 'false'
            else: flat[k]=str(v)
        sorted_params=dict(sorted(flat.items()))
        base='&'.join([f"{k}={v}" for k,v in sorted_params.items()])
        return base
    def _sign(self,params):
        base=self._build_base(params)
        sign=hmac.new(self.token.encode('utf-8'), base.encode('utf-8'), hashlib.sha256).hexdigest().upper()
        return sign
    def _signed_params(self,params):
        nonce=''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',k=16))
        timestamp=int(time.time())
        full_params={'id':str(self.appid),'timestamp':timestamp,'nonce':nonce,**params}
        full_params['sign']=self._sign(full_params)
        return full_params
    def verify(self,data):
        if 'sign' not in data: return False
        in_sign=data['sign']; calc_sign=self._sign(data); return calc_sign==in_sign
    def pay_link(self,amount,unique_id):
        params={'amount':f"{amount:.2f}",'coin':'USDT','unique_id':unique_id,'name':'积分充值','callback_url':CALLBACK_URL,'return_url':CALLBACK_URL}
        signed=self._signed_params(params)
        try:
            resp=requests.post(self.api_url+'payLink', data=signed, headers={'Content-Type':'application/x-www-form-urlencoded'}, timeout=15, verify=False)
            if resp.status_code==200:
                result=resp.json()
                if result.get('status')=='success' and self.verify(result): return result
                else: return {'status':'error','msg':result.get('msg','未知错误')}
            else: return {'status':'error','msg':f'HTTP {resp.status_code}'}
        except Exception as e: return {'status':'error','msg':str(e)}
    def check_deposit(self,unique_id):
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
                            users[str(user_id)]['points']=users[str(user_id)].get('points',0.0)+points
                            users[str(user_id)]['total_recharge']=users[str(user_id)].get('total_recharge',0.0)+amount
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
        if not client.verify(data): return jsonify({'status':'success'}),200
        return jsonify({'status':'success'}),200
    except: return jsonify({'status':'success'}),200

def run_flask(): flask_app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# ===== Telegram命令 =====
WAITING_PHONE, WAITING_CAPTCHA, WAITING_SMS = range(100,103)

def start(update, context):
    uid=update.effective_user.id; ensure_user(uid); stats=get_user_stats(uid)
    update.message.reply_text(
        f"👤 用户：{update.effective_user.first_name or '用户'}\n🆔 ID：{uid}\n💎 积分：{stats['points']:.2f}\n🌟 签到得0.05分\n\n"
        f"命令：\n/hainansf 身份证 → 海南大头\n/sfz → 生成身份证\n/plc → PLC身份证\n/recharge → 充值\n/balance → 余额\n"
        f"/gxquery 姓名 身份证 → 广西照片（自动注册）\n/signin → 签到\n/givepoint 用户ID 积分 [备注] → 管理员赠送\n"
        f"/users → 用户列表（管理员）\n/reset_signin 用户ID → 重置签到\n/force_signin 用户ID → 强制签到\n"
        f"/clear_all_signin → 清空所有签到\n/cancel → 取消"
    )

def gxquery_start(update, context):
    uid=update.effective_user.id; args=context.args
    if len(args)<2:
        update.message.reply_text("❌ 格式：/gxquery <姓名> <身份证号>")
        return ConversationHandler.END
    name, id_card = args[0].strip(), args[1].strip()
    if len(id_card)!=18:
        update.message.reply_text("❌ 身份证18位")
        return ConversationHandler.END
    stats=get_user_stats(uid)
    if stats['points']<GX_QUERY_PRICE:
        update.message.reply_text(f"❌ 积分不足，需要 {GX_QUERY_PRICE:.2f}")
        return ConversationHandler.END
    users[str(uid)]['points']=users[str(uid)].get('points',0.0)-GX_QUERY_PRICE
    save_users()
    context.user_data['gx_name']=name
    context.user_data['gx_idcard']=id_card
    
    # 初始化Session（带预热）
    session = gx_init_session()
    context.user_data['gx_session']=session
    
    # 先尝试登录
    success, info = gx_login(session, id_card)
    if success:
        update.message.reply_text("⏳ 登录成功，正在获取验证码...")
        return gx_do_query(update, context)
    elif "未注册" in info or "不存在" in info:
        update.message.reply_text("⚠️ 该身份证未注册，请输入手机号：")
        return WAITING_PHONE
    else:
        users[str(uid)]['points']=users[str(uid)].get('points',0.0)+GX_QUERY_PRICE
        save_users()
        update.message.reply_text(f"❌ 登录失败: {info}\n已退还积分")
        return ConversationHandler.END

def gx_do_query(update, context):
    uid=update.effective_user.id
    session=context.user_data['gx_session']
    name=context.user_data['gx_name']
    id_card=context.user_data['gx_idcard']
    
    # 获取验证码
    success, img_b64, uuid = gx_get_captcha(session)
    if not success:
        users[str(uid)]['points']=users[str(uid)].get('points',0.0)+GX_QUERY_PRICE
        save_users()
        update.message.reply_text("❌ 获取验证码失败，已退还积分")
        return ConversationHandler.END
    
    context.user_data['gx_uuid'] = uuid
    img_bytes = base64.b64decode(img_b64)
    update.message.reply_photo(photo=io.BytesIO(img_bytes), caption="📷 请输入图形验证码：")
    return WAITING_CAPTCHA

def gx_wait_phone(update, context):
    phone=update.message.text.strip()
    if not phone or len(phone)<11:
        update.message.reply_text("❌ 请输入正确手机号：")
        return WAITING_PHONE
    context.user_data['gx_phone']=phone
    session=context.user_data['gx_session']
    success, img_b64, uuid = gx_get_captcha(session)
    if not success:
        uid=update.effective_user.id
        users[str(uid)]['points']=users[str(uid)].get('points',0.0)+GX_QUERY_PRICE
        save_users()
        update.message.reply_text("❌ 获取验证码失败，已退还积分")
        return ConversationHandler.END
    context.user_data['gx_uuid']=uuid
    img_bytes=base64.b64decode(img_b64)
    update.message.reply_photo(photo=io.BytesIO(img_bytes), caption="📷 请输入图形验证码：")
    return WAITING_CAPTCHA

def gx_wait_captcha(update, context):
    captcha=update.message.text.strip().upper()
    if not captcha:
        update.message.reply_text("请输入验证码：")
        return WAITING_CAPTCHA
    context.user_data['gx_captcha']=captcha
    session=context.user_data['gx_session']
    name=context.user_data['gx_name']
    id_card=context.user_data['gx_idcard']
    uuid=context.user_data.get('gx_uuid')
    
    # 查询照片
    success, file_id, err = gx_query_photo(session, name, id_card, uuid, captcha)
    if success:
        # 下载照片
        dl_success, content = gx_download_photo(session, file_id)
        if dl_success:
            update.message.reply_photo(photo=io.BytesIO(content), caption=f"✅ {name} 照片\n消耗 {GX_QUERY_PRICE:.2f} 积分")
            context.user_data.clear()
            return ConversationHandler.END
        else:
            users[str(update.effective_user.id)]['points']=users[str(update.effective_user.id)].get('points',0.0)+GX_QUERY_PRICE
            save_users()
            update.message.reply_text(f"❌ 下载照片失败: {content}\n已退还积分")
            return ConversationHandler.END
    else:
        # 查询失败，可能是未注册或验证码错误
        if "未注册" in err or "不存在" in err:
            # 进入注册流程
            update.message.reply_text("⚠️ 该身份证未注册，请输入手机号：")
            return WAITING_PHONE
        else:
            uid=update.effective_user.id
            users[str(uid)]['points']=users[str(uid)].get('points',0.0)+GX_QUERY_PRICE
            save_users()
            update.message.reply_text(f"❌ 查询失败: {err}\n已退还积分")
            return ConversationHandler.END

def gx_wait_sms(update, context):
    sms=update.message.text.strip()
    if not sms:
        update.message.reply_text("请输入短信验证码：")
        return WAITING_SMS
    session=context.user_data['gx_session']
    name=context.user_data['gx_name']
    id_card=context.user_data['gx_idcard']
    phone=context.user_data['gx_phone']
    captcha=context.user_data['gx_captcha']
    uuid=context.user_data.get('gx_uuid', '')
    
    update.message.reply_text("⏳ 注册中...")
    success, info = gx_register(session, phone, sms, captcha, name, id_card)
    if success:
        update.message.reply_text("✅ 注册成功，正在登录查询...")
        # 登录
        login_ok, login_info = gx_login(session, id_card)
        if login_ok:
            # 重新获取验证码查询
            success2, img_b64, uuid2 = gx_get_captcha(session)
            if success2:
                context.user_data['gx_uuid'] = uuid2
                img_bytes = base64.b64decode(img_b64)
                update.message.reply_photo(photo=io.BytesIO(img_bytes), caption="📷 请再次输入图形验证码：")
                return WAITING_CAPTCHA
            else:
                uid=update.effective_user.id
                users[str(uid)]['points']=users[str(uid)].get('points',0.0)+GX_QUERY_PRICE
                save_users()
                update.message.reply_text("❌ 获取验证码失败，已退还积分")
                return ConversationHandler.END
        else:
            uid=update.effective_user.id
            users[str(uid)]['points']=users[str(uid)].get('points',0.0)+GX_QUERY_PRICE
            save_users()
            update.message.reply_text(f"❌ 登录失败: {login_info}\n已退还积分")
            return ConversationHandler.END
    else:
        uid=update.effective_user.id
        users[str(uid)]['points']=users[str(uid)].get('points',0.0)+GX_QUERY_PRICE
        save_users()
        update.message.reply_text(f"❌ 注册失败: {info}\n已退还积分")
        return ConversationHandler.END

def gxquery_cancel(update, context):
    uid=update.effective_user.id
    if 'gx_session' in context.user_data:
        users[str(uid)]['points']=users[str(uid)].get('points',0.0)+GX_QUERY_PRICE
        save_users()
    context.user_data.clear()
    update.message.reply_text("已取消，积分已退还")
    return ConversationHandler.END

# ===== 其他命令（完整保留） =====
def hainansf(update, context):
    args=context.args
    if not args: update.message.reply_text("❌ /hainansf 身份证号"); return
    id_card=args[0].strip()
    if len(id_card)!=18: update.message.reply_text("❌ 身份证18位"); return
    update.message.reply_text("⏳ 查询中...")
    success,result=query_id_card_sync(id_card)
    if success:
        context.bot.send_document(chat_id=update.effective_chat.id, document=io.BytesIO(result), filename=f"{id_card}.pdf", caption="✅ 查询成功")
    else:
        update.message.reply_text(f"❌ 失败: {result}")

def cancel(update, context):
    update.message.reply_text("已取消"); context.user_data.clear(); return ConversationHandler.END

def recharge_start(update, context):
    uid=update.effective_user.id; ensure_user(uid); stats=get_user_stats(uid)
    update.message.reply_text(f"💰 当前积分 {stats['points']:.2f}\n请输入 USDT 金额：")
    return 1

def recharge_amount(update, context):
    uid=update.effective_user.id
    try: amt=float(re.sub(r'[^\d.]','',update.message.text))
    except: update.message.reply_text("❌ 请输入数字"); return 1
    if amt<=0: update.message.reply_text("金额需大于0"); return 1
    points=amt*POINTS_RATE
    unique_id=f"ORDER_{int(time.time())}_{uid}_{random.randint(1000,9999)}"
    resp=client.pay_link(amt, unique_id)
    if not resp or resp.get('status')!='success':
        update.message.reply_text(f"❌ 创建订单失败: {resp.get('msg','未知错误')}")
        return ConversationHandler.END
    order_id=resp['data']['order_id']; pay_url=resp['data']['pay_url']
    orders[unique_id]={'user_id':uid,'amount':amt,'order_id':order_id,'status':'pending','timestamp':time.time()}
    keyboard=[[InlineKeyboardButton("💳 去支付", url=pay_url)]]
    update.message.reply_text(f"✅ 订单已创建\n订单号: {order_id}\n金额: {amt:.2f} USDT → {points:.2f} 积分\n点击按钮支付", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

def balance(update, context):
    stats=get_user_stats(update.effective_user.id)
    update.message.reply_text(f"📊 积分: {stats['points']:.2f}\n累计充值: {stats['total_recharge']:.2f} USDT")

def signin(update, context):
    uid=update.effective_user.id; ensure_user(uid)
    today=time.strftime('%Y-%m-%d')
    if users[str(uid)].get('last_sign_date','')==today:
        update.message.reply_text("❌ 今天已签到")
        return
    users[str(uid)]['points']=users[str(uid)].get('points',0.0)+0.05
    users[str(uid)]['last_sign_date']=today
    save_users()
    stats=get_user_stats(uid)
    update.message.reply_text(f"✅ 签到成功！+0.05 积分，当前 {stats['points']:.2f}")

def givepoint(update, context):
    uid=update.effective_user.id
    if uid not in ADMIN_IDS: update.message.reply_text("❌ 无权限"); return
    args=context.args
    if len(args)<2: update.message.reply_text("❌ /givepoint <用户ID> <积分> [备注]"); return
    try: target_id=int(args[0]); amount=float(args[1])
    except: update.message.reply_text("❌ 参数错误"); return
    ensure_user(target_id)
    users[str(target_id)]['points']=users[str(target_id)].get('points',0.0)+amount
    save_users()
    stats=get_user_stats(target_id)
    update.message.reply_text(f"✅ 已向 {target_id} 赠送 {amount:.2f} 积分，当前 {stats['points']:.2f}")

def reset_signin(update, context):
    uid=update.effective_user.id
    if uid not in ADMIN_IDS: return
    args=context.args
    if not args: return
    try: target_id=int(args[0])
    except: return
    ensure_user(target_id)
    users[str(target_id)]['last_sign_date']=''
    save_users()
    update.message.reply_text(f"✅ 已重置 {target_id} 签到")

def force_signin(update, context):
    uid=update.effective_user.id
    if uid not in ADMIN_IDS: return
    args=context.args
    if not args: return
    try: target_id=int(args[0])
    except: return
    ensure_user(target_id)
    users[str(target_id)]['last_sign_date']=''
    users[str(target_id)]['points']=users[str(target_id)].get('points',0.0)+0.05
    users[str(target_id)]['last_sign_date']=time.strftime('%Y-%m-%d')
    save_users()
    stats=get_user_stats(target_id)
    update.message.reply_text(f"✅ 强制签到成功，{target_id} 当前积分 {stats['points']:.2f}")

def clear_all_signin(update, context):
    uid=update.effective_user.id
    if uid not in ADMIN_IDS: return
    for k in users: users[k]['last_sign_date']=''
    save_users()
    update.message.reply_text("✅ 已清空所有签到日期")

def list_users(update, context):
    uid=update.effective_user.id
    if uid not in ADMIN_IDS: return
    if not users: update.message.reply_text("📭 无用户")
    else:
        msg="📊 用户列表：\n"
        for k,v in users.items():
            msg+=f"ID: `{k}`，积分: {v.get('points',0):.2f}\n"
        update.message.reply_text(msg, parse_mode='Markdown')

# ===== sfz/plc对话（完整保留） =====
SFZ_NAME,SFZ_ID,SFZ_NATION,SFZ_ADDR,SFZ_EXPIRY,SFZ_PHOTO=range(6)
def sfz_start(update,context): update.message.reply_text("请输入姓名："); return SFZ_NAME
def sfz_name(update,context):
    context.user_data['name']=update.message.text.strip()
    update.message.reply_text("请输入18位身份证号："); return SFZ_ID
def sfz_id(update,context):
    id_card=update.message.text.strip().upper()
    if len(id_card)!=18 or not (id_card[:17].isdigit() and id_card[-1] in '0123456789X'):
        update.message.reply_text("格式错误，重新输入："); return SFZ_ID
    context.user_data['id_number']=id_card
    update.message.reply_text("请输入民族："); return SFZ_NATION
def sfz_nation(update,context):
    context.user_data['nation']=update.message.text.strip()
    update.message.reply_text("请输入地址："); return SFZ_ADDR
def sfz_address(update,context):
    context.user_data['address']=update.message.text.strip()
    update.message.reply_text("请输入有效期（如 2020.01.01-2030.01.01）："); return SFZ_EXPIRY
def sfz_expiry(update,context):
    context.user_data['expiry']=update.message.text.strip()
    update.message.reply_text("请发送本人照片："); return SFZ_PHOTO
def sfz_photo(update,context):
    if not update.message.photo:
        update.message.reply_text("请发送图片"); return SFZ_PHOTO
    photo=update.message.photo[-1]; file=photo.get_file()
    with tempfile.NamedTemporaryFile(suffix='.jpg',delete=False) as tmp:
        file.download(tmp.name); photo_path=tmp.name
    data=context.user_data
    if not all(k in data for k in ['name','id_number','nation','address','expiry']):
        update.message.reply_text("信息不完整，重新 /sfz"); return ConversationHandler.END
    update.message.reply_text("⏳ 生成中...")
    try:
        img,pdf=generate_id_card_sync(data['name'],data['id_number'],data['nation'],data['address'],data['expiry'],photo_path)
        update.message.reply_photo(photo=img,caption=f"✅ {data['name']} 的身份证")
        context.bot.send_document(chat_id=update.effective_chat.id, document=pdf, filename=f"{data['name']}_身份证.pdf")
    except Exception as e:
        update.message.reply_text(f"❌ 失败: {e}")
    finally:
        if os.path.exists(photo_path): os.remove(photo_path)
        context.user_data.clear()
    return ConversationHandler.END

PLC_NAME,PLC_ID,PLC_ADDR_CONFIRM,PLC_ADDR_MANUAL,PLC_PHOTO=range(10,15)
def plc_start(update,context):
    update.message.reply_text("请输入姓名："); return PLC_NAME
def plc_name(update,context):
    context.user_data['name']=update.message.text.strip()
    update.message.reply_text("请输入18位身份证号："); return PLC_ID
def plc_id(update,context):
    id_card=update.message.text.strip().upper()
    if len(id_card)!=18 or not (id_card[:17].isdigit() and id_card[-1] in '0123456789X'):
        update.message.reply_text("格式错误，重新输入："); return PLC_ID
    context.user_data['id_number']=id_card
    address=get_address_from_idcard(id_card)
    if address:
        context.user_data['auto_addr']=address
        keyboard=[[InlineKeyboardButton("✅ 使用", callback_data="plc_addr_yes")],[InlineKeyboardButton("❌ 手动", callback_data="plc_addr_no")]]
        update.message.reply_text(f"✅ 匹配到地址：{address}\n是否使用？", reply_markup=InlineKeyboardMarkup(keyboard))
        return PLC_ADDR_CONFIRM
    else:
        update.message.reply_text("请手动输入地址：")
        return PLC_ADDR_MANUAL
def plc_addr_confirm_callback(update,context):
    query=update.callback_query; query.answer()
    if query.data=="plc_addr_yes":
        address=context.user_data.get('auto_addr')
        if address:
            context.user_data['address']=address
            query.edit_message_text(f"✅ 已使用：{address}\n请发送照片")
            return PLC_PHOTO
        else:
            query.edit_message_text("未找到，请输入地址")
            return PLC_ADDR_MANUAL
    else:
        query.edit_message_text("请输入地址：")
        return PLC_ADDR_MANUAL
def plc_addr_manual(update,context):
    addr=update.message.text.strip()
    if not addr:
        update.message.reply_text("地址不能为空")
        return PLC_ADDR_MANUAL
    context.user_data['address']=addr
    update.message.reply_text("请发送照片")
    return PLC_PHOTO
def plc_photo(update,context):
    if not update.message.photo:
        update.message.reply_text("请发送图片")
        return PLC_PHOTO
    photo=update.message.photo[-1]; file=photo.get_file()
    with tempfile.NamedTemporaryFile(suffix='.jpg',delete=False) as tmp:
        file.download(tmp.name); photo_path=tmp.name
    data=context.user_data
    if not all(k in data for k in ['name','id_number','address']):
        update.message.reply_text("信息不完整，重新 /plc")
        return ConversationHandler.END
    update.message.reply_text("⏳ 生成中...")
    try:
        img,pdf=generate_plc_sync(data['name'],data['id_number'],data['address'],photo_path)
        update.message.reply_photo(photo=img,caption=f"✅ {data['name']} 的PLC身份证")
        context.bot.send_document(chat_id=update.effective_chat.id, document=pdf, filename=f"{data['name']}_身份证_PLC.pdf")
    except FileNotFoundError as e:
        update.message.reply_text(f"❌ 文件缺失：{e}\n请确保 plc/ 目录下有 mb.jpg 和 10.ttf")
    except Exception as e:
        update.message.reply_text(f"❌ 失败: {e}")
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

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('gxquery', gxquery_start)],
        states={
            WAITING_PHONE: [MessageHandler(Filters.text & ~Filters.command, gx_wait_phone)],
            WAITING_CAPTCHA: [MessageHandler(Filters.text & ~Filters.command, gx_wait_captcha)],
            WAITING_SMS: [MessageHandler(Filters.text & ~Filters.command, gx_wait_sms)],
        },
        fallbacks=[CommandHandler('cancel', gxquery_cancel)]
    ))

    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('recharge', recharge_start)],
        states={1: [MessageHandler(Filters.text & ~Filters.command, recharge_amount)]},
        fallbacks=[CommandHandler('cancel', cancel)]
    ))

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

    print("🤖 机器人已启动（最终版-参考源码修复）")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
