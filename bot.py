import os
import time
import requests
import random
import threading
from flask import Flask
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# User Bot Token အသစ်
TOKEN = "8744519803:AAFOY-LKB7cj2zXk1oLg0K3EXiH3P8i6txU"
bot = telebot.TeleBot(TOKEN, threaded=True)

app = Flask(__name__)
FIREBASE_URL = "https://flash-1d21e-default-rtdb.europe-west1.firebasedatabase.app"

user_sessions = {}

API_HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'my-MM,my;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Referer': 'https://hgnice.biz/',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36'
}

def get_control_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, persistent=True)
    markup.row(
        KeyboardButton("⏳ ကျန်ရှိချိန် စစ်ဆေးရန်"),
        KeyboardButton("🛑 ရပ်ရန် (Stop)")
    )
    return markup

@app.route('/')
def home():
    return "Flash User Bot is Running!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    
    if chat_id in user_sessions:
        user_sessions[chat_id]["step"] = "stopped"
        time.sleep(1)

    user_sessions[chat_id] = {"step": "formula_select"}
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Formula 1 (AI Sniper)", callback_data="formula_1"))
    markup.add(InlineKeyboardButton("Formula 2 (Advanced Engine)", callback_data="formula_2"))
    
    bot.send_message(chat_id, "⚡ FLASH TRX BOT ⚡\n\nအသုံးပြုလိုသော ဖော်မြူလာကို ရွေးချယ်ပါ -", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["formula_1", "formula_2"])
def select_formula(call):
    chat_id = call.message.chat.id
    
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}

    formula_num = 1 if call.data == "formula_1" else 2
    session_token = str(time.time())
    
    user_sessions[chat_id]["session_token"] = session_token
    user_sessions[chat_id]["formula"] = formula_num
    user_sessions[chat_id]["step"] = "running"
    
    bot.edit_message_text(f"🚀 Formula {formula_num} ဖြင့် စတင်အလုပ်လုပ်နေပါပြီ။", 
                          chat_id=chat_id, message_id=call.message.message_id)
    
    bot.send_message(chat_id, f"👇 အောက်ပါ မီနူးခလုတ်များကို အသုံးပြုနိုင်ပါပြီ -", reply_markup=get_control_keyboard())

    threading.Thread(target=run_prediction_loop, args=(chat_id, formula_num, session_token)).start()

@bot.message_handler(func=lambda message: message.text in ["⏳ ကျန်ရှိချိန် စစ်ဆေးရန်", "🛑 ရပ်ရန် (Stop)"])
def handle_reply_buttons(message):
    chat_id = message.chat.id
    session = user_sessions.get(chat_id)
    
    if message.text == "🛑 ရပ်ရန် (Stop)":
        if session:
            session["step"] = "stopped"
        bot.send_message(chat_id, "🛑 **ခန့်မှန်းမှုများ ရပ်တန့်သွားပါပြီ။**\n\nပြန်လည်စတင်ရန် /start ကိုနှိပ်ပါ။", parse_mode="Markdown", reply_markup=telebot.types.ReplyKeyboardRemove())
        
    elif message.text == "⏳ ကျန်ရှိချိန် စစ်ဆေးရန်":
        bot.send_message(chat_id, "⏳ ဘော့သည် အဆက်မပြတ် ပုံမှန် အလုပ်လုပ်နေပါသည်။")

def run_prediction_loop(chat_id, formula_num, session_token):
    api_url = "https://draw.ar-lottery01.com/TrxWinGo/TrxWinGo_1M/GetHistoryIssuePage.json"
    
    last_processed_issue = None
    last_prediction = "BIG"

    def fetch_latest_data():
        try:
            payload = {"pageSize": 10, "pageNo": 1}
            res = requests.post(api_url, json=payload, headers=API_HEADERS, timeout=10)
            if res.status_code == 200:
                data = res.json()
                list_data = data.get('data', {}).get('list', [])
                if list_data:
                    return list_data[0]
        except Exception as e:
            print(f"API Fetch Error: {e}")
        return None

    first_item = fetch_latest_data()
    if first_item:
        current_issue = str(first_item.get('issueNumber'))
        next_issue = str(int(current_issue) + 1)
        actual_num = int(first_item.get('number', 0))
        
        if formula_num == 1:
            predicted_state = "BIG" if actual_num >= 5 else "SMALL"
        else:
            predicted_state = "SMALL" if actual_num >= 5 else "BIG"
            
        last_processed_issue = current_issue
        last_prediction = predicted_state
        
        init_text = f"⚡ FLASH TRX • SNIPER AI\n\n" \
                    f"📌 ပွဲစဉ်အသစ်: {next_issue}\n" \
                    f"🔮 ခန့်မှန်းချက်: {predicted_state}\n" \
                    f"⚡ အသုံးပြုနေသည့် ဖော်မြူလာ: Formula {formula_num}"
        bot.send_message(chat_id, init_text, reply_markup=get_control_keyboard())
    else:
        t = time.gmtime()
        date_str = time.strftime("%Y%m%d", t)
        total_mins = t.tm_hour * 60 + t.tm_min
        next_issue = f"{date_str}{10300000 + total_mins + 1}"
        
        init_text = f"⚡ FLASH TRX • SNIPER AI\n\n" \
                    f"📌 ပွဲစဉ်အသစ်: {next_issue}\n" \
                    f"🔮 ခန့်မှန်းချက်: BIG\n" \
                    f"⚡ အသုံးပြုနေသည့် ဖော်မြူလာ: Formula {formula_num}"
        bot.send_message(chat_id, init_text, reply_markup=get_control_keyboard())
        last_processed_issue = str(int(next_issue) - 1)
        last_prediction = "BIG"

    while chat_id in user_sessions and user_sessions[chat_id].get("step") == "running" and user_sessions[chat_id].get("session_token") == session_token:
        try:
            time.sleep(10)
            latest_item = fetch_latest_data()
            
            if latest_item:
                current_issue = str(latest_item.get('issueNumber'))
                actual_num = int(latest_item.get('number', 0))
                actual_state = "BIG" if actual_num >= 5 else "SMALL"
                
                if current_issue != last_processed_issue:
                    if last_prediction and last_processed_issue:
                        is_win = (last_prediction == actual_state)
                        result_text = f"🎯 ပွဲစဉ်: {last_processed_issue}\n" \
                                      f"🔮 ခန့်မှန်းချက်: {last_prediction}\n" \
                                      f"🎲 ထွက်လာသည့်ဂဏန်း: {actual_num} ({actual_state})\n" \
                                      f"ယခုပွဲရလဒ်: {'🟢 အနိုင် (WIN)' if is_win else '🔴 အရှုံး (LOSS)'}"
                        bot.send_message(chat_id, result_text, reply_markup=get_control_keyboard())
                    
                    last_processed_issue = current_issue
                    next_issue = str(int(current_issue) + 1)
                    
                    if formula_num == 1:
                        predicted_state = "BIG" if actual_num >= 5 else "SMALL"
                    else:
                        predicted_state = "SMALL" if actual_num >= 5 else "BIG"
                        
                    last_prediction = predicted_state
                    
                    next_text = f"⚡ FLASH TRX • SNIPER AI\n\n" \
                                f"📌 ပွဲစဉ်အသစ်: {next_issue}\n" \
                                f"🔮 ခန့်မှန်းချက်: {predicted_state}\n" \
                                f"⚡ အသုံးပြုနေသည့် ဖော်မြူလာ: Formula {formula_num}"
                    
                    bot.send_message(chat_id, next_text, reply_markup=get_control_keyboard())
        except Exception as e:
            print(f"Loop Error: {e}")

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    bot.remove_webhook()
    time.sleep(1)
    
    print("Bot is running with Infinity Polling...")
    bot.infinity_polling(skip_pending=True)
