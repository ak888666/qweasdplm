#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
print("===== Bot 五功能版 (hainansf / sfz / plc / wh / hb) =====")

import os
import time
import json
import io
import tempfile
import re
import base64
import urllib.parse
import requests
import urllib3
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater, CommandHandler, ConversationHandler,
    MessageHandler, Filters, CallbackQueryHandler
)

# ---------- 禁用 SSL 警告 ----------
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
#  ⚠️ Telegram Bot Token
# ============================================================
BOT_TOKEN = "5849383582:AAGSJs4OWCs8pYd9oUFwHbZHpaUBM3CYgXw"

# ============================================================
#  ⚠️ 海南系统配置
# ============================================================
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

HEADERS1 = {
    "Host": "zwfw.dn.haikou.gov.cn",
    "Connection": "keep-alive",
    "sec-ch-ua-platform": "\"Android\"",
    "zwfw-token": ZWFW_TOKEN,
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; MEIZU 21 Build/UKQ1.230917.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/141.0.7390.97 Mobile Safari/537.36 AgentWeb/5.0.0  yssApp",
    "sec-ch-ua": "\"Android WebView\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
    "sec-ch-ua-mobile": "?1",
    "content-type": "application/json",
    "Accept": "*/*",
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

# ============================================================
#  ⚠️ 威海查询功能（/wh）
# ============================================================
WEIHAI_AUTH = "你的真实Authorization"  # ⚠️ 请替换为真实值
WEIHAI_REFERER = "你的真实Referer"  # ⚠️ 请替换为真实值

def query_weihai(idcard):
    """查询威海动物诊疗许可证"""
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Authorization': WEIHAI_AUTH,
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://whzhsp.weihai.cn',
        'Referer': WEIHAI_REFERER,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not_A Brand";v="99", "Chromium";v="142"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    json_data_query = {
        'itemCode': '37100001000055',
        'itemName': '动物诊疗许可证核发',
        'holderCode': idcard,
        'holderTypeCode': '111',
        'certTypeCode': '11100000000013127D001',
    }

    try:
        response_query = requests.post(
            'https://whzhsp.weihai.cn/gate/data/license/queryCertInfoByHolderCode',
            headers=headers,
            json=json_data_query,
            timeout=30
        )
        response_query.raise_for_status()
        res_dict = response_query.json()
    except Exception as e:
        return False, f"查询失败: {e}"

    if "data" in res_dict and len(res_dict["data"]) > 0:
        target_info = res_dict["data"][0]
        zzyxqjzrq = target_info.get("zzyxqjzrq")
        cert_identifier = target_info.get("cert_identifier")
        if not zzyxqjzrq or not cert_identifier:
            return False, "未获取到有效参数"
    else:
        return False, f"无数据: {res_dict.get('msg', '未知错误')}"

    json_data_download = {
        "itemCode": "37100001000055",
        "itemName": "动物诊疗许可证核发",
        "fileType": "ofd",
        "certificateIdentifier": cert_identifier,
        "certificateCopyExpiringTime": zzyxqjzrq
    }

    try:
        res_download = requests.post(
            "https://whzhsp.weihai.cn/gate/data/license/getDownloadFileWeiHai",
            headers=headers,
            json=json_data_download,
            timeout=30
        )
        res_download.raise_for_status()
        download_data = res_download.text
        outer_data = json.loads(download_data)
        inner_data = json.loads(outer_data["data"])
        uuid = inner_data.get("uuid")
        if not uuid:
            return False, "未获取到文件UUID"
    except Exception as e:
        return False, f"下载请求失败: {e}"

    url = f"https://whzhsp.weihai.cn/gate/custom/file/downloadFile?doc_id={uuid}&fileName={idcard}.jpg"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return True, response.content
    except Exception as e:
        return False, f"文件下载失败: {e}"

# ============================================================
#  ⚠️ 湖北查询功能（/hb）
# ============================================================
HB_KEY = b"ZBYSC2SGOYBVVHUZ"

# ===== 纯 Python 实现 AES-ECB 加密 =====
Sbox = [
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16
]
Rcon = [0x8d, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]

def sub_bytes(state):
    for i in range(4):
        for j in range(4):
            state[i][j] = Sbox[state[i][j]]

def shift_rows(state):
    state[1] = state[1][1:] + state[1][:1]
    state[2] = state[2][2:] + state[2][:2]
    state[3] = state[3][3:] + state[3][:3]

def mix_columns(state):
    for i in range(4):
        s0, s1, s2, s3 = state[0][i], state[1][i], state[2][i], state[3][i]
        state[0][i] = gf_mul(s0, 2) ^ gf_mul(s1, 3) ^ s2 ^ s3
        state[1][i] = s0 ^ gf_mul(s1, 2) ^ gf_mul(s2, 3) ^ s3
        state[2][i] = s0 ^ s1 ^ gf_mul(s2, 2) ^ gf_mul(s3, 3)
        state[3][i] = gf_mul(s0, 3) ^ s1 ^ s2 ^ gf_mul(s3, 2)

def gf_mul(a, b):
    res = 0
    for _ in range(8):
        if b & 1:
            res ^= a
        hi = a & 0x80
        a <<= 1
        if hi:
            a ^= 0x1b
        b >>= 1
    return res & 0xff

def add_round_key(state, round_key):
    for i in range(4):
        for j in range(4):
            state[i][j] ^= round_key[i][j]

def key_schedule(key):
    key_flat = [b for b in key]
    expanded_key = [key_flat[i:i+4] for i in range(0, len(key_flat), 4)]
    for i in range(4, 44):
        temp = expanded_key[i-1][:]
        if i % 4 == 0:
            temp = temp[1:] + temp[:1]
            temp = [Sbox[b] for b in temp]
            temp[0] ^= Rcon[i//4]
        expanded_key.append([expanded_key[i-4][j] ^ temp[j] for j in range(4)])
    return expanded_key

def aes_encrypt(plaintext, key):
    state = [[plaintext[i + 4*j] for j in range(4)] for i in range(4)]
    expanded_key = key_schedule(key)
    round_key = [expanded_key[i] for i in range(4)]
    add_round_key(state, round_key)
    for round_num in range(1, 10):
        sub_bytes(state)
        shift_rows(state)
        mix_columns(state)
        round_key = [expanded_key[round_num*4 + i] for i in range(4)]
        add_round_key(state, round_key)
    sub_bytes(state)
    shift_rows(state)
    round_key = [expanded_key[40 + i] for i in range(4)]
    add_round_key(state, round_key)
    result = bytearray(16)
    for i in range(4):
        for j in range(4):
            result[i + 4*j] = state[i][j]
    return bytes(result)

def pkcs7_pad(data, block_size=16):
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len]) * pad_len

def aes_ecb_encrypt(plaintext: str, key: bytes = HB_KEY, url_safe: bool = True) -> str:
    plain_bytes = plaintext.encode('utf-8')
    padded = pkcs7_pad(plain_bytes, 16)
    ciphertext = b''
    for i in range(0, len(padded), 16):
        block = padded[i:i+16]
        ciphertext += aes_encrypt(block, key)
    b64 = base64.b64encode(ciphertext).decode()
    return urllib.parse.quote(b64, safe="") if url_safe else b64

def query_hubei(idcard):
    """查询湖北市场监管证照"""
    LIST_API = "https://scjg.hubei.gov.cn/hbzhspyzw/sc/xzspMain/api/dynamicFileRecord/listInternetFile"
    LIST_HEADERS = {
        "Host": "scjg.hubei.gov.cn",
        "Connection": "keep-alive",
        "sec-ch-ua": '"Not A(Brand";v="99", "Android WebView";v="121", "Chromium";v="121"',
        "isToken": "true",
        "sec-ch-ua-mobile": "?1",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; MI 8 Build/QKQ1.190828.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/121.0.6167.71 COVC/048603 Mobile Safari/537.36",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "productItemClass": "",
        "sec-ch-ua-platform": '"Android"',
        "Origin": "https://scjg.hubei.gov.cn",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    payload_plain = json.dumps({
        "type": "",
        "CertificateType": "",
        "itemCode": "11420000MB1686999B2420131004W0014",
        "holdCode": idcard,
        "operName": ""
    }, separators=(',', ':'))
    encrypt_body = aes_ecb_encrypt(payload_plain)
    req_body = json.dumps({"encryptBody": encrypt_body}, separators=(',', ':'))

    try:
        resp = requests.post(LIST_API, headers=LIST_HEADERS, data=req_body.encode("utf-8"), timeout=30, verify=False)
        resp.raise_for_status()
        res_json = resp.json()
        if res_json.get("code") != 200:
            return False, f"查询失败：{res_json.get('message')}"
        data_list = res_json.get("data", [])
        if not data_list:
            return False, "该身份证无证照记录"
    except Exception as e:
        return False, f"请求异常：{e}"

    # 下载所有证照
    results = []
    for i, item in enumerate(data_list, 1):
        cert_id = item.get("certificateID")
        cert_name = item.get("certificateType", f"证照_{i}")
        if not cert_id:
            continue
        
        dl_url = f"https://zwfw.hubei.gov.cn/hbonething/web/file/download?fileId={cert_id}&filename=1.jpg"
        try:
            resp = requests.get(dl_url, timeout=30, verify=False)
            if resp.status_code == 200:
                results.append({
                    "name": cert_name,
                    "data": resp.content,
                    "index": i
                })
        except:
            pass

    if not results:
        return False, "未获取到任何证照图片"

    return True, results

# ============================================================
#  通用去白底函数
# ============================================================
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

# ============================================================
#  /sfz 生成身份证
# ============================================================
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

# ============================================================
#  /plc 生成PLC模板
# ============================================================
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
#  Telegram 入口命令
# ============================================================
def start(update, context):
    update.message.reply_text(
        "小宇：\n"
        "/hainansf +空格+ 身份证→查询海南大头\n"
        "/sfz → 生成双面身份证·自动签发机关\n"
        "/plc → 生成PLC模板自动地址·按钮确认或手动输入\n"
        "/wh 身份证号 → 查询威海动物诊疗许可证\n"
        "/hb 身份证号 → 查询湖北市场监管证照\n"
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
