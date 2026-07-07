#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
print("===== Bot 完整版（全功能精简）=====")

import os, time, json, io, tempfile, requests, urllib3, sqlite3, hashlib, hmac, threading, logging, re, random, base64, urllib.parse
from typing import Optional
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
BOT_TOKEN = os.environ.get('5849383582:AAERYX0V4qwtQGggXTWQsFI5rlojuNY6oWM')
if not BOT_TOKEN:
    raise ValueError("请在环境变量中设置 BOT_TOKEN，或 GitHub Secrets 中添加")
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

# ===== 身份证生成函数（完整，压缩） =====
HEADERS1 = {"Host":"zwfw.dn.haikou.gov.cn","Connection":"keep-alive","sec-ch-ua-platform":"\"Android\"","zwfw-token":ZWFW_TOKEN,"User-Agent":"Mozilla/5.0 (Linux; Android 14; Build/BP2A.250605.031.A3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.7680.119 Mobile Safari/537.36 AgentWeb/5.0.0  yssApp","sec-ch-ua":"\"Android WebView\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"","content-type":"application/json","sec-ch-ua-mobile":"?1","Accept":"*/*","Origin":"https://zwfw.dn.haikou.gov.cn","X-Requested-With":"com.hanweb.hnzwfw.android.activity","Sec-Fetch-Site":"same-origin","Sec-Fetch-Mode":"cors","Sec-Fetch-Dest":"empty","Referer":"https://zwfw.dn.haikou.gov.cn/portal_h5/wsbl?id=1047370300041120912&step=B&certifyId=undefined","Accept-Encoding":"gzip, deflate, br, zstd","Accept-Language":"zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"}
HEADERS2 = {"Host":"zwfw.dn.haikou.gov.cn","Connection":"keep-alive","sec-ch-ua-platform":"\"Android\"","User-Agent":"Mozilla/5.0 (Linux; Android 14; Build/BP2A.250605.031.A3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.7680.119 Mobile Safari/537.36 AgentWeb/5.0.0  yssApp","sec-ch-ua":"\"Android WebView\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"","sec-ch-ua-mobile":"?1","Accept":"*/*","X-Requested-With":"com.hanweb.hnzwfw.android.activity","Sec-Fetch-Site":"same-origin","Sec-Fetch-Mode":"cors","Sec-Fetch-Dest":"empty","Referer":"https://zwfw.dn.haikou.gov.cn/portal_h5/wsbl?id=1047370300041120912&step=B&certifyId=undefined","Accept-Encoding":"gzip, deflate, br, zstd","Accept-Language":"zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"}
def query_id_card_sync(id_card):
    id_card = id_card.strip().upper()
    if len(id_card)!=18 or not id_card[:17].isdigit() or id_card[17] not in '0123456789X': return False, "身份证号无效"
    if not os.path.exists(SAVE_FOLDER): os.makedirs(SAVE_FOLDER)
    session = requests.Session(); session.cookies.update(BASE_COOKIES); session.verify = False
    url1 = "https://zwfw.dn.haikou.gov.cn/rest/materialshare/canShareMaterial"
    data = {"itemMaterialId":"1498591712970792960","materialCode":"1173207393439670272","materialName":"委托书原件及委托代理人的身份证明","interfaceParam":"ztmc,zzbh,dzzz_name,cardid,dzzz_type","interfaceParamName":"身份证","canShare":False,"isSignature":"N","appInterfaceId":"136","param":{"ztmc":FIXED_NAME,"zzbh":"","dzzz_name":"随便起个名","cardid":id_card,"dzzz_type":"1"},"itemId":"1047370300041120912","userId":"1547878749006024704"}
    for attempt in range(RETRY_TIMES):
        try: res1 = session.post(url1, headers=HEADERS1, json=data, timeout=30); result1 = res1.json()
        except Exception as e: print(f"[{attempt+1}/{RETRY_TIMES}] 请求异常: {e}"); time.sleep(2); continue
        print(f"[{attempt+1}/{RETRY_TIMES}] 服务端返回: {json.dumps(result1, ensure_ascii=False, indent=2)}")
        if result1.get("code")=="1":
            try:
                attachment_id = result1["resultDatas"]["result"]["resultDatas"]["attachmentList"][0]["id"]
                res2 = session.get(f"https://zwfw.dn.haikou.gov.cn/rest/attachment/{attachment_id}", headers=HEADERS2, timeout=30)
                if res2.status_code==200: return True, res2.content
                else: return False, f"下载失败 HTTP {res2.status_code}"
            except Exception as e: return False, f"解析失败: {e}"
        else: print(f"[{attempt+1}/{RETRY_TIMES}] 查询失败: {result1.get('message')}"); time.sleep(2)
    return False, f"连续 {RETRY_TIMES} 次失败"

def remove_white_background(img, threshold=240):
    if img.mode != 'RGBA': img = img.convert('RGBA')
    data = img.getdata()
    new_data = []
    for item in data:
        r, g, b, a = item
        if r > threshold and g > threshold and b > threshold and a != 0: new_data.append((r, g, b, 0))
        else: new_data.append(item)
    img.putdata(new_data); return img

def load_issuing_authority_map(file_path):
    m={}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if line:
                code, authority = line.split(':')
                m[code]=authority
    return m

def get_issuing_authority(id_number, m): return m.get(id_number[:6], "未知签发机关")

def format_address(address, max_chars_per_line=11):
    return [address[i:i+max_chars_per_line] for i in range(0, len(address), max_chars_per_line)]

def generate_id_card_sync(name, id_number, nation, address, expiration_date, user_photo_path):
    if len(id_number)<18: raise ValueError("身份证号码格式不正确")
    birth_date = id_number[6:14]; gender = '女' if int(id_number[-2])%2==0 else '男'
    m = load_issuing_authority_map('fonts/签发机关.txt'); issuing_authority = get_issuing_authority(id_number, m)
    template = Image.open('fonts/empty.png').convert("RGBA")
    name_font = ImageFont.truetype('fonts/hei.ttf', 72); other_font = ImageFont.truetype('fonts/hei.ttf', 64); birth_font = ImageFont.truetype('fonts/fzhei.ttf', 60); id_font = ImageFont.truetype('fonts/ocrb10bt.ttf', 90)
    draw = ImageDraw.Draw(template)
    draw.text((630,690), name, font=name_font, fill='black')
    draw.text((630,840), gender, font=other_font, fill='black')
    draw.text((1030,840), nation, font=other_font, fill='black')
    draw.text((630,975), birth_date[:4], font=birth_font, fill='black')
    draw.text((950,975), birth_date[4:6], font=birth_font, fill='black')
    draw.text((1150,975), birth_date[6:], font=birth_font, fill='black')
    y=1115
    for line in format_address(address):
        draw.text((630,y), line, font=other_font, fill='black'); y+=85
    draw.text((900,1475), id_number, font=id_font, fill='black')
    draw.text((1050,2750), issuing_authority, font=other_font, fill='black')
    draw.text((1050,2895), expiration_date, font=other_font, fill='black')
    photo = Image.open(user_photo_path).convert("RGBA"); photo = remove_white_background(photo, 240); photo = photo.resize((500,670)); template.paste(photo, (1500,670), mask=photo)
    img_bytes = io.BytesIO(); template.save(img_bytes, format='PNG'); img_bytes.seek(0)
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp: tmp_path = tmp.name; template.save(tmp_path, format='PNG')
    pdf_bytes = io.BytesIO(); c = canvas.Canvas(pdf_bytes, pagesize=A4); w,h = template.size; scale = min(A4[0]/w, A4[1]/h); c.drawImage(tmp_path, (A4[0]-w*scale)/2, (A4[1]-h*scale)/2, w*scale, h*scale); c.save(); pdf_bytes.seek(0); os.remove(tmp_path)
    return img_bytes, pdf_bytes

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
AREA_MAP = load_area_map()
def get_address_from_idcard(id_card): return AREA_MAP.get(id_card[:6], None)

def generate_plc_sync(name, id_card, address, avatar_path):
    if len(id_card)!=18: raise ValueError("身份证号必须为18位")
    gender = "男" if int(id_card[16])%2==1 else "女"
    if not os.path.exists('plc/mb.jpg'): raise FileNotFoundError("PLC模板文件 mb.jpg 不存在")
    if not os.path.exists('plc/10.ttf'): raise FileNotFoundError("PLC字体文件 10.ttf 不存在")
    template = Image.open('plc/mb.jpg').convert("RGBA")
    avatar = Image.open(avatar_path).convert("RGBA"); avatar = remove_white_background(avatar, 240); avatar = avatar.resize((416,500)); template.paste(avatar, (26,333), mask=avatar)
    draw = ImageDraw.Draw(template); font = ImageFont.truetype('plc/10.ttf', 55)
    year=id_card[6:10]; month=id_card[10:12]; day=id_card[12:14]; birth_str=f"{year}年{month}月{day}日"
    draw.text((598,314), name, font=font, fill=(0,0,0))
    draw.text((598,398), gender, font=font, fill=(0,0,0))
    draw.text((474,641), id_card, font=font, fill=(0,0,0))
    draw.text((718,482), birth_str, font=font, fill=(0,0,0))
    address_lines = [address[i:i+11] for i in range(0, len(address), 11)]
    for i,line in enumerate(address_lines): draw.text((473,782+i*60), line, font=font, fill=(0,0,0))
    img_bytes = io.BytesIO(); template.save(img_bytes, format='PNG'); img_bytes.seek(0)
    pdf_bytes = io.BytesIO(); c = canvas.Canvas(pdf_bytes, pagesize=A4); w,h = template.size; scale = min(A4[0]/w, A4[1]/h)
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp: tmp_path=tmp.name; template.save(tmp_path, format='PNG')
    c.drawImage(tmp_path, (A4[0]-w*scale)/2, (A4[1]-h*scale)/2, w*scale, h*scale); c.save(); pdf_bytes.seek(0); os.remove(tmp_path)
    return img_bytes, pdf_bytes

# ===== 数据库 =====
def init_db():
    conn = sqlite3.connect('user_points.db'); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, points REAL DEFAULT 0, total_recharge REAL DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    c.execute('CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, order_id TEXT UNIQUE, unique_id TEXT UNIQUE, amount REAL, points_earned REAL, status TEXT DEFAULT "pending", created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, processed_at TIMESTAMP)')
    c.execute('CREATE TABLE IF NOT EXISTS point_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, change_type TEXT, change_amount REAL, current_balance REAL, description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    c.execute('CREATE TABLE IF NOT EXISTS signin (user_id INTEGER PRIMARY KEY, last_sign_date TEXT)')
    conn.commit(); conn.close(); logger.info("数据库初始化完成")
init_db()

# ===== UserManager =====
class UserManager:
    @staticmethod
    def get_user(user_id):
        conn=sqlite3.connect('user_points.db'); c=conn.cursor(); c.execute('SELECT * FROM users WHERE user_id=?',(user_id,)); row=c.fetchone(); conn.close()
        if row: return dict(zip(['user_id','username','first_name','last_name','points','total_recharge','created_at','last_active'], row))
        return None
    @staticmethod
    def create_user(user_id, username, first_name, last_name):
        conn=sqlite3.connect('user_points.db'); c=conn.cursor(); c.execute('INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?,?,?,?)', (user_id, username, first_name, last_name)); conn.commit(); conn.close()
    @staticmethod
    def create_pending_order(user_id, order_id, unique_id, amount, points):
        conn=sqlite3.connect('user_points.db'); c=conn.cursor()
        try: c.execute('INSERT INTO transactions (user_id, order_id, unique_id, amount, points_earned, status) VALUES (?,?,?,?,?,?)', (user_id, order_id, unique_id, amount, points, 'pending')); conn.commit()
        except sqlite3.IntegrityError: logger.warning(f"订单 {order_id} 已存在")
        finally: conn.close()
    @staticmethod
    def add_points(user_id, amount_usdt, order_id):
        points=amount_usdt*POINTS_RATE; conn=sqlite3.connect('user_points.db'); c=conn.cursor()
        try:
            c.execute('SELECT status FROM transactions WHERE order_id=?',(order_id,)); row=c.fetchone()
            if row and row[0]=='completed': conn.close(); return points
            c.execute('SELECT points FROM users WHERE user_id=?',(user_id,)); current=c.fetchone()
            if not current: conn.close(); return None
            current_points=current[0] if current[0] is not None else 0.0
            c.execute('BEGIN'); c.execute('UPDATE users SET points=points+?, total_recharge=total_recharge+?, last_active=CURRENT_TIMESTAMP WHERE user_id=?', (points, amount_usdt, user_id))
            if row: c.execute('UPDATE transactions SET status=?, processed_at=CURRENT_TIMESTAMP WHERE order_id=?', ('completed', order_id))
            else: c.execute('INSERT INTO transactions (user_id, order_id, amount, points_earned, status, processed_at) VALUES (?,?,?,?,?, CURRENT_TIMESTAMP)', (user_id, order_id, amount_usdt, points, 'completed'))
            c.execute('INSERT INTO point_history (user_id, change_type, change_amount, current_balance, description) VALUES (?,?,?,?,?)', (user_id, 'recharge', points, current_points+points, f'充值 {amount_usdt} USDT'))
            conn.commit(); return points
        except Exception as e: conn.rollback(); logger.error(f"加积分失败: {e}"); raise
        finally: conn.close()
    @staticmethod
    def deduct_points(user_id, amount):
        if amount<=0: return False
        conn=sqlite3.connect('user_points.db'); c=conn.cursor()
        try:
            c.execute('SELECT points FROM users WHERE user_id=?',(user_id,)); row=c.fetchone()
            if not row: return False
            current=row[0] if row[0] is not None else 0.0
            if current<amount: return False
            c.execute('BEGIN'); c.execute('UPDATE users SET points=points-?, last_active=CURRENT_TIMESTAMP WHERE user_id=?', (amount, user_id))
            c.execute('INSERT INTO point_history (user_id, change_type, change_amount, current_balance, description) VALUES (?,?,?,?,?)', (user_id, 'consume', -amount, current-amount, f'广西查询消耗 {amount:.2f} 积分'))
            conn.commit(); return True
        except Exception as e: conn.rollback(); logger.error(f"扣积分失败: {e}"); return False
        finally: conn.close()
    @staticmethod
    def get_stats(user_id):
        conn=sqlite3.connect('user_points.db'); c=conn.cursor()
        c.execute('SELECT u.points, u.total_recharge, COUNT(t.id), COALESCE(SUM(t.amount),0) FROM users u LEFT JOIN transactions t ON u.user_id=t.user_id AND t.status="completed" WHERE u.user_id=? GROUP BY u.user_id', (user_id,))
        row=c.fetchone(); conn.close()
        if row: return {'points': row[0] or 0.0, 'total_recharge': row[1] or 0.0, 'trans_count': row[2] or 0, 'total_amount': row[3] or 0.0}
        return {'points':0.0, 'total_recharge':0.0, 'trans_count':0, 'total_amount':0.0}
    @staticmethod
    def sign_in(user_id):
        today=time.strftime('%Y-%m-%d'); conn=sqlite3.connect('user_points.db'); c=conn.cursor()
        try:
            c.execute('SELECT last_sign_date FROM signin WHERE user_id=?',(user_id,)); row=c.fetchone()
            if row and row[0]==today: return False, 0
            reward=0.05
            c.execute('BEGIN'); c.execute('UPDATE users SET points=points+?, last_active=CURRENT_TIMESTAMP WHERE user_id=?', (reward, user_id))
            c.execute('INSERT INTO point_history (user_id, change_type, change_amount, current_balance, description) VALUES (?,?,?,?,?)', (user_id, 'signin', reward, None, '每日签到'))
            if row: c.execute('UPDATE signin SET last_sign_date=? WHERE user_id=?', (today, user_id))
            else: c.execute('INSERT INTO signin (user_id, last_sign_date) VALUES (?,?)', (user_id, today))
            conn.commit(); return True, reward
        except Exception as e: conn.rollback(); logger.error(f"签到失败: {e}"); return False, 0
        finally: conn.close()
    @staticmethod
    def add_points_direct(user_id, amount, description='管理员赠送'):
        if amount<=0: return False
        conn=sqlite3.connect('user_points.db'); c=conn.cursor()
        try:
            c.execute('SELECT points FROM users WHERE user_id=?',(user_id,)); row=c.fetchone()
            if not row: return False
            current=row[0] if row[0] is not None else 0.0
            c.execute('BEGIN'); c.execute('UPDATE users SET points=points+?, last_active=CURRENT_TIMESTAMP WHERE user_id=?', (amount, user_id))
            c.execute('INSERT INTO point_history (user_id, change_type, change_amount, current_balance, description) VALUES (?,?,?,?,?)', (user_id, 'gift', amount, current+amount, description))
            conn.commit(); return True
        except Exception as e: conn.rollback(); logger.error(f"赠送积分失败: {e}"); return False
        finally: conn.close()

# ===== OkayPay 客户端 (HMAC-SHA256) =====
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
        logger.info(f"📝 签名原文: {base}")
        return base
    def _sign(self, params):
        base=self._build_base(params)
        sign=hmac.new(self.token.encode('utf-8'), base.encode('utf-8'), hashlib.sha256).hexdigest().upper()
        logger.info(f"📝 计算签名: {sign}")
        return sign
    def _signed_params(self, params):
        nonce=''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16))
        timestamp=int(time.time())
        full_params={'id':str(self.appid),'timestamp':timestamp,'nonce':nonce,**params}
        full_params['sign']=self._sign(full_params)
        logger.info(f"📤 完整提交参数: {full_params}")
        return full_params
    def verify(self, data):
        if 'sign' not in data: return False
        in_sign=data['sign']; calc_sign=self._sign(data); return calc_sign==in_sign
    def pay_link(self, amount, unique_id):
        logger.info(f"🚀 创建支付链接 - 金额: {amount}, 订单号: {unique_id}")
        params={'amount':f"{amount:.2f}",'coin':'USDT','unique_id':unique_id,'name':'积分充值','callback_url':CALLBACK_URL,'return_url':CALLBACK_URL}
        signed=self._signed_params(params)
        try:
            resp=requests.post(self.api_url+'payLink', data=signed, headers={'Content-Type':'application/x-www-form-urlencoded'}, timeout=15, verify=False)
            logger.info(f"📨 响应: {resp.text}")
            if resp.status_code==200:
                result=resp.json()
                if result.get('status')=='success' and self.verify(result):
                    return result
                else:
                    logger.error(f"⚠️ 响应异常: {result}")
                    return {'status':'error','msg':result.get('msg','未知错误')}
            else: return {'status':'error','msg':f'HTTP {resp.status_code}'}
        except Exception as e: logger.error(e); return {'status':'error','msg':str(e)}
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
                            points=UserManager.add_points(user_id, amount, order_id)
                            if points is not None:
                                stats=UserManager.get_stats(user_id)
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
        logger.info(f"收到回调: {data}")
        if not client.verify(data): return jsonify({'status':'success'}), 200
        if data.get('status')=='success':
            od=data.get('data',{}); otype=od.get('type'); oid=od.get('order_id'); amount=float(od.get('amount',0)); uid=od.get('unique_id')
            if otype=='deposit' and od.get('status')==1:
                conn=sqlite3.connect('user_points.db'); c=conn.cursor(); c.execute('SELECT user_id,status FROM transactions WHERE order_id=?',(oid,)); row=c.fetchone(); conn.close()
                if not row: return jsonify({'status':'success'}), 200
                user_id, current_status = row
                if current_status=='completed': return jsonify({'status':'success'}), 200
                points=UserManager.add_points(user_id, amount, oid)
                if points is not None:
                    stats=UserManager.get_stats(user_id)
                    try: bot.send_message(user_id, f"✅ 支付成功！（回调）\n订单号: {oid}\n充值: {amount:.2f} USDT\n获得积分: {points:.2f}\n当前积分: {stats['points']:.2f}")
                    except: pass
                    if uid and uid in orders: orders[uid]['status']='completed'
        return jsonify({'status':'success'}), 200
    except Exception as e: logger.exception("回调异常"); return jsonify({'status':'success'}), 200

def run_flask(): flask_app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# ===== 广西查询模块 =====
SM4_KEY="CatsPK0WWWRRhjkw"
SboxTable = [0xd6,0x90,0xe9,0xfe,0xcc,0xe1,0x3d,0xb7,0x16,0xb6,0x14,0xc2,0x28,0xfb,0x2c,0x05,0x2b,0x67,0x9a,0x76,0x2a,0xbe,0x04,0xc3,0xaa,0x44,0x13,0x26,0x49,0x86,0x06,0x99,0x9c,0x42,0x50,0xf4,0x91,0xef,0x98,0x7a,0x33,0x54,0x0b,0x43,0xed,0xcf,0xac,0x62,0xe4,0xb3,0x1c,0xa9,0xc9,0x08,0xe8,0x95,0x80,0xdf,0x94,0xfa,0x75,0x8f,0x3f,0xa6,0x47,0x07,0xa7,0xfc,0xf3,0x73,0x17,0xba,0x83,0x59,0x3c,0x19,0xe6,0x85,0x4f,0xa8,0x68,0x6b,0x81,0xb2,0x71,0x64,0xda,0x8b,0xf8,0xeb,0x0f,0x4b,0x70,0x56,0x9d,0x35,0x1e,0x24,0x0e,0x5e,0x63,0x58,0xd1,0xa2,0x25,0x22,0x7c,0x3b,0x01,0x21,0x78,0x87,0xd4,0x00,0x46,0x57,0x9f,0xd3,0x27,0x52,0x4c,0x36,0x02,0xe7,0xa0,0xc4,0xc8,0x9e,0xea,0xbf,0x8a,0xd2,0x40,0xc7,0x38,0xb5,0xa3,0xf7,0xf2,0xce,0xf9,0x61,0x15,0xa1,0xe0,0xae,0x5d,0xa4,0x9b,0x34,0x1a,0x55,0xad,0x93,0x32,0x30,0xf5,0x8c,0xb1,0xe3,0x1d,0xf6,0xe2,0x2e,0x82,0x66,0xca,0x60,0xc0,0x29,0x23,0xab,0x0d,0x53,0x4e,0x6f,0xd5,0xdb,0x37,0x45,0xde,0xfd,0x8e,0x2f,0x03,0xff,0x6a,0x72,0x6d,0x6c,0x5b,0x51,0x8d,0x1b,0xaf,0x92,0xbb,0xdd,0xbc,0x7f,0x11,0xd9,0x5c,0x41,0x1f,0x10,0x5a,0xd8,0x0a,0xc1,0x31,0x88,0xa5,0xcd,0x7b,0xbd,0x2d,0x74,0xd0,0x12,0xb8,0xe5,0xb4,0xb0,0x89,0x69,0x97,0x4a,0x0c,0x96,0x77,0x7e,0x65,0xb9,0xf1,0x09,0xc5,0x6e,0xc6,0x84,0x18,0xf0,0x7d,0xec,0x3a,0xdc,0x4d,0x20,0x79,0xee,0x5f,0x3e,0xd7,0xcb,0x39,0x48]
FK=[0xa3b1bac6,0x56aa3350,0x677d9197,0xb27022dc]
CK=[0x00070e15,0x1c232a31,0x383f464d,0x545b6269,0x70777e85,0x8c939aa1,0xa8afb6bd,0xc4cbd2d9,0xe0e7eef5,0xfc030a11,0x181f262d,0x343b4249,0x50575e65,0x6c737a81,0x888f969d,0xa4abb2b9,0xc0c7ced5,0xdce3eaf1,0xf8ff060d,0x141b2229,0x30373e45,0x4c535a61,0x686f767d,0x848b9299,0xa0a7aeb5,0xbcc3cad1,0xd8dfe6ed,0xf4fb0209,0x10171e25,0x2c333a41,0x484f565d,0x646b7279]
def rotl(x,n): return ((x<<n)&0xffffffff) | (((x-0x100000000 if x&0x80000000 else x)>>(32-n))&0xffffffff)
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

def gx_login(session, id_card):
    enc_login=urllib.parse.quote(sm4_encrypt_ecb(id_card)); enc_pwd=urllib.parse.quote(sm4_encrypt_ecb(GX_PASSWORD))
    data=f"loginName={enc_login}&password={enc_pwd}&wechatUid="
    headers={"User-Agent":"Mozilla/5.0 (Linux; Android 14; Build/BP2A.250605.031.A3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.7680.119 Mobile Safari/537.36","X-Requested-With":"XMLHttpRequest","Accept":"application/json, text/javascript, */*; q=0.01","Accept-Encoding":"gzip, deflate","Accept-Language":"zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7","Connection":"keep-alive","Content-Type":"application/x-www-form-urlencoded; charset=UTF-8","Referer":"http://www.gxdlys.com/Wechat/Home/Login","Host":"www.gxdlys.com"}
    try:
        r=session.post("http://www.gxdlys.com/Wechat/Home/PostLogin", headers=headers, data=data, timeout=30)
        if r.status_code==200:
            res=r.json(); return res.get("statusCode")==200
    except: return False
    return False

def gx_query_photo(session, name, id_card):
    try:
        encoded_name=urllib.parse.quote(name)
        url=f"http://www.gxdlys.com/Wechat/FaceDetect/GetGAIDCardPhotoNew?idCard={id_card}&name={encoded_name}"
        headers={"User-Agent":"Mozilla/5.0 (Linux; Android 14; Build/BP2A.250605.031.A3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.7680.119 Mobile Safari/537.36","X-Requested-With":"XMLHttpRequest","Accept":"application/json, text/javascript, */*; q=0.01","Accept-Encoding":"gzip, deflate","Accept-Language":"zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7","Connection":"keep-alive","Referer":"http://www.gxdlys.com/Wechat/EcertCert/ECertApply?OperateType=0&BnsAcceptId=&ObjectId=&BasicBnsId=46011&Params=%E7%BB%8F%E8%90%A5%E6%80%A7%E9%81%93%E8%B7%AF%E8%B4%A7%E7%89%A9%E8%BF%90%E8%BE%93%E9%A9%BE%E9%A9%B6%E5%91%98&Step=1","Host":"www.gxdlys.com"}
        r=session.get(url, headers=headers, timeout=30)
        if r.status_code!=200: return False, f"HTTP {r.status_code}"
        res=r.json()
        if res.get("statusCode")!=200: return False, res.get("info","查询失败")
        file_id=res.get("data",{}).get("item1")
        if not file_id: return False, "未获取到照片文件ID"
        photo_resp=session.get(f"http://www.gxdlys.com/System/FileService/ShowFile?fileId={file_id}", timeout=30)
        if photo_resp.status_code!=200 or 'image' not in photo_resp.headers.get('Content-Type',''): return False, "照片下载失败"
        return True, photo_resp.content
    except Exception as e: return False, str(e)

def gx_query_main(name, id_card):
    session=requests.Session()
    try:
        if not gx_login(session, id_card): return False, "登录失败"
        return gx_query_photo(session, name, id_card)
    finally: session.close()

# ===== Telegram 命令 =====
RECHARGE_AMOUNT=100

def start(update, context):
    update.message.reply_text("小宇机器人功能列表：\n/hainansf +空格+身份证 → 查询海南大头\n/sfz → 生成标准身份证（双面）\n/plc → 生成PLC模板身份证\n/recharge → 充值积分\n/balance → 查询积分余额\n/gxquery 姓名 身份证 → 查询广西道路运输照片（消耗0.05积分）\n/signin → 每日签到（获得0.05积分）\n/givepoint 用户ID 积分 [备注] → 管理员赠送积分\n/cancel → 取消当前操作")

def hainansf(update, context):
    args=context.args
    if not args: update.message.reply_text("❌ 格式错误\n正确格式：/hainansf <身份证号>"); return
    id_card=args[0].strip()
    if len(id_card)!=18: update.message.reply_text("❌ 身份证号必须为18位"); return
    update.message.reply_text("⏳ 正在查询海南系统...")
    success, result=query_id_card_sync(id_card)
    if success: context.bot.send_document(chat_id=update.effective_chat.id, document=io.BytesIO(result), filename=f"{id_card}.pdf", caption="✅ 查询成功")
    else: update.message.reply_text(f"❌ 查询失败：{result}")

def cancel(update, context):
    update.message.reply_text("已取消"); context.user_data.clear(); return ConversationHandler.END

def recharge_start(update, context):
    uid=update.effective_user.id
    UserManager.create_user(uid, update.effective_user.username, update.effective_user.first_name, update.effective_user.last_name)
    stats=UserManager.get_stats(uid)
    update.message.reply_text(f"💰 积分充值\n当前积分: {stats['points']:.2f}\n累计充值: {stats['total_recharge']:.2f} USDT\n\n请输入要充值的 USDT 金额（例如 10）：")
    return RECHARGE_AMOUNT

def recharge_amount(update, context):
    uid=update.effective_user.id
    try: amt=float(re.sub(r'[^\d.]', '', update.message.text)); 
    except: update.message.reply_text("❌ 请输入有效的正数金额"); return RECHARGE_AMOUNT
    if amt<=0: update.message.reply_text("❌ 金额必须大于0"); return RECHARGE_AMOUNT
    points=amt*POINTS_RATE
    unique_id=f"ORDER_{int(time.time())}_{uid}_{random.randint(1000,9999)}"
    resp=client.pay_link(amt, unique_id)
    if not resp or resp.get('status')!='success':
        update.message.reply_text(f"❌ 创建订单失败: {resp.get('msg','未知错误')}")
        return ConversationHandler.END
    order_id=resp['data']['order_id']; pay_url=resp['data']['pay_url']
    UserManager.create_pending_order(uid, order_id, unique_id, amt, points)
    orders[unique_id]={'user_id':uid,'amount':amt,'order_id':order_id,'status':'pending','timestamp':time.time()}
    keyboard=[[InlineKeyboardButton("💳 去支付", url=pay_url)]]
    update.message.reply_text(f"✅ 订单已创建\n订单号: {order_id}\n金额: {amt:.2f} USDT → {points:.2f} 积分\n有效期: 30 分钟\n点击下方按钮完成支付", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

def balance(update, context):
    stats=UserManager.get_stats(update.effective_user.id)
    update.message.reply_text(f"📊 您的积分: {stats['points']:.2f}\n累计充值: {stats['total_recharge']:.2f} USDT")

def signin(update, context):
    uid=update.effective_user.id; success, reward=UserManager.sign_in(uid)
    if success: stats=UserManager.get_stats(uid); update.message.reply_text(f"✅ 签到成功！获得 {reward:.2f} 积分\n当前积分: {stats['points']:.2f}")
    else: update.message.reply_text("❌ 今天已经签到了，明天再来吧！")

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
    remark=' '.join(args[2:]) if len(args)>2 else '管理员赠送'
    if UserManager.add_points_direct(target_id, amount, remark):
        stats=UserManager.get_stats(target_id); update.message.reply_text(f"✅ 已向用户 {target_id} 赠送 {amount:.2f} 积分，当前积分 {stats['points']:.2f}")
    else: update.message.reply_text(f"❌ 赠送失败，请确认用户 {target_id} 存在")

def gxquery(update, context):
    uid=update.effective_user.id; args=context.args
    if len(args)<2: update.message.reply_text("❌ 格式错误\n正确格式：/gxquery <姓名> <身份证号>"); return
    name=args[0].strip(); id_card=args[1].strip()
    if len(id_card)!=18: update.message.reply_text("❌ 身份证号必须为18位"); return
    stats=UserManager.get_stats(uid)
    if stats['points']<GX_QUERY_PRICE: update.message.reply_text(f"❌ 积分不足！需要 {GX_QUERY_PRICE:.2f} 积分，当前 {stats['points']:.2f}"); return
    if not UserManager.deduct_points(uid, GX_QUERY_PRICE): update.message.reply_text("❌ 积分扣除失败"); return
    msg=update.message.reply_text(f"⏳ 正在查询 {name} 的照片...")
    def do():
        success, result=gx_query_main(name, id_card)
        if success:
            try: context.bot.send_photo(chat_id=uid, photo=io.BytesIO(result), caption=f"✅ {name} 的身份证照片（广西道路运输）\n消耗积分: {GX_QUERY_PRICE:.2f}")
            except Exception as e: context.bot.send_message(uid, f"❌ 发送照片失败: {e}")
        else:
            UserManager.add_points(uid, GX_QUERY_PRICE, None)
            context.bot.send_message(uid, f"❌ 查询失败: {result}\n已退还 {GX_QUERY_PRICE:.2f} 积分")
        context.bot.delete_message(chat_id=uid, message_id=msg.message_id)
    threading.Thread(target=do, daemon=True).start()

# ===== sfz 对话 =====
SFZ_NAME, SFZ_ID, SFZ_NATION, SFZ_ADDR, SFZ_EXPIRY, SFZ_PHOTO = range(6)
def sfz_start(update, context): update.message.reply_text("📝 开始生成身份证（标准模板），请输入姓名："); return SFZ_NAME
def sfz_name(update, context): context.user_data['name']=update.message.text.strip(); update.message.reply_text("请输入18位身份证号："); return SFZ_ID
def sfz_id(update, context):
    id_card=update.message.text.strip().upper()
    if len(id_card)!=18 or not (id_card[:17].isdigit() and id_card[-1] in '0123456789X'): update.message.reply_text("格式错误，重新输入："); return SFZ_ID
    context.user_data['id_number']=id_card; update.message.reply_text("请输入民族："); return SFZ_NATION
def sfz_nation(update, context): context.user_data['nation']=update.message.text.strip(); update.message.reply_text("请输入地址："); return SFZ_ADDR
def sfz_address(update, context): context.user_data['address']=update.message.text.strip(); update.message.reply_text("请输入有效期（如 2020.01.01-2030.01.01）："); return SFZ_EXPIRY
def sfz_expiry(update, context): context.user_data['expiry']=update.message.text.strip(); update.message.reply_text("请发送一张本人照片："); return SFZ_PHOTO
def sfz_photo(update, context):
    if not update.message.photo: update.message.reply_text("请发送图片。"); return SFZ_PHOTO
    photo=update.message.photo[-1]; file=photo.get_file()
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp: file.download(tmp.name); photo_path=tmp.name
    data=context.user_data
    if not all(k in data for k in ['name','id_number','nation','address','expiry']): update.message.reply_text("信息不完整，请重新 /sfz"); return ConversationHandler.END
    update.message.reply_text("⏳ 生成中...")
    try:
        img, pdf=generate_id_card_sync(data['name'], data['id_number'], data['nation'], data['address'], data['expiry'], photo_path)
        update.message.reply_photo(photo=img, caption=f"✅ {data['name']} 的身份证"); context.bot.send_document(chat_id=update.effective_chat.id, document=pdf, filename=f"{data['name']}_身份证.pdf")
    except Exception as e: update.message.reply_text(f"❌ 失败：{e}")
    finally:
        if os.path.exists(photo_path): os.remove(photo_path)
        context.user_data.clear()
    return ConversationHandler.END

# ===== plc 对话 =====
PLC_NAME, PLC_ID, PLC_ADDR_CONFIRM, PLC_ADDR_MANUAL, PLC_PHOTO = range(10,15)
def plc_start(update, context): update.message.reply_text("📝 开始生成身份证（PLC模板），请输入姓名："); return PLC_NAME
def plc_name(update, context): context.user_data['name']=update.message.text.strip(); update.message.reply_text("请输入18位身份证号："); return PLC_ID
def plc_id(update, context):
    id_card=update.message.text.strip().upper()
    if len(id_card)!=18 or not (id_card[:17].isdigit() and id_card[-1] in '0123456789X'): update.message.reply_text("格式错误，重新输入："); return PLC_ID
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
            context.user_data['address']=address; query.edit_message_text(f"✅ 已使用地址：{address}\n请发送一张本人照片："); return PLC_PHOTO
        else: query.edit_message_text("未找到地址，请手动输入："); return PLC_ADDR_MANUAL
    elif query.data=="plc_addr_no":
        query.edit_message_text("请输入详细地址（手动输入）："); return PLC_ADDR_MANUAL
def plc_addr_manual(update, context):
    address=update.message.text.strip()
    if not address: update.message.reply_text("地址不能为空，请重新输入："); return PLC_ADDR_MANUAL
    context.user_data['address']=address; update.message.reply_text("请发送一张本人照片："); return PLC_PHOTO
def plc_photo(update, context):
    if not update.message.photo: update.message.reply_text("请发送图片。"); return PLC_PHOTO
    photo=update.message.photo[-1]; file=photo.get_file()
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp: file.download(tmp.name); photo_path=tmp.name
    data=context.user_data
    if not all(k in data for k in ['name','id_number','address']): update.message.reply_text("信息不完整，请重新 /plc"); return ConversationHandler.END
    update.message.reply_text("⏳ 生成中...")
    try:
        img, pdf=generate_plc_sync(data['name'], data['id_number'], data['address'], photo_path)
        update.message.reply_photo(photo=img, caption=f"✅ {data['name']} 的身份证（PLC模板）"); context.bot.send_document(chat_id=update.effective_chat.id, document=pdf, filename=f"{data['name']}_身份证_PLC.pdf")
    except FileNotFoundError as e: update.message.reply_text(f"❌ 文件缺失：{e}\n请确保 plc/ 目录下有 mb.jpg 和 10.ttf")
    except Exception as e: update.message.reply_text(f"❌ 生成失败：{e}")
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
    dp.add_handler(CommandHandler("gxquery", gxquery))
    dp.add_handler(CommandHandler("signin", signin))
    dp.add_handler(CommandHandler("givepoint", givepoint))

    dp.add_handler(ConversationHandler(entry_points=[CommandHandler('recharge', recharge_start)],
        states={RECHARGE_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, recharge_amount)]},
        fallbacks=[CommandHandler('cancel', cancel)]))
    dp.add_handler(ConversationHandler(entry_points=[CommandHandler('sfz', sfz_start)],
        states={SFZ_NAME:[MessageHandler(Filters.text & ~Filters.command, sfz_name)], SFZ_ID:[MessageHandler(Filters.text & ~Filters.command, sfz_id)], SFZ_NATION:[MessageHandler(Filters.text & ~Filters.command, sfz_nation)], SFZ_ADDR:[MessageHandler(Filters.text & ~Filters.command, sfz_address)], SFZ_EXPIRY:[MessageHandler(Filters.text & ~Filters.command, sfz_expiry)], SFZ_PHOTO:[MessageHandler(Filters.photo, sfz_photo)]},
        fallbacks=[CommandHandler('cancel', cancel)]))
    dp.add_handler(ConversationHandler(entry_points=[CommandHandler('plc', plc_start)],
        states={PLC_NAME:[MessageHandler(Filters.text & ~Filters.command, plc_name)], PLC_ID:[MessageHandler(Filters.text & ~Filters.command, plc_id)], PLC_ADDR_CONFIRM:[CallbackQueryHandler(plc_addr_confirm_callback, pattern='^(plc_addr_yes|plc_addr_no)$')], PLC_ADDR_MANUAL:[MessageHandler(Filters.text & ~Filters.command, plc_addr_manual)], PLC_PHOTO:[MessageHandler(Filters.photo, plc_photo)]},
        fallbacks=[CommandHandler('cancel', cancel)]))

    threading.Thread(target=check_orders, daemon=True).start()
    threading.Thread(target=run_flask, daemon=True).start()

    print("🤖 机器人已启动（全功能）")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
