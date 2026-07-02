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

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
#  ⚠️ 以下所有配置必须替换为您的真实值！
# ============================================================================
BOT_TOKEN = "5849383582:AAHIfKvl2O3buRgiIq4rwtC4b95KsP3BfS4"   # 您的 Bot Token（已填）

# 以下从浏览器抓包获取（必须替换！）
BASE_COOKIES = {
    "cna": "REPLACE_CNA_HERE",
    "JSESSIONID": "REPLACE_JSESSIONID_HERE",
    "SESSION": "REPLACE_SESSION_HERE",
    "SERVERID": "REPLACE_SERVERID_HERE",
}
ZWFW_TOKEN = "REPLACE_ZWFW_TOKEN_HERE"

# 其他参数（通常无需改动）
FIXED_NAME = "刘德华"
SAVE_FOLDER = "temp_files"
RETRY_TIMES = 5

# ============================================================================
#  请求头（自动使用上面的 ZWFW_TOKEN）
# ============================================================================
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
#  配置检查（确保必填项不为空）
# ============================================================================
def check_config():
    errors = []
    if any(v == "请替换为实际cna值" or v == "" for v in BASE_COOKIES.values()):
        errors.append("BASE_COOKIES 中有未替换的占位符或空值")
    if ZWFW_TOKEN == "请替换为实际zwfw-token值" or not ZWFW_TOKEN:
        errors.append("ZWFW_TOKEN 未替换")
    if errors:
        print("=" * 60)
        print("❌ 配置错误：")
        for err in errors:
            print(f"  - {err}")
        print("\n请从浏览器抓包获取真实的 Cookie 和 zwfw-token，然后替换代码中的对应位置。")
        print("=" * 60)
        sys.exit(1)

check_config()

# ============================================================================
#  核心查询函数
# ============================================================================
def query_id_card(id_card):
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

# ============================================================================
#  Telegram 命令
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
    if len(id_card) != 18:
        await update.message.reply_text("❌ 身份证号必须为18位")
        return

    await update.message.reply_text("⏳ 正在查询海南系统，请稍候...")

    loop = asyncio.get_event_loop()
    success, result = await loop.run_in_executor(None, query_id_card, id_card)

    if success:
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
