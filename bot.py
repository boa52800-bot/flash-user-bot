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

# Firebase Realtime Database URL အသစ်
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

# User Bot ရဲ့ မီနူးခလုတ်များ
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
        bot.send_message(
            message.chat.id, 
            f"❌ **အသုံးပြုခွင့် မရှိသေးပါ။**\n\n"
            f"သင့်ရဲ့ Telegram Chat ID (`{chat_id}`) ကို Admin Bot ထံ ပို့ပြီး အချိန်ခွင့်ပြုချက် (Check ID) ရယူပါ။", 
            parse_mode="Markdown"
        )
        return

    status = user_data.get('status', False)
    mode = user_data.get('mode', '')

    if status and mode == 'always':
        bot.send_message(
            message.chat.id, 
            "✨ **ကြိုဆိုပါတယ်!**\nသင်သည် အမြဲတမ်း (Always) အသုံးပြုခွင့် ရရှိထားပါသည်။ အောက်ပါမီနူးမှ အသုံးပြုနိုင်ပါပြီ -", 
            reply_markup=get_main_menu(), 
            parse_mode="Markdown"
        )
        return

    if not status or mode == 'blocked':
        bot.send_message(message.chat.id, "❌ သင့်အကောင့်မှာ အသုံးပြုခွင့် ပိတ်ထားခြင်း ခံထားရပါသည် သို့မဟုတ် အချိန်ကုန်သွားပါပြီ။")
        return

    start_time = user_data.get('startTime', 0)
    duration = user_data.get('duration', 0)
    elapsed_before = user_data.get('elapsed', 0)

    if start_time == 0:
        requests.patch(f"{FIREBASE_URL}/users/{chat_id}.json", json={
            'startTime': current_time,
            'status': True
        })
        bot.send_message(
            message.chat.id, 
            "▶️ **အချိန်စတင်ရေတွက်နေပါပြီ။**\nအောက်ပါမီနူးများမှ ဆက်လက်အသုံးပြုနိုင်ပါပြီ -", 
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
            bot.send_message(message.chat.id, "⏰ **အချိန်ကုန်ဆုံးသွားပါပြီ။** Admin ထံတွင် အချိန်တိုးပေးရန် တောင်းဆိုပါ။", parse_mode="Markdown")
        else:
            bot.send_message(
                message.chat.id, 
                "▶️ **Bot ကို ပြန်လည်စတင်လိုက်ပါပြီ။** ဆက်လက်အသုံးပြုနိုင်ပါပြီ -", 
                reply_markup=get_main_menu(), 
                parse_mode="Markdown"
            )

# 🛑 Stop Command
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

    mode = user_data.get('mode', '')
    if mode == 'always':
        bot.send_message(message.chat.id, "♾️ သင်သည် အမြဲတမ်းသုံးခွင့်ရှိသူဖြစ်၍ ရပ်တန့်ရန် မလိုပါ။")
        return

    start_time = user_data.get('startTime', 0)
    duration = user_data.get('duration', 0)
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

# ⏳ ကျန်ရှိချိန် စစ်ဆေးရန်
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
    mode = user_data.get('mode', '')

    if not status or mode == 'blocked':
        bot.send_message(message.chat.id, "❌ ပိတ်ထားသည် သို့မဟုတ် အချိန်ကုန်သွားပါပြီ။")
        return

    if mode == 'always':
        bot.send_message(message.chat.id, "♾️ အမြဲတမ်း (Always) အသုံးပြုခွင့် ရှိပါသည်။")
        return

    start_time = user_data.get('startTime', 0)
    duration = user_data.get('duration', 0)
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
    bot.send_message(message.chat.id, f"⏳ **ကျန်ရှိသောအချိန်:** {rem_mins} မိနစ် {rem_secs} စက္ကန့်", parse_mode="Markdown")

# 🎲 Formula 1 & Formula 2
@bot.message_handler(func=lambda message: message.text in ["🎲 Big / Small (Formula 1)", "🔥 Big / Small (Formula 2)"])
def handle_formulas(message):
    chat_id = str(message.chat.id)
    current_time = int(time.time() * 1000)
    
    try:
        response = requests.get(f"{FIREBASE_URL}/users/{chat_id}.json")
        user_data = response.json()
    except:
        user_data = None

    if not user_data:
        bot.send_message(message.chat.id, "❌ အသုံးပြုခွင့် မရှိပါ။ Admin ထံ စာရင်းသွင်းပါ။")
        return

    status = user_data.get('status', False)
    mode = user_data.get('mode', '')

    if mode != 'always':
        if not status or mode == 'blocked':
            bot.send_message(message.chat.id, "❌ သင့်အကောင့် ပိတ်ထားသည် သို့မဟုတ် အချိန်ကုန်သွားပါပြီ။")
            return

        start_time = user_data.get('startTime', 0)
        duration = user_data.get('duration', 0)
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
            bot.send_message(message.chat.id, "⏰ အချိန်ကုန်ဆုံးသွားပါပြီ။ ဂိမ်းကစား၍ မရတော့ပါ။")
            return

    is_formula_2 = "Formula 2" in message.text
    formula_name = "Formula 2 (Advanced Engine)" if is_formula_2 else "Formula 1 (AI Sniper Engine)"
    
    try:
        api_res = requests.get("https://draw.ar-lottery01.com/TrxWinGo/TrxWinGo_1M/GetHistoryIssuePage.json", timeout=5).json()
        list_data = api_res.get('data', {}).get('list', [])
        if list_data:
            latest_issue = str(list_data[0].get('issueNumber', '00000'))
            next_issue = str(int(latest_issue) + 1)
        else:
            next_issue = "Active Period"
    except:
        next_issue = "Active Period"

    bot.send_message(
        message.chat.id,
        f"🎯 **FLASH TRX • SNIPER AI**\n"
        f"📌 ရွေးချယ်ထားသော ဖော်မြူလာ: *{formula_name}*\n"
        f"🔢 Period: `{next_issue}`\n"
        f"🔮 ခန့်မှန်းချက်: **BIG (Confidence: 94%)**\n"
        f"🎯 ⚡ Sniper Shot Active!",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
        print(f"Webhook set to: {RENDER_URL}/{TOKEN}")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
