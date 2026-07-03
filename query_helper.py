# query_helper.py
import asyncio
import sys
import requests
import json
import os
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== 从环境变量读取配置 ==========
FIXED_NAME = "刘德华"               # 可保留固定值，或也从环境变量读取
SAVE_FOLDER = "海南"
RETRY_TIMES = 5

# 必须从环境变量读取
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ZWFW_TOKEN = os.environ.get("ZWFW_TOKEN", "")
BASE_COOKIES = {
    "cna": os.environ.get("CNA", ""),
    "JSESSIONID": os.environ.get("JSESSIONID", ""),
    "SESSION": os.environ.get("SESSION", ""),
    "SERVERID": os.environ.get("SERVERID", ""),
}

# 检查是否所有必需的环境变量都已设置
if not all([BOT_TOKEN, ZWFW_TOKEN] + list(BASE_COOKIES.values())):
    print("❌ 环境变量缺失，请检查 Secrets 设置")
    print("需要: BOT_TOKEN, ZWFW_TOKEN, CNA, JSESSIONID, SESSION, SERVERID")
    sys.exit(1)

# ========== 请求头（完全照搬原脚本）==========
HEADERS1 = {
    "Host": "zwfw.dn.haikou.gov.cn",
    "Connection": "keep-alive",
    "sec-ch-ua-platform": "\"Android\"",
    "zwfw-token": ZWFW_TOKEN,   # 使用环境变量值
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

# ========== 工具函数 ==========
def validate_id_card(id_card):
    id_card = id_card.strip().upper()
    if len(id_card) != 18:
        return False, "身份证号必须为18位"
    if not id_card[:17].isdigit():
        return False, "前17位必须为数字"
    if id_card[17] not in '0123456789X':
        return False, "最后一位必须是数字或X"
    return True, id_card

def query_id_card_sync(id_card):
    ok, id_card = validate_id_card(id_card)
    if not ok:
        return False, id_card

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
        "userId": "1547878749006024704"   # 可能需要更新
    }

    for i in range(RETRY_TIMES):
        try:
            res1 = session.post(url1, headers=HEADERS1, json=data, timeout=30)
            result1 = res1.json()
        except Exception as e:
            print(f"[{i+1}/{RETRY_TIMES}] 请求异常: {e}")
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
                return True, f"成功! 文件已保存至: {filepath}"
            except (KeyError, IndexError, AttributeError) as e:
                return False, f"解析下载数据失败: {e},返回内容: {result1}"
        else:
            msg = result1.get('message', '未知错误')
            if 'resultDatas' in result1:
                detail = result1['resultDatas']
                print(f"详细错误: {detail}")
            print(f"[{i+1}/{RETRY_TIMES}] 查询失败: {msg}")
            time.sleep(2)

    return False, f"连续 {RETRY_TIMES} 次查询均失败,请检查 Cookie/Token 是否有效"

# ========== 异步包装器 ==========
async def query_id_card_async(id_card):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, query_id_card_sync, id_card)
