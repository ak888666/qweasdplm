# query_helper.py
import asyncio
import sys
import requests
import json
import os
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== 配置（必须全 ASCII）==========
FIXED_NAME = "刘德华"
SAVE_FOLDER = "海南"
RETRY_TIMES = 5

BASE_COOKIES = {
    "cna": "REPLACE_CNA_HERE",
    "JSESSIONID": "REPLACE_JSESSIONID_HERE",
    "SESSION": "REPLACE_SESSION_HERE",
    "SERVERID": "REPLACE_SERVERID_HERE",
}
ZWFW_TOKEN = "REPLACE_ZWFW_TOKEN_HERE"

# ========== 配置检查 ==========
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
        print("配置错误:", errors)
        sys.exit(1)

check_ascii_config()

HEADERS1 = { ... }   # 同原脚本
HEADERS2 = { ... }

def validate_id_card(id_card):
    # 同原脚本
    ...

def query_id_card_sync(id_card):
    # 原 query_id_card 函数体，返回值 (success, msg)
    ...

# 异步包装器
async def query_id_card_async(id_card):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, query_id_card_sync, id_card)
