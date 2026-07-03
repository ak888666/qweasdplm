#!/usr/bin/env python3
import sys
import os
import json
import time
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ------------------ 日志重定向（确保所有输出都被捕获）------------------
log_file = open("output.log", "a", buffering=1)
sys.stdout = log_file
sys.stderr = log_file

def print_and_log(*args, **kwargs):
    print(*args, **kwargs)
    log_file.flush()

# ------------------ 配置读取 ------------------
def get_env(name):
    val = os.environ.get(name, "").strip()
    if not val:
        return None
    return val

required = [
    "COOKIE_CNA", "COOKIE_JSESSIONID", "COOKIE_SESSION", "COOKIE_SERVERID",
    "ZWFW_TOKEN", "ID_CARD", "TG_BOT_TOKEN", "TG_CHAT_ID"
]
config = {}
missing = []
for v in required:
    val = get_env(v)
    if val is None:
        missing.append(v)
    else:
        config[v] = val

if missing:
    print_and_log("❌ 缺少以下环境变量:", missing)
    sys.exit(1)

# 赋值
BASE_COOKIES = {
    "cna": config["COOKIE_CNA"],
    "JSESSIONID": config["COOKIE_JSESSIONID"],
    "SESSION": config["COOKIE_SESSION"],
    "SERVERID": config["COOKIE_SERVERID"],
}
ZWFW_TOKEN = config["ZWFW_TOKEN"]
ID_CARD = config["ID_CARD"]
TG_BOT_TOKEN = config["TG_BOT_TOKEN"]
TG_CHAT_ID = config["TG_CHAT_ID"]

FIXED_NAME = os.environ.get("FIXED_NAME", "刘德华")
SAVE_FOLDER = "output"
RETRY_TIMES = 3

print_and_log("✅ 所有环境变量已读取，开始查询...")

# ------------------ Telegram 通知 ------------------
def send_tg_message(text):
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text}, timeout=10)
        print_and_log(f"TG 响应: {r.status_code} {r.text}")
    except Exception as e:
        print_and_log(f"TG 发送失败: {e}")

# ------------------ 查询逻辑 ------------------
def query():
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)

    session = requests.Session()
    session.cookies.update(BASE_COOKIES)
    session.verify = False

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
        "userId": "1547878749006024704"
    }

    for i in range(RETRY_TIMES):
        try:
            res1 = session.post(url1, headers=HEADERS1, json=data, timeout=30)
            result1 = res1.json()
        except Exception as e:
            msg = f"[{i+1}/{RETRY_TIMES}] 请求异常: {e}"
            print_and_log(msg)
            time.sleep(2)
            continue

        print_and_log(f"[{i+1}/{RETRY_TIMES}] 服务端返回: {json.dumps(result1, ensure_ascii=False, indent=2)}")

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
                print_and_log(f"详细错误: {detail}")
            print_and_log(f"[{i+1}/{RETRY_TIMES}] 查询失败: {msg}")
            time.sleep(2)

    return False, f"连续 {RETRY_TIMES} 次查询均失败"

def main():
    try:
        success, msg = query()
        print_and_log(msg)
        send_tg_message(msg)
    except Exception as e:
        print_and_log(f"❌ 未捕获的异常: {e}")
        import traceback
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

if __name__ == "__main__":
    main()
    # 确保日志文件被刷新
    log_file.close()
