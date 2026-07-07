#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并版机器人：身份证生成 + OkayPay 自助充值（HMAC-SHA256 新协议）
根据官方文档 https://docs.okaypay.me 完整对接
"""

import sys
print("===== Bot 完整版（身份证生成 + 支付充值 | HMAC-SHA256）=====")

import os
import time
import json
import io
import tempfile
import requests
import urllib3
import sqlite3
import hashlib
import hmac
import threading
import logging
import re
import random
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater, CommandHandler, ConversationHandler,
    MessageHandler, Filters, CallbackQueryHandler
)
from flask import Flask, request, jsonify

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MergedBot')

# ============================================================
#  配置（请将下方密钥替换为您刷新后的新密钥）
# ============================================================
BOT_TOKEN = os.environ.get('BOT_TOKEN') or "5849383582:AAHYfu-sNW7v_I2cMcfMv52EUDjZ1xaGelY"

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

# ----- OkayPay 配置（请修改为您的最新信息） -----
OKPAY_ID = int(os.environ.get('OKPAY_ID') or 36326)          # 您的 App ID
OKPAY_TOKEN = os.environ.get('OKPAY_TOKEN') or 'TCtvS9O6idNOw3XaDyoTEEVG8awJCkdb'  # ⚠️ 务必刷新后填入
OKPAY_API_URL = 'https://api.okaypay.me/shop/'
CALLBACK_URL = os.environ.get('CALLBACK_URL') or 'https://docs.okaypay.me/'
PORT = 1010
POINTS_RATE = 1
CHECK_INTERVAL = 0.5
ORDER_TIMEOUT = 1800

# ============================================================
#  1. 身份证生成相关函数（完整）
# ============================================================
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
#  2. 支付模块（数据库、用户管理、OkayPay 客户端）
# ============================================================

def init_db():
    conn = sqlite3.connect('user_points.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT,
                  points INTEGER DEFAULT 0, total_recharge REAL DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, order_id TEXT UNIQUE, unique_id TEXT UNIQUE,
                  amount REAL, points_earned INTEGER, status TEXT DEFAULT 'pending',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  processed_at TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS point_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                  change_type TEXT, change_amount INTEGER, current_balance INTEGER,
                  description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
    logger.info("数据库初始化完成")

init_db()

class UserManager:
    @staticmethod
    def get_user(user_id):
        conn = sqlite3.connect('user_points.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return dict(zip(['user_id','username','first_name','last_name','points',
                             'total_recharge','created_at','last_active'], row))
        return None

    @staticmethod
    def create_user(user_id, username, first_name, last_name):
        conn = sqlite3.connect('user_points.db')
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?,?,?,?)',
                  (user_id, username, first_name, last_name))
        conn.commit()
        conn.close()

    @staticmethod
    def update_activity(user_id):
        conn = sqlite3.connect('user_points.db')
        c = conn.cursor()
        c.execute('UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def create_pending_order(user_id, order_id, unique_id, amount, points):
        conn = sqlite3.connect('user_points.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO transactions (user_id, order_id, unique_id, amount, points_earned, status) VALUES (?,?,?,?,?,?)',
                      (user_id, order_id, unique_id, amount, points, 'pending'))
            conn.commit()
            logger.info(f"记录订单 {order_id} 用户 {user_id}")
        except sqlite3.IntegrityError:
            logger.warning(f"订单 {order_id} 已存在")
        finally:
            conn.close()

    @staticmethod
    def get_order_by_unique_id(unique_id):
        conn = sqlite3.connect('user_points.db')
        c = conn.cursor()
        c.execute('SELECT user_id, order_id, amount, status FROM transactions WHERE unique_id = ?', (unique_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return row[0], row[1], row[2], row[3]
        return None, None, None, None

    @staticmethod
    def add_points(user_id, amount_usdt, order_id):
        points = int(amount_usdt * POINTS_RATE)
        conn = sqlite3.connect('user_points.db')
        c = conn.cursor()
        try:
            c.execute('SELECT status FROM transactions WHERE order_id = ?', (order_id,))
            row = c.fetchone()
            if row and row[0] == 'completed':
                logger.info(f"订单 {order_id} 已完成，跳过")
                conn.close()
                return points

            c.execute('SELECT points FROM users WHERE user_id = ?', (user_id,))
            current = c.fetchone()
            if not current:
                logger.error(f"用户 {user_id} 不存在")
                conn.close()
                return None

            current_points = current[0]
            c.execute('BEGIN')
            c.execute('UPDATE users SET points = points + ?, total_recharge = total_recharge + ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?',
                      (points, amount_usdt, user_id))
            if row:
                c.execute('UPDATE transactions SET status = ?, processed_at = CURRENT_TIMESTAMP WHERE order_id = ?',
                          ('completed', order_id))
            else:
                c.execute('INSERT INTO transactions (user_id, order_id, amount, points_earned, status, processed_at) VALUES (?,?,?,?,?, CURRENT_TIMESTAMP)',
                          (user_id, order_id, amount_usdt, points, 'completed'))
            c.execute('INSERT INTO point_history (user_id, change_type, change_amount, current_balance, description) VALUES (?,?,?,?,?)',
                      (user_id, 'recharge', points, current_points + points, f'充值 {amount_usdt} USDT'))
            conn.commit()
            logger.info(f"用户 {user_id} 充值 {amount_usdt} USDT，获得 {points} 积分")
            return points
        except Exception as e:
            conn.rollback()
            logger.error(f"加积分失败: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def get_stats(user_id):
        conn = sqlite3.connect('user_points.db')
        c = conn.cursor()
        c.execute('''
            SELECT u.points, u.total_recharge, COUNT(t.id), COALESCE(SUM(t.amount),0)
            FROM users u LEFT JOIN transactions t ON u.user_id = t.user_id AND t.status='completed'
            WHERE u.user_id = ?
            GROUP BY u.user_id
        ''', (user_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return {'points': row[0] or 0, 'total_recharge': row[1] or 0,
                    'trans_count': row[2] or 0, 'total_amount': row[3] or 0}
        return {'points':0, 'total_recharge':0, 'trans_count':0, 'total_amount':0}

# ============================================================
#  OkayPay 客户端（HMAC-SHA256 新协议）
# ============================================================

class OkayPay:
    def __init__(self, appid, token, api_url):
        self.appid = appid
        self.token = token
        self.api_url = api_url

    def _build_base(self, params):
        """构造签名原文 base（符合文档 2.1 节）"""
        # 1. 去掉 sign 字段
        params = {k: v for k, v in params.items() if k != 'sign'}
        # 2. 去掉 null 和空字符串
        params = {k: v for k, v in params.items() if v is not None and v != ''}
        # 3 & 4 & 5: 展开嵌套对象，布尔值转字符串
        def flatten(obj, prefix=''):
            items = {}
            if isinstance(obj, dict):
                for k, v in obj.items():
                    key = f"{prefix}.{k}" if prefix else k
                    if isinstance(v, dict):
                        items.update(flatten(v, key))
                    else:
                        items[key] = v
            else:
                items[prefix] = obj
            return items

        flat_params = {}
        for k, v in params.items():
            if isinstance(v, dict):
                flat_params.update(flatten(v, k))
            elif isinstance(v, bool):
                flat_params[k] = 'true' if v else 'false'
            else:
                flat_params[k] = str(v)

        # 6. 按键名 ASCII 升序排序
        sorted_params = dict(sorted(flat_params.items()))
        # 7. 拼接 key=value&...
        base = '&'.join([f"{k}={v}" for k, v in sorted_params.items()])
        logger.info(f"📝 签名原文: {base}")
        return base

    def _sign(self, params):
        """计算 HMAC-SHA256 签名，返回 64 位大写十六进制"""
        base = self._build_base(params)
        sign = hmac.new(
            self.token.encode('utf-8'),
            base.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        logger.info(f"📝 计算签名: {sign}")
        return sign

    def _signed_params(self, params):
        """自动添加 id, timestamp, nonce, sign"""
        nonce = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16))
        timestamp = int(time.time())

        full_params = {
            'id': str(self.appid),
            'timestamp': timestamp,
            'nonce': nonce,
            **params
        }

        sign = self._sign(full_params)
        full_params['sign'] = sign

        logger.info(f"📤 完整提交参数: {full_params}")
        return full_params

    def verify(self, data):
        """验证回调/响应签名"""
        if 'sign' not in data:
            logger.error("响应数据缺少 sign 字段")
            return False
        in_sign = data['sign']
        calc_sign = self._sign(data)
        is_valid = calc_sign == in_sign
        logger.info(f"🔐 验签结果: {'✅ 通过' if is_valid else '❌ 失败'}")
        return is_valid

    def pay_link(self, amount, unique_id):
        """6.1 创建支付链接"""
        logger.info(f"🚀 创建支付链接 - 金额: {amount}, 订单号: {unique_id}")
        params = {
            'amount': f"{amount:.2f}",
            'coin': 'USDT',
            'unique_id': unique_id,
            'name': '积分充值',
            'callback_url': CALLBACK_URL,
            'return_url': CALLBACK_URL
        }
        signed = self._signed_params(params)

        try:
            api_url = self.api_url + 'payLink'
            logger.info(f"🌐 请求 URL: {api_url}")
            resp = requests.post(
                api_url,
                data=signed,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=15,
                verify=False
            )
            logger.info(f"📨 响应状态码: {resp.status_code}")
            logger.info(f"📨 响应内容: {resp.text}")

            if resp.status_code == 200:
                result = resp.json()
                if result.get('status') == 'success':
                    if self.verify(result):
                        logger.info(f"✅ 支付链接创建成功: {result}")
                        return result
                    else:
                        logger.error("⚠️ 响应签名验证失败！")
                        return {'status': 'error', 'msg': '响应签名验证失败'}
                else:
                    logger.info(f"⚠️ 响应状态: {result.get('status')}, msg: {result.get('msg')}")
                    return result
            else:
                return {'status': 'error', 'msg': f'HTTP {resp.status_code}', 'body': resp.text}
        except Exception as e:
            logger.error(f"❌ 请求异常: {e}", exc_info=True)
            return {'status': 'error', 'msg': str(e)}

    def check_deposit(self, unique_id):
        """6.2 查询充值订单"""
        logger.info(f"🔍 检查充值状态 - unique_id: {unique_id}")
        params = {'unique_id': unique_id}
        signed = self._signed_params(params)

        try:
            api_url = self.api_url + 'checkDeposit'
            resp = requests.post(
                api_url,
                data=signed,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=15,
                verify=False
            )
            logger.info(f"📨 检查响应: {resp.text}")
            if resp.status_code == 200:
                result = resp.json()
                if result.get('status') == 'success':
                    if self.verify(result):
                        return result
                    else:
                        return {'status': 'error', 'msg': '响应签名验证失败'}
                return result
            else:
                return {'status': 'error', 'msg': f'HTTP {resp.status_code}'}
        except Exception as e:
            logger.error(f"❌ 检查请求异常: {e}", exc_info=True)
            return {'status': 'error', 'msg': str(e)}

client = OkayPay(OKPAY_ID, OKPAY_TOKEN, OKPAY_API_URL)
orders = {}

# ============================================================
#  轮询检查线程
# ============================================================

def check_orders():
    while True:
        try:
            now = time.time()
            expired_orders = []
            for unique_id, order_info in list(orders.items()):
                if now - order_info['timestamp'] > ORDER_TIMEOUT:
                    expired_orders.append(unique_id)
                    continue
                if order_info['status'] == 'pending':
                    result = client.check_deposit(unique_id)
                    if result and result.get('status') == 'success':
                        data = result.get('data', {})
                        status = data.get('status')
                        if status == 1:
                            user_id = order_info['user_id']
                            amount = float(data.get('amount', 0))
                            order_id = data.get('order_id')
                            points_added = UserManager.add_points(user_id, amount, order_id)
                            if points_added is not None:
                                stats = UserManager.get_stats(user_id)
                                try:
                                    bot.send_message(user_id,
                                        f"✅ 支付成功！\n订单号: {order_id}\n充值: {amount} USDT\n获得积分: {points_added}\n当前积分: {stats['points']}")
                                except Exception as e:
                                    logger.error(f"发送消息失败: {e}")
                            orders[unique_id]['status'] = 'completed'
                            logger.info(f"订单 {unique_id} 充值成功（轮询）")
            for unique_id in expired_orders:
                user_id = orders[unique_id]['user_id']
                try:
                    bot.send_message(user_id, f"⏰ 订单 {unique_id} 已过期，请重新创建。")
                except Exception as e:
                    logger.error(f"发送消息失败: {e}")
                del orders[unique_id]
                logger.info(f"订单 {unique_id} 已过期")
        except Exception as e:
            logger.error(f"订单检查异常: {e}", exc_info=True)
        time.sleep(CHECK_INTERVAL)

# ============================================================
#  Flask 回调服务
# ============================================================

flask_app = Flask(__name__)

@flask_app.route('/OkPay.php', methods=['POST'])
def callback():
    try:
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        logger.info(f"收到回调: {data}")

        if not client.verify(data):
            logger.error("签名验证失败")
            return jsonify({'status': 'success'}), 200

        if data.get('status') == 'success':
            order_data = data.get('data', {})
            order_type = order_data.get('type')
            order_id = order_data.get('order_id')
            amount = float(order_data.get('amount', 0))
            unique_id = order_data.get('unique_id')

            if order_type == 'deposit' and order_data.get('status') == 1:
                conn = sqlite3.connect('user_points.db')
                c = conn.cursor()
                c.execute('SELECT user_id, status FROM transactions WHERE order_id = ?', (order_id,))
                row = c.fetchone()
                conn.close()

                if not row:
                    logger.warning(f"未找到订单 {order_id}")
                    return jsonify({'status': 'success'}), 200

                user_id, current_status = row
                if current_status == 'completed':
                    logger.info(f"订单 {order_id} 已处理")
                    return jsonify({'status': 'success'}), 200

                points_added = UserManager.add_points(user_id, amount, order_id)
                if points_added is not None:
                    stats = UserManager.get_stats(user_id)
                    try:
                        bot.send_message(user_id,
                            f"✅ 支付成功！（回调）\n订单号: {order_id}\n充值: {amount} USDT\n获得积分: {points_added}\n当前积分: {stats['points']}")
                    except Exception as e:
                        logger.error(f"发送消息失败: {e}")
                    if unique_id and unique_id in orders:
                        orders[unique_id]['status'] = 'completed'
                else:
                    logger.error(f"积分添加失败，订单 {order_id}")

        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.exception("回调处理异常")
        return jsonify({'status': 'success'}), 200

def run_flask():
    logger.info(f"启动 Flask 回调服务，端口 {PORT}")
    flask_app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# ============================================================
#  支付命令
# ============================================================

RECHARGE_AMOUNT = 100

def recharge_start(update, context):
    user_id = update.effective_user.id
    UserManager.create_user(user_id, update.effective_user.username,
                            update.effective_user.first_name, update.effective_user.last_name)
    stats = UserManager.get_stats(user_id)
    update.message.reply_text(
        f"💰 积分充值\n"
        f"当前积分: {stats['points']}\n"
        f"累计充值: {stats['total_recharge']} USDT\n\n"
        f"请输入要充值的 USDT 金额（例如 10）："
    )
    return RECHARGE_AMOUNT

def recharge_amount(update, context):
    user_id = update.effective_user.id
    try:
        amt = float(re.sub(r'[^\d.]', '', update.message.text))
        if amt <= 0:
            raise ValueError
    except:
        update.message.reply_text("❌ 请输入有效的正数金额，例如 10")
        return RECHARGE_AMOUNT

    points = int(amt * POINTS_RATE)
    unique_id = f"ORDER_{int(time.time())}_{user_id}_{random.randint(1000,9999)}"
    resp = client.pay_link(amt, unique_id)
    if not resp or resp.get('status') != 'success':
        error_msg = resp.get('msg', resp.get('error', '未知错误'))
        update.message.reply_text(f"❌ 创建订单失败: {error_msg}")
        logger.error(f"创建订单失败: {resp}")
        return ConversationHandler.END

    order_id = resp['data']['order_id']
    pay_url = resp['data']['pay_url']

    UserManager.create_pending_order(user_id, order_id, unique_id, amt, points)
    orders[unique_id] = {
        'user_id': user_id,
        'amount': amt,
        'order_id': order_id,
        'status': 'pending',
        'timestamp': time.time()
    }

    keyboard = [[InlineKeyboardButton("💳 去支付", url=pay_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        f"✅ 订单已创建\n"
        f"订单号: {order_id}\n"
        f"金额: {amt} USDT → {points} 积分\n"
        f"有效期: 30 分钟\n\n"
        f"点击下方按钮完成支付，系统将自动确认。",
        reply_markup=reply_markup
    )
    logger.info(f"用户 {user_id} 创建订单 {order_id}，金额 {amt} USDT")
    return ConversationHandler.END

def balance(update, context):
    user_id = update.effective_user.id
    stats = UserManager.get_stats(user_id)
    update.message.reply_text(
        f"📊 您的积分: {stats['points']}\n"
        f"累计充值: {stats['total_recharge']} USDT"
    )

# ============================================================
#  Telegram 命令处理
# ============================================================

def start(update, context):
    update.message.reply_text(
        "小宇机器人功能列表：\n"
        "/hainansf +空格+身份证 → 查询海南大头\n"
        "/sfz → 生成标准身份证（双面）\n"
        "/plc → 生成PLC模板身份证\n"
        "/recharge → 充值积分\n"
        "/balance → 查询积分余额\n"
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

# ----- /sfz 对话 -----
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

# ----- /plc 对话 -----
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
    global bot
    updater = Updater(BOT_TOKEN)
    bot = updater.bot
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("hainansf", hainansf))
    dp.add_handler(CommandHandler("balance", balance))
    dp.add_handler(CommandHandler("cancel", cancel))

    conv_recharge = ConversationHandler(
        entry_points=[CommandHandler('recharge', recharge_start)],
        states={
            RECHARGE_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, recharge_amount)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dp.add_handler(conv_recharge)

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

    threading.Thread(target=check_orders, daemon=True).start()
    threading.Thread(target=run_flask, daemon=True).start()

    print("🤖 机器人已启动（身份证生成 + 支付充值 | HMAC-SHA256）")
    logger.info("所有功能已加载，开始轮询...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
