import os
import time
import requests
from flask import Flask, request
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# User Bot Token
TOKEN = "8785462549:AAEDI_fiJJXAOaVFFWhGChGQT3VnmzskDWQ"
bot = telebot.TeleBot(TOKEN, threaded=False)

# Flask App
app = Flask(__name__)

# Firebase Realtime Database URL
FIREBASE_URL = "https://flashlotter-default-rtdb.europe-west1.firebasedatabase.app"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    else:
        return "Internal Server Error", 403

@app.route('/')
def home():
    return "User BetBot Webhook is Active!"

def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🎲 Big / Small (Formula 1)"),
        KeyboardButton("🔥 Big / Small (Formula 2)"),
        KeyboardButton("⏳ ကျန်ရှိချိန် စစ်ဆေးရန်"),
        KeyboardButton("🛑 Stop"),
        KeyboardButton("▶️ Start")
    )
    return markup

# 🚀 /start Command
@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = str(message.chat.id)
    current_time = int(time.time() * 1000)
    
    try:
        response = requests.get(f"{FIREBASE_URL}/users/{chat_id}.json")
        user_data = response.json()
    except:
        user_data = None

    if not user_data:
        initial_data = {
            'checkId': chat_id,
            'tgName': message.from_user.first_name or "User",
            'status': True,
            'mode': 'timed',
            'startTime': current_time,
            'duration': 10 * 60 * 1000,
            'elapsed': 0
        }
        requests.put(f"{FIREBASE_URL}/users/{chat_id}.json", json=initial_data)
        bot.send_message(
            message.chat.id, 
            "✨ **ကြိုဆိုပါတယ်!**\n၁၀ မိနစ် စမ်းသပ်သုံးခွင့် အလိုအလျောက် ပေးလိုက်ပါပြီ။ အောက်ပါမီနူးများမှ အသုံးပြုနိုင်ပါပြီ -", 
            reply_markup=get_main_menu(), 
            parse_mode="Markdown"
        )
        return

    status = user_data.get('status', False)
    mode = user_data.get('mode', '')

    if mode == 'always':
        bot.send_message(message.chat.id, "✨ အမြဲတမ်း အသုံးပြုခွင့် ရှိပါသည်။", reply_markup=get_main_menu())
        return

    start_time = user_data.get('startTime', 0)
    duration = user_data.get('duration', 600000)
    elapsed_before = user_data.get('elapsed', 0)

    if start_time == 0:
        requests.patch(f"{FIREBASE_URL}/users/{chat_id}.json", json={
            'startTime': current_time,
            'status': True,
            'mode': 'timed'
        })
        bot.send_message(
            message.chat.id, 
            "▶️ **အချိန်စတင်ရေတွက်နေပါပြီ (၁၀ မိနစ်)။**\nအောက်ပါမီနူးများမှ ဆက်လက်အသုံးပြုနိုင်ပါပြီ -", 
            reply_markup=get_main_menu(), 
            parse_mode="Markdown"
        )
    else:
        current_session_elapsed = current_time - start_time
        total_elapsed = elapsed_before + current_session_elapsed
        remaining_ms = duration - total_elapsed

        if remaining_ms <= 0:
            requests.patch(f"{FIREBASE_URL}/users/{chat_id}.json", json={
                'status': False,
                'startTime': 0,
                'elapsed': duration
            })
            bot.send_message(message.chat.id, "⏰ **အချိန်ကုန်ဆုံးသွားပါပြီ။**", parse_mode="Markdown")
        else:
            bot.send_message(
                message.chat.id, 
                "▶️ **Bot ကို ပြန်လည်စတင်လိုက်ပါပြီ။** ဆက်လက်အသုံးပြုနိုင်ပါပြီ -", 
                reply_markup=get_main_menu(), 
                parse_mode="Markdown"
            )

@bot.message_handler(func=lambda message: message.text in ["🛑 Stop", "stop", "STOP"])
def stop_command(message):
    chat_id = str(message.chat.id)
    current_time = int(time.time() * 1000)
    
    try:
        response = requests.get(f"{FIREBASE_URL}/users/{chat_id}.json")
        user_data = response.json()
    except:
        user_data = None

    if not user_data:
        bot.send_message(message.chat.id, "❌ အချက်အလက် မရှိပါ။")
        return

    start_time = user_data.get('startTime', 0)
    duration = user_data.get('duration', 600000)
    elapsed_before = user_data.get('elapsed', 0)

    if start_time > 0:
        current_session_elapsed = current_time - start_time
        total_elapsed = elapsed_before + current_session_elapsed
        
        requests.patch(f"{FIREBASE_URL}/users/{chat_id}.json", json={
            'startTime': 0,
            'elapsed': total_elapsed
        })
        
        remaining_ms = duration - total_elapsed
        if remaining_ms < 0:
            remaining_ms = 0
            
        rem_mins = int(remaining_ms / (1000 * 60))
        rem_secs = int((remaining_ms % (1000 * 60)) / 1000)
        
        bot.send_message(
            message.chat.id, 
            f"⏸️ **အချိန်ခေတ္တရပ်လိုက်ပါပြီ။**\n⏳ ကျန်ရှိသောအချိန်: {rem_mins} မိနစ် {rem_secs} စက္ကန့်\n\nပြန်သုံးလိုပါက '▶️ Start' ကို နှိပ်ပါ။", 
            parse_mode="Markdown"
        )
    else:
        bot.send_message(message.chat.id, "ℹ️ အချိန်ရေတွက်ခြင်း မရှိသေးပါ။")

@bot.message_handler(func=lambda message: message.text in ["⏳ ကျန်ရှိချိန် စစ်ဆေးရန်"])
def check_time_command(message):
    chat_id = str(message.chat.id)
    current_time = int(time.time() * 1000)
    
    try:
        response = requests.get(f"{FIREBASE_URL}/users/{chat_id}.json")
        user_data = response.json()
    except:
        user_data = None

    if not user_data:
        bot.send_message(message.chat.id, "❌ အချက်အလက် မရှိပါ။")
        return

    status = user_data.get('status', False)
    if not status:
        bot.send_message(message.chat.id, "❌ အချိန်ကုန်သွားပါပြီ။")
        return

    start_time = user_data.get('startTime', 0)
    duration = user_data.get('duration', 600000)
    elapsed_before = user_data.get('elapsed', 0)

    if start_time > 0:
        current_session_elapsed = current_time - start_time
        total_elapsed = elapsed_before + current_session_elapsed
    else:
        total_elapsed = elapsed_before

    remaining_ms = duration - total_elapsed

    if remaining_ms <= 0:
        requests.patch(f"{FIREBASE_URL}/users/{chat_id}.json", json={
            'status': False,
            'startTime': 0,
            'elapsed': duration
        })
        bot.send_message(message.chat.id, "⏰ အချိန်ကုန်ဆုံးသွားပါပြီ။")
        return

    rem_mins = int(remaining_ms / (1000 * 60))
    rem_secs = int((remaining_ms % (1000 * 60)) / 1000)
    bot.send_message(message.chat.id, f"⏳ **ကျန်ရှိချိန်:** {rem_mins} မိနစ် {rem_secs} စက္ကန့်", parse_mode="Markdown")

# --- ဖော်မြူလာ ၁ (Formula 1 Python Logic) ---
def run_formula_1(api_list):
    states = ['BIG' if int(item.get('number', 0)) >= 5 else 'SMALL' for item in api_list[:700]]
    if not states or len(states) < 5:
        return {"formulaName": "Formula 1 (AI Sniper)", "prediction": "BIG 🟢", "confidence": 65}

    big_score = 50
    small_score = 50

    recent_numbers = [int(i.get('number', 0)) for i in api_list[:10] if str(i.get('number', '')).isdigit()]
    if len(recent_numbers) >= 5:
        w_sum = sum([num * (10 - idx) for idx, num in enumerate(recent_numbers)])
        w_avg = w_sum / len(recent_numbers)
        if w_avg < 4.5:
            big_score += 35
        else:
            small_score += 35

    p1, p2, p3 = states[0], states[1], states[2]
    if p1 == p2 and p2 == p3:
        if p1 == 'BIG':
            small_score += 30
        else:
            big_score += 30
    else:
        if p1 == 'BIG':
            big_score += 25
        else:
            small_score += 25

    score_diff = abs(big_score - small_score)
    is_big = big_score >= small_score
    confidence = 65 + int(score_diff * 0.5)
    if confidence > 98:
        confidence = 98

    return {
        "formulaName": "Formula 1 (AI Sniper)",
        "prediction": "BIG 🟢" if is_big else "SMALL 🔴",
        "confidence": confidence
    }

# --- ဖော်မြူလာ ၂ (Formula 2 Python Logic) ---
def run_formula_2(api_list):
    if not api_list or len(api_list) < 5:
        return {"formulaName": "Formula 2 (Advanced Engine)", "prediction": "SMALL 🔴", "confidence": 68}

    big_score = 50
    small_score = 50

    recent_numbers = [int(i.get('number', 0)) for i in api_list[:5] if str(i.get('number', '')).isdigit()]
    total_sum = sum(recent_numbers)
    last_num = recent_numbers[0] if recent_numbers else 0

    if total_sum % 2 == 0:
        big_score += 45
    else:
        small_score += 45

    if last_num >= 5:
        big_score += 20
    else:
        small_score += 20

    score_diff = abs(big_score - small_score)
    is_big = big_score >= small_score
    confidence = 70 + int(score_diff * 0.4)
    if confidence > 99:
        confidence = 99

    return {
        "formulaName": "Formula 2 (Advanced Engine)",
        "prediction": "BIG 🟢" if is_big else "SMALL 🔴",
        "confidence": confidence
    }

# 🎲 Formula 1 & Formula 2 Execution Handler (TRX_API_CONFIG ပုံစံအတိုင်း အတိအကျချိတ်ဆက်ခြင်း)
@bot.message_handler(func=lambda message: message.text in ["🎲 Big / Small (Formula 1)", "🔥 Big / Small (Formula 2)"])
def handle_formulas(message):
    is_formula_2 = "Formula 2" in message.text
    
    prev_issue = "-"
    prev_result = "-"
    win_loss = "-"
    formula_name = "Formula 2 (Advanced Engine)" if is_formula_2 else "Formula 1 (AI Sniper)"
    prediction = "BIG 🟢"
    confidence = 94

    try:
        TRX_API_CONFIG = {
            "url": "https://draw.ar-lottery01.com/TrxWinGo/TrxWinGo_1M/GetHistoryIssuePage.json",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10) Chrome/139.0.0.0 Mobile Safari/537.36',
                'Referer': 'https://hgnice.biz'
            }
        }
        
        ts_url = f"{TRX_API_CONFIG['url']}?ts={int(time.time() * 1000)}"
        res = requests.get(ts_url, headers=TRX_API_CONFIG['headers'], timeout=5)
        
        if res.status_code == 200 and res.headers.get('content-type', '').startswith('application/json'):
            data = res.json()
            lst = data.get('data', {}).get('list', [])
            
            if lst and len(lst) >= 2:
                latest_item = lst[0]
                prev_item = lst[1]
                
                # JavaScript ပုံစံအတိုင်း တိကျမှန်ကန်သော ပွဲစဉ်နံပါတ် တွက်ချက်မှု
                latest_issue_str = str(latest_item.get('issueNumber', ''))
                if latest_issue_str.isdigit():
                    next_issue = str(int(latest_issue_str) + 1)
                else:
                    next_issue = str(int(time.time() / 60))

                prev_issue = str(prev_item.get('issueNumber', ''))
                prev_num = int(prev_item.get('number', 0))
                prev_result = "BIG 🟢" if prev_num >= 5 else "SMALL 🔴"
                
                if is_formula_2:
                    result = run_formula_2(lst)
                else:
                    result = run_formula_1(lst)
                    
                prediction = result['prediction']
                confidence = result['confidence']
                formula_name = result['formulaName']
                
                win_loss = "WIN ✅" if (prediction.startswith("BIG") and prev_num >= 5) or (prediction.startswith("SMALL") and prev_num < 5) else "LOSE ❌"
            else:
                next_issue = str(int(time.time() / 60))
        else:
            next_issue = str(int(time.time() / 60))
    except Exception as e:
        print(f"TRX API Fetch Error: {e}")
        next_issue = str(int(time.time() / 60))

    bot.send_message(
        message.chat.id,
        f"🎯 **FLASH TRX • SNIPER AI**\n"
        f"📌 ဖော်မြူလာ: *{formula_name}*\n"
        f"🔢 လက်ရှိ Period: `{next_issue}`\n"
        f"📊 ပြီးခဲ့သော Period ({prev_issue}): **{prev_result}**\n"
        f"🏆 ရလဒ်စစ်ဆေးချက်: **{win_loss}**\n"
        f"🔮 ခန့်မှန်းချက်: **{prediction} (Confidence: {confidence}%)**\n"
        f"🎯 ⚡ Sniper Shot Active!",
        parse_mode="Markdown"
    )

RENDER_URL = "https://flash-user-bot.onrender.com"
try:
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    print(f"Webhook set to: {RENDER_URL}/{TOKEN}")
except Exception as e:
    print(f"Webhook error: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
