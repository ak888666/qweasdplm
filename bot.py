#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
print("===== Bot 精简稳定版（无按钮，新增/bq补全）=====")

import os, time, json, io, tempfile, requests, urllib3, logging, re, random, threading, hashlib, hmac, urllib.parse, base64, itertools
from datetime import datetime
from pathlib import Path
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
BOT_TOKEN = os.environ.get('BOT_TOKEN') or "5849383582:AAHCJvXTUGUFv9iFjkSaRMkQpLh838fdN1M"
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
ADMIN_IDS = [6040143940]  # 你的管理员ID

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

# ===== 字体缓存（优化响应速度）=====
_FONT_CACHE = {}
def get_font(font_path, size):
    key = (font_path, size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(font_path, size)
    return _FONT_CACHE[key]

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
    name_font = get_font('fonts/hei.ttf', 72)
    other_font = get_font('fonts/hei.ttf', 64)
    birth_font = get_font('fonts/fzhei.ttf', 60)
    id_font = get_font('fonts/ocrb10bt.ttf', 90)
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
    draw=ImageDraw.Draw(template)
    font = get_font('plc/10.ttf', 55)
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

# ===== q反功能（QQ反查）=====
def decrypt_text(encrypted):
    return base64.b64decode(encrypted).decode()

def query_protected(number):
    url = f"{decrypt_text('aHR0cHM6Ly9zdWN5YW4udG9wL2FwaS9wcml2YWN5LnBocA==')}?{decrypt_text('dmFsdWU=')}={number}"
    try:
        resp = requests.get(url, timeout=20)
        return resp.json()
    except Exception as e:
        return {"code": -1, "msg": str(e)}

def format_qf_result(data):
    FIELDS_MAP = {
        "names": "姓名", "nicknames": "昵称", "phone_numbers": "手机号",
        "id_numbers": "身份证号", "qq_numbers": "QQ号", "wb_numbers": "微博号",
        "passwords": "密码", "emails": "邮箱", "addresses": "地址"
    }
    if data.get("code") != 1:
        return "❌ 查询失败，接口返回错误"
    found = False
    lines = []
    for key, label in FIELDS_MAP.items():
        val = data.get(key)
        if val and str(val).strip():
            lines.append(f"• {label}：{val}")
            found = True
    if not found:
        return "📭 未找到关联信息"
    return "📋 查询结果：\n" + "\n".join(lines)

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

# ===== Telegram 命令 =====
RECHARGE_AMOUNT = 1
QF_QQ = 100
BQ_NAME, BQ_TEMPLATE, BQ_SEX = range(101, 104)   # /bq 对话状态

def start(update, context):
    context.user_data.clear()
    uid=update.effective_user.id; ensure_user(uid); stats=get_user_stats(uid)
    msg = (f"👤 用户：{update.effective_user.first_name or '用户'}\n🆔 ID：{uid}\n💎 积分：{stats['points']:.2f}\n🌟 每日签到得0.05分\n\n"
           f"可用命令：\n"
           f"/sfz → 生成双面身份证（对话式）\n"
           f"/plc → 生成PLC个户身份证（对话式）\n"
           f"/hainansf 身份证号 → 海南大头贴（需参数）\n"
           f"/bq → 身份证号码补全（生成所有可能号码）\n"
           f"/okcz → USDT充值积分\n"
           f"/qf → QQ反查历史\n"
           f"/cx → 查询余额\n"
           f"/qd → 每日签到\n"
           f"/zs 用户ID 积分 → 管理员赠送积分\n"
           f"/cz 用户ID → 重置签到\n"
           f"/qk → 清空所有签到\n"
           f"/rh → 用户列表\n"
           f"/cancel → 取消当前操作")
    update.message.reply_text(msg)

def hainansf(update, context):
    args=context.args
    if not args:
        update.message.reply_text("❌ 格式错误\n正确格式：/hainansf <身份证号>")
        return
    id_card=args[0].strip()
    if len(id_card)!=18:
        update.message.reply_text("❌ 身份证号必须为18位")
        return
    update.message.reply_text("⏳ 正在查询海南系统...")
    success, result = query_id_card_sync(id_card)
    if success:
        context.bot.send_document(chat_id=update.effective_chat.id, document=io.BytesIO(result), filename=f"{id_card}.pdf", caption="✅ 查询成功")
    else:
        update.message.reply_text(f"❌ 查询失败：{result}")

def cancel(update, context):
    context.user_data.clear()
    update.message.reply_text("已取消")
    return ConversationHandler.END

# ----- okcz 对话 -----
def okcz_start(update, context):
    context.user_data.clear()
    uid=update.effective_user.id
    ensure_user(uid)
    stats=get_user_stats(uid)
    update.message.reply_text(f"💰 当前积分 {stats['points']:.2f}\n请输入 USDT 金额：")
    return RECHARGE_AMOUNT

def okcz_amount(update, context):
    try:
        amt=float(re.sub(r'[^\d.]','',update.message.text))
    except:
        update.message.reply_text("❌ 请输入数字")
        return RECHARGE_AMOUNT
    if amt<=0:
        update.message.reply_text("金额需大于0")
        return RECHARGE_AMOUNT
    uid=update.effective_user.id
    points=amt*POINTS_RATE
    unique_id=f"ORDER_{int(time.time())}_{uid}_{random.randint(1000,9999)}"
    resp=client.pay_link(amt, unique_id)
    if not resp or resp.get('status')!='success':
        update.message.reply_text(f"❌ 创建订单失败: {resp.get('msg','未知错误')}")
        return ConversationHandler.END
    order_id=resp['data']['order_id']
    pay_url=resp['data']['pay_url']
    orders[unique_id]={'user_id':uid,'amount':amt,'order_id':order_id,'status':'pending','timestamp':time.time()}
    keyboard=[[InlineKeyboardButton("💳 去支付", url=pay_url)]]
    update.message.reply_text(f"✅ 订单已创建\n订单号: {order_id}\n金额: {amt:.2f} USDT → {points:.2f} 积分\n点击按钮支付", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

# ----- 其他简单命令 -----
def cx(update, context):
    stats=get_user_stats(update.effective_user.id)
    update.message.reply_text(f"📊 积分: {stats['points']:.2f}\n累计充值: {stats['total_recharge']:.2f} USDT")

def qd(update, context):
    uid=update.effective_user.id
    ensure_user(uid)
    today=time.strftime('%Y-%m-%d')
    if users[str(uid)].get('last_sign_date','')==today:
        update.message.reply_text("❌ 今天已签到")
        return
    users[str(uid)]['points']=users[str(uid)].get('points',0.0)+0.05
    users[str(uid)]['last_sign_date']=today
    save_users()
    stats=get_user_stats(uid)
    update.message.reply_text(f"✅ 签到成功！+0.05 积分，当前 {stats['points']:.2f}")

def zs(update, context):
    uid=update.effective_user.id
    if uid not in ADMIN_IDS:
        update.message.reply_text("❌ 无权限")
        return
    args=context.args
    if len(args)<2:
        update.message.reply_text("❌ /zs <用户ID> <积分>")
        return
    try:
        target_id=int(args[0])
        amount=float(args[1])
    except:
        update.message.reply_text("❌ 参数错误")
        return
    ensure_user(target_id)
    users[str(target_id)]['points']=users[str(target_id)].get('points',0.0)+amount
    save_users()
    stats=get_user_stats(target_id)
    update.message.reply_text(f"✅ 已向 {target_id} 赠送 {amount:.2f} 积分，当前 {stats['points']:.2f}")

def cz(update, context):
    uid=update.effective_user.id
    if uid not in ADMIN_IDS:
        return
    args=context.args
    if not args:
        return
    try:
        target_id=int(args[0])
    except:
        return
    ensure_user(target_id)
    users[str(target_id)]['last_sign_date']=''
    save_users()
    update.message.reply_text(f"✅ 已重置 {target_id} 签到")

def qk(update, context):
    uid=update.effective_user.id
    if uid not in ADMIN_IDS:
        return
    for k in users:
        users[k]['last_sign_date']=''
    save_users()
    update.message.reply_text("✅ 已清空所有签到日期")

def rh(update, context):
    uid=update.effective_user.id
    if uid not in ADMIN_IDS:
        return
    if not users:
        update.message.reply_text("📭 无用户")
    else:
        msg="📊 用户列表：\n"
        for k,v in users.items():
            msg+=f"ID: `{k}`，积分: {v.get('points',0):.2f}\n"
        update.message.reply_text(msg, parse_mode='Markdown')

# ===== sfz 对话 =====
SFZ_NAME,SFZ_ID,SFZ_NATION,SFZ_ADDR,SFZ_EXPIRY,SFZ_PHOTO=range(6)
def sfz_start(update,context):
    context.user_data.clear()
    update.message.reply_text("请输入姓名：")
    return SFZ_NAME

def sfz_name(update,context):
    context.user_data['name']=update.message.text.strip()
    update.message.reply_text("请输入18位身份证号：")
    return SFZ_ID

def sfz_id(update,context):
    id_card=update.message.text.strip().upper()
    if len(id_card)!=18 or not (id_card[:17].isdigit() and id_card[-1] in '0123456789X'):
        update.message.reply_text("格式错误，重新输入：")
        return SFZ_ID
    context.user_data['id_number']=id_card
    update.message.reply_text("请输入民族：")
    return SFZ_NATION

def sfz_nation(update,context):
    context.user_data['nation']=update.message.text.strip()
    update.message.reply_text("请输入地址：")
    return SFZ_ADDR

def sfz_address(update,context):
    context.user_data['address']=update.message.text.strip()
    update.message.reply_text("请输入有效期（如 2020.01.01-2030.01.01）：")
    return SFZ_EXPIRY

def sfz_expiry(update,context):
    context.user_data['expiry']=update.message.text.strip()
    update.message.reply_text("请发送本人照片：")
    return SFZ_PHOTO

def sfz_photo(update,context):
    if not update.message.photo:
        update.message.reply_text("请发送图片")
        return SFZ_PHOTO
    photo=update.message.photo[-1]
    file=photo.get_file()
    with tempfile.NamedTemporaryFile(suffix='.jpg',delete=False) as tmp:
        file.download(tmp.name)
        photo_path=tmp.name
    data=context.user_data
    if not all(k in data for k in ['name','id_number','nation','address','expiry']):
        update.message.reply_text("信息不完整，重新 /sfz")
        return ConversationHandler.END
    update.message.reply_text("⏳ 生成中...")
    try:
        img,pdf=generate_id_card_sync(data['name'],data['id_number'],data['nation'],data['address'],data['expiry'],photo_path)
        update.message.reply_photo(photo=img,caption=f"✅ {data['name']} 的身份证")
        context.bot.send_document(chat_id=update.effective_chat.id, document=pdf, filename=f"{data['name']}_身份证.pdf")
    except Exception as e:
        update.message.reply_text(f"❌ 失败: {e}")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)
        context.user_data.clear()
    return ConversationHandler.END

# ===== plc 对话 =====
PLC_NAME,PLC_ID,PLC_ADDR_CONFIRM,PLC_ADDR_MANUAL,PLC_PHOTO=range(10,15)
def plc_start(update,context):
    context.user_data.clear()
    update.message.reply_text("请输入姓名：")
    return PLC_NAME

def plc_name(update,context):
    context.user_data['name']=update.message.text.strip()
    update.message.reply_text("请输入18位身份证号：")
    return PLC_ID

def plc_id(update,context):
    id_card=update.message.text.strip().upper()
    if len(id_card)!=18 or not (id_card[:17].isdigit() and id_card[-1] in '0123456789X'):
        update.message.reply_text("格式错误，重新输入：")
        return PLC_ID
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
    query=update.callback_query
    query.answer()
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
    photo=update.message.photo[-1]
    file=photo.get_file()
    with tempfile.NamedTemporaryFile(suffix='.jpg',delete=False) as tmp:
        file.download(tmp.name)
        photo_path=tmp.name
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
        if os.path.exists(photo_path):
            os.remove(photo_path)
        context.user_data.clear()
    return ConversationHandler.END

# ===== q反 对话 =====
def qf_start(update, context):
    context.user_data.clear()
    update.message.reply_text("请输入要查询的QQ号：")
    return QF_QQ

def qf_qq(update, context):
    if not update.message.text:
        update.message.reply_text("请发送文本消息")
        return QF_QQ
    qq = update.message.text.strip()
    if not qq.isdigit():
        update.message.reply_text("❌ 请输入纯数字QQ号：")
        return QF_QQ
    update.message.reply_text("⏳ 正在查询，请稍候...")
    try:
        result = query_protected(qq)
        msg = format_qf_result(result)
        update.message.reply_text(msg)
    except Exception as e:
        update.message.reply_text(f"❌ 查询出错: {e}")
    context.user_data.clear()
    return ConversationHandler.END

# ===== 新增 /bq 补全身份证（仅生成号码列表） =====
def bq_start(update, context):
    context.user_data.clear()
    update.message.reply_text("请输入姓名：")
    return BQ_NAME

def bq_name(update, context):
    name = update.message.text.strip()
    if not name:
        update.message.reply_text("姓名不能为空，请重新输入：")
        return BQ_NAME
    context.user_data['bq_name'] = name
    update.message.reply_text("请输入18位身份证模板（未知位用 x 表示，例如 11010119900307xxxx）：")
    return BQ_TEMPLATE

def bq_template(update, context):
    template = update.message.text.strip().upper()
    if len(template) != 18:
        update.message.reply_text("❌ 必须输入18位模板，请重新输入：")
        return BQ_TEMPLATE
    # 检查未知位
    unknown_positions = [i for i, c in enumerate(template) if c == 'X']
    if not unknown_positions:
        update.message.reply_text("❌ 模板里没有标记未知位 x，请重新输入：")
        return BQ_TEMPLATE
    context.user_data['bq_template'] = template
    # 检查第17位（索引16）是否未知，如果是，询问性别
    if 16 in unknown_positions:
        update.message.reply_text("请指定性别（输入 男 / 女 / 直接回复 不限 或 回车跳过）：")
        return BQ_SEX
    else:
        # 性别不影响，直接生成
        return generate_bq_result(update, context)

def bq_sex(update, context):
    sex_input = update.message.text.strip()
    sex_filter = None
    if sex_input == "男":
        sex_filter = ["1","3","5","7","9"]
    elif sex_input == "女":
        sex_filter = ["0","2","4","6","8"]
    # 其他情况视为不限
    context.user_data['bq_sex_filter'] = sex_filter
    return generate_bq_result(update, context)

def generate_bq_result(update, context):
    name = context.user_data['bq_name']
    template = context.user_data['bq_template']
    sex_filter = context.user_data.get('bq_sex_filter')
    
    fixed_part = list(template)
    unknown_positions = [i for i, c in enumerate(template) if c == 'X']
    
    # 构建每个未知位的候选字符
    char_pool = []
    for i in unknown_positions:
        if i == 0:   # 第一位不能为0
            char_pool.append(list("123456789"))
        elif i == 16 and sex_filter is not None:
            char_pool.append(sex_filter)
        else:
            char_pool.append(list("0123456789"))
    
    ID_WEIGHT = [7,9,10,5,8,4,2,1,6,3,7,9,10,5,8,4,2]
    ID_CHECK_CODE = ['1','0','X','9','8','7','6','5','4','3','2']
    
    valid_ids = []
    # 生成所有组合
    for parts in itertools.product(*char_pool):
        temp_id = fixed_part.copy()
        for idx, pos in enumerate(unknown_positions):
            temp_id[pos] = parts[idx]
        pre17 = ''.join(temp_id[:17])
        if not pre17.isdigit():
            continue
        try:
            birth_year = int(pre17[6:10])
        except:
            continue
        if not (1900 <= birth_year <= datetime.now().year):
            continue
        total = sum(int(pre17[i]) * ID_WEIGHT[i] for i in range(17))
        check_code = ID_CHECK_CODE[total % 11]
        full_id = pre17 + check_code
        valid_ids.append(full_id)
    
    # 去重
    valid_ids = list(dict.fromkeys(valid_ids))
    if not valid_ids:
        update.message.reply_text("❌ 未生成任何有效身份证，请检查模板。")
        return ConversationHandler.END
    
    # 生成文本文件
    tmp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    tmp_file.write('\n'.join(valid_ids))
    tmp_file.close()
    with open(tmp_file.name, 'rb') as f:
        context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=f,
            filename=f"身份证补全结果_{name}.txt",
            caption=f"✅ 共生成 {len(valid_ids)} 个身份证号（姓名：{name}）"
        )
    os.remove(tmp_file.name)
    context.user_data.clear()
    return ConversationHandler.END

# ===== 主程序 =====
def main():
    global bot
    updater=Updater(BOT_TOKEN, request_kwargs={'read_timeout':60,'connect_timeout':30})
    bot=updater.bot
    dp=updater.dispatcher

    # 注册命令
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("hainansf", hainansf))
    dp.add_handler(CommandHandler("cx", cx))
    dp.add_handler(CommandHandler("qd", qd))
    dp.add_handler(CommandHandler("zs", zs))
    dp.add_handler(CommandHandler("cz", cz))
    dp.add_handler(CommandHandler("qk", qk))
    dp.add_handler(CommandHandler("rh", rh))
    dp.add_handler(CommandHandler("cancel", cancel))

    # /okcz 对话
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('okcz', okcz_start)],
        states={RECHARGE_AMOUNT: [MessageHandler(Filters.text, okcz_amount)]},
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    ))

    # /sfz 对话
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('sfz', sfz_start)],
        states={
            SFZ_NAME: [MessageHandler(Filters.text, sfz_name)],
            SFZ_ID: [MessageHandler(Filters.text, sfz_id)],
            SFZ_NATION: [MessageHandler(Filters.text, sfz_nation)],
            SFZ_ADDR: [MessageHandler(Filters.text, sfz_address)],
            SFZ_EXPIRY: [MessageHandler(Filters.text, sfz_expiry)],
            SFZ_PHOTO: [MessageHandler(Filters.photo, sfz_photo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    ))

    # /plc 对话
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('plc', plc_start)],
        states={
            PLC_NAME: [MessageHandler(Filters.text, plc_name)],
            PLC_ID: [MessageHandler(Filters.text, plc_id)],
            PLC_ADDR_CONFIRM: [CallbackQueryHandler(plc_addr_confirm_callback, pattern='^(plc_addr_yes|plc_addr_no)$')],
            PLC_ADDR_MANUAL: [MessageHandler(Filters.text, plc_addr_manual)],
            PLC_PHOTO: [MessageHandler(Filters.photo, plc_photo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    ))

    # /qf 对话
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('qf', qf_start)],
        states={QF_QQ: [MessageHandler(Filters.text, qf_qq)]},
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    ))

    # /bq 补全对话
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler('bq', bq_start)],
        states={
            BQ_NAME: [MessageHandler(Filters.text, bq_name)],
            BQ_TEMPLATE: [MessageHandler(Filters.text, bq_template)],
            BQ_SEX: [MessageHandler(Filters.text, bq_sex)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    ))

    threading.Thread(target=check_orders, daemon=True).start()
    threading.Thread(target=run_flask, daemon=True).start()

    print("🔄 开始轮询 Telegram 服务器...")
    updater.start_polling()
    print("✅ 机器人已进入运行状态，等待消息...")
    updater.idle()
    print("⏹️ 机器人已停止")

if __name__ == "__main__":
    main()
