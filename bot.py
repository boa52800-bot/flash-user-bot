import os
import time
import requests
import random
import threading
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# User Bot Token
TOKEN = "8785462549:AAEDI_fiJJXAOaVFFWhGChGQT3VnmzskDWQ"
bot = telebot.TeleBot(TOKEN, threaded=False)

# Flask App
app = Flask(__name__)

# Admin Bot တွင် အသုံးပြုခဲ့သော တိကျမှန်ကန်သည့် Database URL
FIREBASE_URL = "https://flash-1d21e-default-rtdb.europe-west1.firebasedatabase.app"

# အသုံးပြုသူများ၏ လက်ရှိအခြေအနေကို မှတ်သားရန်
user_sessions = {}

# API Headers အသစ်များ (Block မခံရအောင် ပိုမိုကောင်းမွန်အောင် ပြင်ဆင်ထားသည်)
API_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://hgnice.biz/'
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

# 1. /start နှိပ်သောအခါ
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    
    try:
        res = requests.get(f"{FIREBASE_URL}/users.json")
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

# 2. Telegram Name လက်ခံရယူပြီး Check ID ထုတ်ပေးခြင်း
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

# 3. ခွင့်ပြုချက် စစ်ဆေးခြင်း
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

# 4. ဖော်မြူလာ ရွေးချယ်ခြင်း
@bot.callback_query_handler(func=lambda call: call.data in ["formula_1", "formula_2"])
def select_formula(call):
    chat_id = call.message.chat.id
    formula_num = 1 if call.data == "formula_1" else 2
    
    user_sessions[chat_id]["formula"] = formula_num
    user_sessions[chat_id]["step"] = "running"
    
    bot.edit_message_text(f"🚀 Formula {formula_num} ဖြင့် စတင်အလုပ်လုပ်နေပါပြီ။", 
                          chat_id=chat_id, message_id=call.message.message_id)
    
    threading.Thread(target=run_prediction_loop, args=(chat_id, formula_num)).start()

# 5. API ချိတ်ဆက်မှုကို ဆွဲထုတ်မည့် Loop (Alternative API Endpoints များပါ ထည့်သွင်းထားသည်)
def run_prediction_loop(chat_id, formula_num):
    last_processed_issue = None
    last_prediction = None
    
    # API URLs အလှည့်ကျ သုံးရန်
    api_urls = [
        "https://draw.ar-lottery01.com/TrxWinGo/TrxWinGo_1M/GetHistoryIssuePage.json",
        "https://api.hgnice.biz/api/webapi/GetNoaverageEmerdList"
    ]
    
    success = False
    for api_url in api_urls:
        for _ in range(2):
            try:
                res = requests.get(f"{api_url}?ts={int(time.time()*1000)}", headers=API_HEADERS, timeout=8)
                data = res.json()
                
                # Response ပုံစံအမျိုးမျိုးအတွက် အံဝင်ခွင်ကျဖြစ်စေရန်
                list_data = []
                if 'data' in data and isinstance(data['data'], dict):
                    list_data = data['data'].get('list', [])
                elif 'data' in data and isinstance(data['data'], list):
                    list_data = data['data']
                
                if len(list_data) > 0:
                    current_issue = str(list_data[0].get('issueNumber') or list_data[0].get('issue') or list_data[0].get('period'))
                    actual_num = int(list_data[0].get('number') or list_data[0].get('winningNumber') or 0)
                    
                    last_processed_issue = current_issue
                    next_issue = str(int(current_issue) + 1)
                    
                    predicted_state = "BIG" if actual_num >= 5 else "SMALL"
                    last_prediction = predicted_state
                    
                    init_text = f"⚡ FLASH TRX • SNIPER AI\n\n" \
                                f"📌 ပွဲစဉ်အသစ်: {next_issue}\n" \
                                f"🔮 ခန့်မှန်းချက်: {predicted_state}\n" \
                                f"⚡ အသုံးပြုနေသည့် ဖော်မြူလာ: Formula {formula_num}"
                    bot.send_message(chat_id, init_text)
                    success = True
                    break
            except Exception as e:
                print(f"API Error: {e}")
                time.sleep(1)
        if success:
            break
            
    if not success:
        bot.send_message(chat_id, "⚠️ API ချိတ်ဆက်ရာတွင် အခက်အခဲရှိနေပါသည်။ ဆက်လက်ကြိုးစားနေပါမည်။")

    while chat_id in user_sessions and user_sessions[chat_id].get("step") == "running":
        try:
            time.sleep(12)
            current_issue = None
            actual_num = 0
            
            for api_url in api_urls:
                try:
                    res = requests.get(f"{api_url}?ts={int(time.time()*1000)}", headers=API_HEADERS, timeout=8)
                    data = res.json()
                    list_data = []
                    if 'data' in data and isinstance(data['data'], dict):
                        list_data = data['data'].get('list', [])
                    elif 'data' in data and isinstance(data['data'], list):
                        list_data = data['data']
                        
                    if len(list_data) > 0:
                        current_issue = str(list_data[0].get('issueNumber') or list_data[0].get('issue') or list_data[0].get('period'))
                        actual_num = int(list_data[0].get('number') or list_data[0].get('winningNumber') or 0)
                        break
                except:
                    continue
            
            if current_issue and current_issue != last_processed_issue:
                actual_state = "BIG" if actual_num >= 5 else "SMALL"
                
                if last_prediction and last_processed_issue:
                    is_win = (last_prediction == actual_state)
                    result_text = f"🎯 ပွဲစဉ်: {last_processed_issue}\n" \
                                  f"🔮 ခန့်မှန်းချက်: {last_prediction}\n" \
                                  f"🎲 ထွက်လာသည့်ဂဏန်း: {actual_num} ({actual_state})\n" \
                                  f"ယခုပွဲရလဒ်: {'🟢 အနိုင် (WIN)' if is_win else '🔴 အရှုံး (LOSS)'}"
                    bot.send_message(chat_id, result_text)
                
                last_processed_issue = current_issue
                next_issue = str(int(current_issue) + 1)
                predicted_state = "BIG" if actual_num >= 5 else "SMALL"
                last_prediction = predicted_state
                
                next_text = f"⚡ FLASH TRX • SNIPER AI\n\n" \
                            f"📌 ပွဲစဉ်အသစ်: {next_issue}\n" \
                            f"🔮 ခန့်မှန်းချက်: {predicted_state}\n" \
                            f"⚡ အသုံးပြုနေသည့် ဖော်မြူလာ: Formula {formula_num}"
                bot.send_message(chat_id, next_text)
        except Exception as e:
            print(f"Loop Error: {e}")

if __name__ == "__main__":
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
        print(f"Webhook set to: {RENDER_URL}/{TOKEN}")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
