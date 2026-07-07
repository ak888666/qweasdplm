#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并版机器人：身份证生成 + OkayPay 自助充值
"""

import sys
print("===== Bot 完整版 (身份证生成 + 支付充值) =====")

import os
import time
import json
import io
import tempfile
import requests
import urllib3
import sqlite3
import hashlib
import urllib.parse
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

# ---------- 禁用 SSL 警告 ----------
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------- 日志配置 ----------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MergedBot')

# ============================================================
#   ⚠️ 必填项：请将下方 Token / Cookie / 支付密钥替换为真实数据
# ============================================================
BOT_TOKEN = "5849383582:AAGSJs4OWCs8pYd9oUFwHbZHpaUBM3CYgXw"   # 替换为您的机器人 Token

# ----- 海南查询接口 Cookie -----
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

# ----- OkayPay 支付配置 -----
OKPAY_ID = 123456                    # 替换为您的商户ID
OKPAY_TOKEN = 'your_merchant_token'  # 替换为您的商户秘钥
OKPAY_API_URL = 'https://api.okaypay.me/shop/'
CALLBACK_URL = 'https://你的域名/OkPay.php'  # 必须外网可访问
PORT = 1010                         # Flask 监听端口
POINTS_RATE = 1                     # 1 USDT = 1 积分
CHECK_INTERVAL = 0.5                # 轮询间隔（秒）
ORDER_TIMEOUT = 1800                # 订单超时（秒）

# ============================================================
#  1. 身份证生成相关函数（原有，保持不变）
# ============================================================
HEADERS1 = { ... }  # 原代码中的 HEADERS1，此处省略（请保留原样）
HEADERS2 = { ... }  # 原代码中的 HEADERS2，此处省略（请保留原样）

def query_id_card_sync(id_card):
    # 原函数，保持不变
    pass

def remove_white_background(img, threshold=240):
    # 原函数，保持不变
    pass

def load_issuing_authority_map(file_path):
    # 原函数，保持不变
    pass

def get_issuing_authority(id_number, issuing_authority_map):
    # 原函数，保持不变
    pass

def format_address(address, max_chars_per_line=11):
    # 原函数，保持不变
    pass

def generate_id_card_sync(name, id_number, nation, address, expiration_date, user_photo_path):
    # 原函数，保持不变
    pass

def load_area_map():
    # 原函数，保持不变
    pass

AREA_MAP = load_area_map()

def get_address_from_idcard(id_card):
    # 原函数，保持不变
    pass

def generate_plc_sync(name, id_card, address, avatar_path):
    # 原函数，保持不变
    pass

# ============================================================
#  2. 支付模块（新增）
# ============================================================

# ---------- 数据库初始化 ----------
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

# ---------- 用户积分管理 ----------
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

# ---------- OkayPay API 客户端 ----------
class OkayPay:
    def __init__(self, appid, token, api_url):
        self.appid = appid
        self.token = token
        self.api_url = api_url

    def _sign(self, params):
        params = {k: v for k, v in params.items() if v is not None and v != ''}
        params['id'] = str(self.appid)
        sorted_params = dict(sorted(params.items()))
        query_string = urllib.parse.urlencode(sorted_params)
        sign_str = urllib.parse.unquote(query_string) + '&token=' + self.token
        sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
        return sign

    def verify_sign(self, data):
        """验证回调签名，与 PHP 的 checkSign 逻辑一致"""
        if 'sign' not in data:
            logger.error("回调数据缺少 sign 字段")
            return False
        in_sign = data['sign']
        params = data.copy()
        params.pop('sign')
        params = {k: v for k, v in params.items() if v is not None and v != ''}
        sorted_params = dict(sorted(params.items()))
        query_string = urllib.parse.urlencode(sorted_params)
        sign_str = urllib.parse.unquote(query_string) + '&token=' + self.token
        calc_sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
        logger.debug(f"回调签名原串: {sign_str}")
        logger.debug(f"计算签名: {calc_sign}, 接收签名: {in_sign}")
        return calc_sign == in_sign

    def pay_link(self, amount, unique_id):
        logger.info(f"创建支付链接 - 金额: {amount}, 订单号: {unique_id}")
        params = {
            'unique_id': unique_id,
            'name': '积分充值',
            'amount': str(amount),
            'coin': 'USDT',
            'return_url': CALLBACK_URL
        }
        sign = self._sign(params)
        submit_params = params.copy()
        submit_params['id'] = str(self.appid)
        submit_params['sign'] = sign

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        try:
            api_url = self.api_url + 'payLink'
            resp = requests.post(api_url, data=submit_params, headers=headers, timeout=15, verify=False)
            if resp.status_code == 200:
                result = resp.json()
                logger.info(f"支付链接响应: {result}")
                return result
            else:
                error_result = {'error': f'HTTP {resp.status_code}', 'body': resp.text}
                logger.error(f"API请求失败: {error_result}")
                return error_result
        except Exception as e:
            logger.error(f"请求异常: {e}", exc_info=True)
            return {'error': str(e)}

    def check_deposit(self, unique_id):
        logger.info(f"检查充值状态 - unique_id: {unique_id}")
        params = {'unique_id': unique_id}
        sign = self._sign(params)
        submit_params = params.copy()
        submit_params['id'] = str(self.appid)
        submit_params['sign'] = sign

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        try:
            api_url = self.api_url + 'checkDeposit'
            resp = requests.post(api_url, data=submit_params, headers=headers, timeout=15, verify=False)
            if resp.status_code == 200:
                result = resp.json()
                logger.info(f"检查响应: {result}")
                return result
            else:
                error_result = {'error': f'HTTP {resp.status_code}', 'body': resp.text}
                logger.error(f"API请求失败: {error_result}")
                return error_result
        except Exception as e:
            logger.error(f"请求异常: {e}", exc_info=True)
            return {'error': str(e)}

client = OkayPay(OKPAY_ID, OKPAY_TOKEN, OKPAY_API_URL)

# ---------- 订单内存存储 ----------
orders = {}  # unique_id -> {user_id, amount, order_id, status, timestamp}

# ---------- 轮询检查线程 ----------
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
                    if result and 'data' in result:
                        status = result['data'].get('status')
                        if status == 1:
                            user_id = order_info['user_id']
                            amount = float(result['data'].get('amount', 0))
                            order_id = result['data'].get('order_id')
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

# ---------- Flask 回调服务 ----------
flask_app = Flask(__name__)

@flask_app.route('/OkPay.php', methods=['POST'])
def callback():
    try:
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        logger.info(f"收到回调: {data}")

        if not client.verify_sign(data):
            logger.error("签名验证失败")
            return jsonify({'status': 'success'}), 200

        if data.get('type') == 'deposit' and data.get('status') == 1:
            order_id = data.get('order_id')
            amount = float(data.get('amount', 0))
            unique_id = data.get('unique_id')

            if not order_id:
                logger.warning("回调缺少 order_id")
                return jsonify({'status': 'success'}), 200

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
                        f"✅ 支付成功！（实时回调）\n订单号: {order_id}\n充值: {amount} USDT\n获得积分: {points_added}\n当前积分: {stats['points']}")
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

# ---------- 支付命令（/recharge） ----------
RECHARGE_AMOUNT = 100  # 状态：等待输入金额

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
    if not resp or 'data' not in resp:
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

# ---------- 余额查询 ----------
def balance(update, context):
    user_id = update.effective_user.id
    stats = UserManager.get_stats(user_id)
    update.message.reply_text(
        f"📊 您的积分: {stats['points']}\n"
        f"累计充值: {stats['total_recharge']} USDT"
    )

# ============================================================
#  3. Telegram 命令处理（原有 + 新增支付）
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
    # 原有函数，保持不变
    pass

def cancel(update, context):
    update.message.reply_text("已取消")
    context.user_data.clear()
    return ConversationHandler.END

# ----- /sfz 对话（原有，不变）-----
SFZ_NAME, SFZ_ID, SFZ_NATION, SFZ_ADDR, SFZ_EXPIRY, SFZ_PHOTO = range(6)
def sfz_start(update, context):
    update.message.reply_text("📝 开始生成身份证（标准模板），请输入姓名：")
    return SFZ_NAME
# ... 其余 sfz_* 函数保持不变（略，请保留原代码）

# ----- /plc 对话（原有，不变）-----
PLC_NAME, PLC_ID, PLC_ADDR_CONFIRM, PLC_ADDR_MANUAL, PLC_PHOTO = range(10, 15)
def plc_start(update, context):
    update.message.reply_text("📝 开始生成身份证（PLC模板），请输入姓名：")
    return PLC_NAME
# ... 其余 plc_* 函数保持不变（略，请保留原代码）

# 注意：由于代码长度限制，此处仅展示新增部分，您需要将原有的 sfz_* 和 plc_* 函数完整保留。

# ============================================================
#  4. 主程序
# ============================================================

def main():
    global bot  # 使其他线程能使用 bot 发送消息
    updater = Updater(BOT_TOKEN)
    bot = updater.bot
    dp = updater.dispatcher

    # ---- 普通命令 ----
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("hainansf", hainansf))
    dp.add_handler(CommandHandler("balance", balance))
    dp.add_handler(CommandHandler("cancel", cancel))

    # ---- /recharge 对话 ----
    conv_recharge = ConversationHandler(
        entry_points=[CommandHandler('recharge', recharge_start)],
        states={
            RECHARGE_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, recharge_amount)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dp.add_handler(conv_recharge)

    # ---- /sfz 对话（保持不变） ----
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

    # ---- /plc 对话（保持不变） ----
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

    # ---- 启动轮询线程 ----
    threading.Thread(target=check_orders, daemon=True).start()

    # ---- 启动 Flask 回调服务线程 ----
    threading.Thread(target=run_flask, daemon=True).start()

    print("🤖 机器人已启动（身份证生成 + 支付充值）")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
