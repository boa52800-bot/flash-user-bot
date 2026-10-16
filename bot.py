import os
import time
import requests
import random
import threading
from flask import Flask
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# User Bot Token
TOKEN = "8785462549:AAEDI_fiJJXAOaVFFWhGChGQT3VnmzskDWQ"
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

# အမြဲပေါ်နေမည့် Reply Keyboard (Control Menu)
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

    try:
        res = requests.get(f"{FIREBASE_URL}/users.json", timeout=5)
        users = res.json()
        existing_check_id = None
        if users:
            for cid, data in users.items():
                if isinstance(data, dict) and data.get('chatId') == chat_id:
                    existing_check_id = cid
                    break
        
        if existing_check_id:
            user_sessions[chat_id] = {"check_id": existing_check_id, "step": "waiting_approval"}
            text = f"✅ သင့်ရဲ့ Check ID (ရှိပြီးသား): `{existing_check_id}`\n\n" \
                   f"အထက်ပါ Check ID ကို Admin Bot သို့ ပို့၍ အချိန်ခွင့်ပြုချက် ရယူပါ။"
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔄 ခွင့်ပြုချက် စစ်ဆေးမည် (Check Approval)", callback_data="check_approval"))
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
            return
    except Exception as e:
        print(e)

    bot.send_message(chat_id, "⚡ FLASH TRX BOT ⚡\n\nအသုံးပြုရန် ကျေးဇူးပြု၍ သင့် Telegram Name ကို ရိုက်ထည့်ပေးပါ (ဥပမာ - Kyaw Kyaw)")
    user_sessions[chat_id] = {"step": "awaiting_name"}

@bot.message_handler(func=lambda message: message.chat.id in user_sessions and user_sessions[message.chat.id].get("step") == "awaiting_name")
def handle_name(message):
    chat_id = message.chat.id
    tg_name = message.text.strip()
    
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    check_id = 'FLASH-' + ''.join(random.choice(chars) for _ in range(5))
    
    user_data = {
        'checkId': check_id,
        'tgName': tg_name,
        'status': False,
        'mode': 'none',
        'chatId': chat_id,
        'createdAt': int(time.time() * 1000)
    }
    
    try:
        requests.put(f"{FIREBASE_URL}/users/{check_id}.json", json=user_data, timeout=5)
    except Exception as e:
        print(f"Firebase Error: {e}")

    user_sessions[chat_id] = {"check_id": check_id, "tg_name": tg_name, "step": "waiting_approval"}
    
    text = f"✅ သင့်ရဲ့ Check ID: `{check_id}`\n\n" \
           f"အထက်ပါ Check ID ကို Admin Bot သို့ ပို့၍ အချိန်ခွင့်ပြုချက် ရယူပါ။\n" \
           f"ခွင့်ပြုချက်ရပြီဆိုရင် အောက်ပါ ခလုတ်ကို နှိပ်ပါ -"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔄 ခွင့်ပြုချက် စစ်ဆေးမည် (Check Approval)", callback_data="check_approval"))
    
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "check_approval")
def verify_approval(call):
    chat_id = call.message.chat.id
    session = user_sessions.get(chat_id)
    
    if not session:
        bot.answer_callback_query(call.id, text="ကျေးဇူးပြု၍ /start ဖြင့် အစမှစပါ။")
        return
        
    check_id = session["check_id"]
    
    try:
        res = requests.get(f"{FIREBASE_URL}/users/{check_id}.json", timeout=5)
        data = res.json()
    except:
        data = None
        
    if data and data.get('status') == True:
        user_sessions[chat_id]["step"] = "formula_select"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Formula 1 (AI Sniper)", callback_data="formula_1"))
        markup.add(InlineKeyboardButton("Formula 2 (Advanced Engine)", callback_data="formula_2"))
        
        bot.edit_message_text("🎉 Admin မှ ခွင့်ပြုချက်ပေးပြီးပါပြီ။\n\nအသုံးပြုလိုသော ဖော်မြူလာကို ရွေးချယ်ပါ -", 
                              chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)
    else:
        bot.answer_callback_query(call.id, text="❌ Admin မှ ခွင့်ပြုချက် မပေးသေးပါ သို့မဟုတ် စောင့်ဆိုင်းနေဆဲပါ။")

@bot.callback_query_handler(func=lambda call: call.data in ["formula_1", "formula_2"])
def select_formula(call):
    chat_id = call.message.chat.id
    
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}
        
    check_id = user_sessions[chat_id].get("check_id")
    try:
        res = requests.get(f"{FIREBASE_URL}/users/{check_id}.json", timeout=5)
        data = res.json()
        if not data or data.get('status') != True:
            bot.answer_callback_query(call.id, text="❌ ခွင့်ပြုချက် မရှိတော့ပါ သို့မဟုတ် ပိတ်ထားသည်။", show_alert=True)
            return
    except:
        pass

    formula_num = 1 if call.data == "formula_1" else 2
    session_token = str(time.time())
    
    user_sessions[chat_id]["session_token"] = session_token
    user_sessions[chat_id]["formula"] = formula_num
    user_sessions[chat_id]["step"] = "running"
    
    bot.edit_message_text(f"🚀 Formula {formula_num} ဖြင့် စတင်အလုပ်လုပ်နေပါပြီ။", 
                          chat_id=chat_id, message_id=call.message.message_id)
    
    # ခလုတ်အသစ် (Reply Keyboard) ပေါ်လာစေရန် စာတစ်စောင်ပို့မည်
    bot.send_message(chat_id, f"👇 အောက်ပါခလုတ်များကို အသုံးပြုနိုင်ပါပြီ -", reply_markup=get_control_keyboard())

    threading.Thread(target=run_prediction_loop, args=(chat_id, formula_num, session_token)).start()

# အောက်ခြေခလုတ်များ (Reply Keyboard) ကို လက်ခံဆောင်ရွက်ပေးခြင်း
@bot.message_handler(func=lambda message: message.text in ["⏳ ကျန်ရှိချိန် စစ်ဆေးရန်", "🛑 ရပ်ရန် (Stop)"])
def handle_reply_buttons(message):
    chat_id = message.chat.id
    session = user_sessions.get(chat_id)
    
    if message.text == "🛑 ရပ်ရန် (Stop)":
        if session:
            session["step"] = "stopped"
        bot.send_message(chat_id, "🛑 **ခန့်မှန်းမှုများ ရပ်တန့်သွားပါပြီ။**\n\nပြန်လည်စတင်ရန် /start ကိုနှိပ်ပါ။", parse_mode="Markdown")
        
    elif message.text == "⏳ ကျန်ရှိချိန် စစ်ဆေးရန်":
        if not session:
            bot.send_message(chat_id, "အချက်အလက် မရှိပါ။ ကျေးဇူးပြု၍ /start ဖြင့် အစမှစပါ။")
            return
            
        check_id = session.get("check_id")
        try:
            res = requests.get(f"{FIREBASE_URL}/users/{check_id}.json", timeout=5)
            data = res.json()
            if not data or data.get('status') != True:
                bot.send_message(chat_id, "❌ Admin မှ အချိန်ပိတ်ထားပါပြီ သို့မဟုတ် ခွင့်ပြုချက်မရှိပါ။")
                return
                
            created_at = data.get('createdAt', int(time.time() * 1000))
            expire_time = created_at + (24 * 60 * 60 * 1000)
            remaining_ms = expire_time - int(time.time() * 1000)
            
            if remaining_ms <= 0:
                bot.send_message(chat_id, "⏰ Admin ခွင့်ပြုထားသော အချိန်ကုန်ဆုံးသွားပါပြီ။")
            else:
                rem_hours = remaining_ms // (1000 * 60 * 60)
                rem_mins = (remaining_ms // (1000 * 60)) % 60
                bot.send_message(chat_id, f"⏳ ကျန်ရှိသော အချိန်: {rem_hours} နာရီ {rem_mins} မိနစ်")
        except Exception as e:
            bot.send_message(chat_id, "အချိန်စစ်ဆေး၍ မရပါ။")

def run_prediction_loop(chat_id, formula_num, session_token):
    api_url = "https://draw.ar-lottery01.com/TrxWinGo/TrxWinGo_1M/GetHistoryIssuePage.json"
    
    last_processed_issue = None
    last_prediction = "BIG"
    check_id = user_sessions.get(chat_id, {}).get("check_id")

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
        bot.send_message(chat_id, init_text)
    else:
        t = time.gmtime()
        date_str = time.strftime("%Y%m%d", t)
        total_mins = t.tm_hour * 60 + t.tm_min
        next_issue = f"{date_str}{10300000 + total_mins + 1}"
        
        init_text = f"⚡ FLASH TRX • SNIPER AI\n\n" \
                    f"📌 ပွဲစဉ်အသစ်: {next_issue}\n" \
                    f"🔮 ခန့်မှန်းချက်: BIG\n" \
                    f"⚡ အသုံးပြုနေသည့် ဖော်မြူလာ: Formula {formula_num}"
        bot.send_message(chat_id, init_text)
        last_processed_issue = str(int(next_issue) - 1)
        last_prediction = "BIG"

    while chat_id in user_sessions and user_sessions[chat_id].get("step") == "running" and user_sessions[chat_id].get("session_token") == session_token:
        try:
            if check_id:
                res = requests.get(f"{FIREBASE_URL}/users/{check_id}.json", timeout=5)
                data = res.json()
                if not data or data.get('status') != True:
                    user_sessions[chat_id]["step"] = "stopped"
                    bot.send_message(chat_id, "⚠️ **Admin မှ ခွင့်ပြုချက်ပိတ်လိုက်ပါပြီ (သို့မဟုတ်) အချိန်ကုန်ဆုံးသွားပါပြီ။**\n\nဘော့အလုပ်လုပ်ခြင်းကို ရပ်တန့်လိုက်ပါပြီ။", parse_mode="Markdown")
                    break

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
                        bot.send_message(chat_id, result_text)
                    
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
                    
                    bot.send_message(chat_id, next_text)
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
    print("Bot is running with Infinity Polling...")
    bot.infinity_polling(skip_pending=True)
