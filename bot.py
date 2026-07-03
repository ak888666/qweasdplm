#!/usr/bin/env python3
import requests
import json
import os
import time
import urllib3
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== 配置区域（请替换为你的真实值） ==========
# 固定业务参数
FIXED_NAME = "刘德华"                # 委托书中的姓名，根据实际情况修改
SAVE_FOLDER = "output"              # 保存 PDF 的文件夹
RETRY_TIMES = 3

# 以下四项必须从浏览器抓包获取（替换引号内的值）
BASE_COOKIES = {
    "cna": "你的cna值",
    "JSESSIONID": "你的JSESSIONID值",
    "SESSION": "你的SESSION值",
    "SERVERID": "你的SERVERID值",
}
ZWFW_TOKEN = "你的zwfw-token值"     # 替换为真实 token

# 用户输入身份证号（交互式输入，所以这里不设默认）
# ID_CARD 在 main 中由用户输入

# ========== Telegram 机器人配置（已替你填好） ==========
TG_BOT_TOKEN = "5849383582:AAF7VKPb6rzyv0Xk5AL2YypQxunktRaTJHw"   # 你的 Token
TG_CHAT_ID = "6040143940"           # 从 getUpdates 中获取的 Chat ID

# 若上面的 Token 已失效，请在 @BotFather 重置后替换。

# ---------- 以下函数无需修改 ----------
def send_tg_message(text):
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"TG 发送失败: {e}")

def query(id_card):
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
            "cardid": id_card,
            "dzzz_type": "1"
        },
        "itemId": "1047370300041120912",
        "userId": "1547878749006024704"   # 可能需要更新，请抓包确认
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
                filename = f"{id_card}.pdf"
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

    return False, f"连续 {RETRY_TIMES} 次查询均失败，请检查 Cookie/Token 是否有效"

def main():
    print("="*50)
    print("海口政务身份证查询（带 TG 通知）")
    print("="*50)
    id_card = input("请输入身份证号: ").strip()
    if not id_card:
        print("身份证号不能为空")
        return

    success, msg = query(id_card)
    print(msg)
    send_tg_message(msg)

if __name__ == "__main__":
    main()
