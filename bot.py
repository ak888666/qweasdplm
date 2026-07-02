#!/usr/bin/env python3
import sys
print("===== Bot starting (海南真实查询版) =====")

import asyncio
import io
import os
import time
import json
import requests
import urllib3
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 禁用 SSL 警告（与您的脚本保持一致）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
#  海南查询配置（必须替换为真实值！）
# ============================================================================
FIXED_NAME = "刘德华"                 # 固定姓名（根据接口要求可修改）
SAVE_FOLDER = "temp_files"           # 临时文件目录（机器人会自动清理）
RETRY_TIMES = 5

# ⚠️ 以下所有值必须从浏览器最新抓包中复制，且不能包含中文！
BASE_COOKIES = {
    "cna": "REPLACE_CNA_HERE",          # 替换为实际 cna
    "JSESSIONID": "REPLACE_JSESSIONID_HERE",
    "SESSION": "REPLACE_SESSION_HERE",
    "SERVERID": "REPLACE_SERVERID_HERE",
}

ZWFW_TOKEN = "REPLACE_ZWFW_TOKEN_HERE"   # 替换为真实的 zwfw-token

# 以下两个请求头与您的脚本一致（通常无需修改）
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

# ============================================================================
#  配置检查（防止非 ASCII 字符导致编码错误）
# ============================================================================
def check_ascii_config():
    errors = []
    for key, value in BASE_COOKIES.items():
        try:
            value.encode('ascii')
        except UnicodeEncodeError:
            errors.append(f"BASE_COOKIES['{key}'] = '{value}' 包含非 ASCII 字符")
    try:
        ZWFW_TOKEN.encode('ascii')
    except UnicodeEncodeError:
        errors.append(f"ZWFW_TOKEN = '{ZWFW_TOKEN}' 包含非 ASCII 字符")
    if errors:
        print("=" * 60)
        print("❌ 配置错误：以下变量包含非 ASCII 字符（如中文），必须替换为实际值！")
        for err in errors:
            print(f"  - {err}")
        print("\n请从浏览器最新请求中复制正确的 Cookie 和 zwfw-token 值。")
        print("所有值应为英文、数字、-、_ 等 ASCII 字符。")
        print("=" * 60)
        sys.exit(1)

check_ascii_config()  # 启动时检查

# ============================================================================
#  核心查询函数（同步，返回 (成功, 内容)）
# ============================================================================
def query_id_card(id_card):
    """查询并返回 (成功标志, 二进制数据或错误消息)"""
    # 1. 验证身份证
    id_card = id_card.strip().upper()
    if len(id_card) != 18:
        return False, "身份证号必须为18位"
    if not id_card[:17].isdigit():
        return False, "前17位必须为数字"
    if id_card[17] not in '0123456789X':
        return False, "最后一位必须是数字或X"

    # 2. 创建临时目录（如果不存在）
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)

    session = requests.Session()
    session.cookies.update(BASE_COOKIES)
    session.verify = False

    # 3. 构造第一个请求（获取附件ID）
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
        "userId": "1547878749006024704"   # 如过期需从抓包更新
    }

    for attempt in range(RETRY_TIMES):
        try:
            res1 = session.post(url1, headers=HEADERS1, json=data, timeout=30)
            result1 = res1.json()
        except Exception as e:
            print(f"[{attempt+1}/{RETRY_TIMES}] 请求异常: {e}")
            time.sleep(2)
            continue

        # 调试输出（可在后台查看日志）
        print(f"[{attempt+1}/{RETRY_TIMES}] 服务端返回: {json.dumps(result1, ensure_ascii=False, indent=2)}")

        if result1.get("code") == "1":
            try:
                attachment_id = result1["resultDatas"]["result"]["resultDatas"]["attachmentList"][0]["id"]
                # 4. 下载附件
                url2 = f"https://zwfw.dn.haikou.gov.cn/rest/attachment/{attachment_id}"
                res2 = session.get(url2, headers=HEADERS2, timeout=30)
                if res2.status_code == 200:
                    # 返回二进制内容
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

# ============================================================================
#  Telegram 命令处理
# ============================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 可用命令：\n"
        "/hainansf <身份证号> → 查询海南身份证附件（PDF）\n"
        "\n示例：/hainansf 460101199001011234"
    )

async def hainansf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ 格式错误\n"
            "正确格式：/hainansf <身份证号>\n"
            "示例：/hainansf 460101199001011234"
        )
        return

    id_card = args[0].strip()
    # 简单长度校验（详细校验在 query_id_card 中）
    if len(id_card) != 18:
        await update.message.reply_text("❌ 身份证号必须为18位")
        return

    await update.message.reply_text("⏳ 正在查询海南系统，请稍候...")

    # 异步执行查询（避免阻塞事件循环）
    loop = asyncio.get_event_loop()
    success, result = await loop.run_in_executor(None, query_id_card, id_card)

    if success:
        # result 为二进制数据（PDF 或图片）
        # 发送为文档（因为可能是 PDF）
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=io.BytesIO(result),
            filename=f"{id_card}.pdf",
            caption="✅ 查询成功，附件如下："
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ 查询失败：{result}"
        )

# ============================================================================
#  主程序
# ============================================================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('hainansf', hainansf))
    print("===== Bot is ready (海南真实查询版) =====")
    app.run_polling()

if __name__ == '__main__':
    main()
