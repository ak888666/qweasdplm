#!/usr/bin/env python3
import requests
import json
import os
import time
import urllib3
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------- 所有敏感信息均从环境变量读取 ----------
BASE_COOKIES = {
    "cna": os.environ.get("COOKIE_CNA", ""),
    "JSESSIONID": os.environ.get("COOKIE_JSESSIONID", ""),
    "SESSION": os.environ.get("COOKIE_SESSION", ""),
    "SERVERID": os.environ.get("COOKIE_SERVERID", ""),
}
ZWFW_TOKEN = os.environ.get("ZWFW_TOKEN", "")
ID_CARD = os.environ.get("ID_CARD", "").strip()
FIXED_NAME = os.environ.get("FIXED_NAME", "刘德华")   # 默认值，也可从环境变量定制
SAVE_FOLDER = "output"
RETRY_TIMES = 3

# Telegram 配置
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")

# ---------- 配置完整性检查 ----------
def check_config():
    errors = []
    for key, value in BASE_COOKIES.items():
        if not value:
            errors.append(f"缺少环境变量 COOKIE_{key.upper()}")
    if not ZWFW_TOKEN:
        errors.append("缺少 ZWFW_TOKEN")
    if not ID_CARD:
        errors.append("缺少 ID_CARD（要查询的身份证号）")
    if not TG_BOT_TOKEN:
        errors.append("缺少 TG_BOT_TOKEN")
    if not TG_CHAT_ID:
        errors.append("缺少 TG_CHAT_ID")
    if errors:
        print("❌ 配置错误:")
        for e in errors:
            print(f"  - {e}")
        return False
    return True

# ---------- Telegram 通知 ----------
def send_tg_message(text):
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"TG 发送失败: {e}")

# ---------- 查询核心逻辑 ----------
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

def query():
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
            "cardid": ID_CARD,
            "dzzz_type": "1"
        },
        "itemId": "1047370300041120912",
        "userId": "1547878749006024704"   # 注意：此值可能需要从最新抓包更新
    }

    for i in range(RETRY_TIMES):
        try:
            res1 = session.post(url1, headers=HEADERS1, json=data, timeout=30)
            result1 = res1.json()
        except Exception as e:
            msg = f"[{i+1}/{RETRY_TIMES}] 请求异常: {e}"
            print(msg)
            time.sleep(2)
            continue

        print(f"[{i+1}/{RETRY_TIMES}] 服务端返回: {json.dumps(result1, ensure_ascii=False, indent=2)}")

        if result1.get("code") == "1":
            try:
                attachment_id = result1["resultDatas"]["result"]["resultDatas"]["attachmentList"][0]["id"]
                url2 = f"https://zwfw.dn.haikou.gov.cn/rest/attachment/{attachment_id}"
                res2 = session.get(url2, headers=HEADERS2, timeout=30)
                filename = f"{ID_CARD}.pdf"
                filepath = os.path.join(SAVE_FOLDER, filename)
                with open(filepath, 'wb') as f:
                    f.write(res2.content)
                return True, f"✅ 查询成功！文件已保存: {filepath}"
            except (KeyError, IndexError, AttributeError) as e:
                return False, f"解析下载数据失败: {e}, 返回内容: {result1}"
        else:
            msg = result1.get('message', '未知错误')
            if 'resultDatas' in result1:
                detail = result1['resultDatas']
                print(f"详细错误: {detail}")
            print(f"[{i+1}/{RETRY_TIMES}] 查询失败: {msg}")
            time.sleep(2)

    return False, f"连续 {RETRY_TIMES} 次查询均失败,请检查 Cookie/Token 是否有效"

# ---------- 主程序 ----------
def main():
    if not check_config():
        send_tg_message("❌ 配置错误，请检查环境变量。")
        sys.exit(1)

    success, msg = query()
    print(msg)
    send_tg_message(msg)

if __name__ == "__main__":
    main()
