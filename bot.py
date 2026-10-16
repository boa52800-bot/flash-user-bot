import os
import time
import requests
import random
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# User Bot Token
TOKEN = "8785462549:AAEDI_fiJJXAOaVFFWhGChGQT3VnmzskDWQ"
bot = telebot.TeleBot(TOKEN, threaded=False)

# Flask App (ဒီနေရာမှာ app ကို အသေအချာ ကြေညာထားပါတယ်)
app = Flask(__name__)

# Firebase Realtime Database URL
FIREBASE_URL = "https://flashlotter-default-rtdb.europe-west1.firebasedatabase.app"

# အသုံးပြုသူများ၏ လက်ရှိအခြေအနေကို မှတ်သားရန်
user_sessions = {}

# TRX WinGo API အတွက် Headers
API_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10) Chrome/139.0.0.0 Mobile Safari/537.36',
    'Referer': 'https://hgnice.biz'
}

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
    return "Flash User Bot Webhook is Active!"

# 1. /start နှိပ်သောအခါ Telegram Name တောင်းခြင်း
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "⚡ FLASH TRX BOT ⚡\n\nအသုံးပြုရန် ကျေးဇူးပြု၍ သင့် Telegram Name ကို ရိုက်ထည့်ပေးပါ (ဥပမာ - Kyaw Kyaw)")
    user_sessions[chat_id] = {"step": "awaiting_name"}

# 2. Telegram Name လက်ခံရယူပြီး Check ID ထုတ်ပေးခြင်း
@bot.message_handler(func=lambda message: message.chat.id in user_sessions and user_sessions[message.chat.id].get("step") == "awaiting_name")
def handle_name(message):
    chat_id = message.chat.id
    tg_name = message.text.strip()
    
    # Random Check ID ဖန်တီးခြင်း
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    check_id = 'FLASH-' + ''.join(random.choice(chars) for _ in range(5))
    
    # Firebase သို့ အချက်အလက် ပို့ခြင်း (Admin Bot မှ မြင်နိုင်ရန်)
    user_data = {
        'checkId': check_id,
        'tgName': tg_name,
        'status': False,
        'mode': 'none',
        'chatId': chat_id,
        'createdAt': int(time.time() * 1000)
    }
    
    try:
        requests.put(f"{FIREBASE_URL}/users/{check_id}.json", json=user_data)
    except Exception as e:
        print(f"Firebase Error: {e}")

    user_sessions[chat_id] = {"check_id": check_id, "tg_name": tg_name, "step": "waiting_approval"}
    
    text = f"✅ သင့်ရဲ့ Check ID: `{check_id}`\n\n" \
           f"အထက်ပါ Check ID ကို Admin Bot သို့ ပို့၍ အချိန်ခွင့်ပြုချက် ရယူပါ။\n" \
           f"ခွင့်ပြုချက်ရပြီဆိုရင် အောက်ပါ ခလုတ်ကို နှိပ်ပါ -"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔄 ခွင့်ပြုချက် စစ်ဆေးမည် (Check Approval)", callback_data="check_approval"))
    
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

# 3. ခွင့်ပြုချက် စစ်ဆေးခြင်းနှင့် ဖော်မြူလာ ရွေးချယ်ခိုင်းခြင်း
@bot.callback_query_handler(func=lambda call: call.data == "check_approval")
def verify_approval(call):
    chat_id = call.message.chat.id
    session = user_sessions.get(chat_id)
    
    if not session:
        bot.answer_callback_query(call.id, text="ကျေးဇူးပြု၍ /start ဖြင့် အစမှစပါ။")
        return
        
    check_id = session["check_id"]
    
    try:
        res = requests.get(f"{FIREBASE_URL}/users/{check_id}.json")
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

# 4. ဖော်မြူလာ ရွေးချယ်ပြီး ခန့်မှန်းချက်စတင်ခြင်း
@bot.callback_query_handler(func=lambda call: call.data in ["formula_1", "formula_2"])
def select_formula(call):
    chat_id = call.message.chat.id
    formula_num = 1 if call.data == "formula_1" else 2
    
    user_sessions[chat_id]["formula"] = formula_num
    user_sessions[chat_id]["step"] = "running"
    
    bot.edit_message_text(f"🚀 Formula {formula_num} ဖြင့် စတင်အလုပ်လုပ်နေပါပြီ။\nပွဲစဉ်အသစ်ထွက်လာသည်နှင့် Telegram မှတဆင့် Noti ပို့ပေးပါမည်။", 
                          chat_id=chat_id, message_id=call.message.message_id)
    
    # နောက်ခံတွင် ပွဲစဉ်များကို စောင့်ကြည့်ပြီး Noti ပို့မည့် Thread ကို စတင်ခြင်း
    import threading
    threading.Thread(target=run_prediction_loop, args=(chat_id, formula_num)).start()

# 5. API မှ ဒေတာဆွဲထုတ်ပြီး တစ်ပွဲပြီးတစ်ပွဲ Noti ပို့ပေးမည့် Function
def run_prediction_loop(chat_id, formula_num):
    last_processed_issue = None
    last_prediction = None
    
    while chat_id in user_sessions and user_sessions[chat_id].get("step") == "running":
        try:
            res = requests.get(f"https://draw.ar-lottery01.com/TrxWinGo/TrxWinGo_1M/GetHistoryIssuePage.json?ts={int(time.time()*1000)}", headers=API_HEADERS)
            data = res.json()
            list_data = data.get('data', {}).get('list', [])
            
            if len(list_data) > 0:
                current_issue = list_data[0]['issueNumber']
                actual_num = int(list_data[0]['number'])
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
                    predicted_state = "BIG" if actual_num >= 4 else "SMALL"
                    last_prediction = predicted_state
                    
                    next_text = f"⚡ FLASH TRX • SNIPER AI\n\n" \
                                f"📌 ပွဲစဉ်အသစ်: {next_issue}\n" \
                                f"🔮 ခန့်မှန်းချက်: {predicted_state}\n" \
                                f"⚡ အသုံးပြုနေသည့် ဖော်မြူလာ: Formula {formula_num}"
                    bot.send_message(chat_id, next_text)
                    
        except Exception as e:
            print(f"Loop Error: {e}")
            
        time.sleep(15)

if __name__ == "__main__":
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
        print(f"Webhook set to: {RENDER_URL}/{TOKEN}")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
