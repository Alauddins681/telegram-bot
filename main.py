# This tool was created by@Nexus  Respect the developer's work.CREDITS =Channel:Nexus
import telebot
import requests
import time
import json
import threading
import os
imort sys
from io import BytesIO
BOT_ACTIVE = True
ADMIN_ID = 953030386

# --- CONFIGURATION ---
# Use environment variable if available, else use hardcoded token
API_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '7927527224:AAEWk-HXpsTnnus9s6T1ZiZRPVpM_oA2_a8')
bot = telebot.TeleBot(API_TOKEN)
BOT_ACTIVE = True

@bot.message_handler(commands=['off'])
def stop_bot(message):
    global BOT_ACTIVE
    if message.from_user.id == ADMIN_ID:
        BOT_ACTIVE = False
        bot.reply_to(message, "🛑 Bot OFF ho gaya")

@bot.message_handler(commands=['on'])
def start_bot(message):
    global BOT_ACTIVE
    if message.from_user.id == ADMIN_ID:
        BOT_ACTIVE = True
        bot.reply_to(message, "✅ Bot ON ho gaya")
        @bot.message_handler(commands=['kill'])
def kill_bot(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "💀 Server stopping...")

# Store user data
user_sessions = {}

# --- COOKIE PARSER ---
def smart_cookie_parser(file_content):
    try:
        text_data = file_content.decode('utf-8').strip()
        
        # 1. Try parsing as JSON
        try:
            json_data = json.loads(text_data)
            if isinstance(json_data, list):
                cookies = []
                for item in json_data:
                    if isinstance(item, dict) and 'name' in item and 'value' in item:
                        cookies.append(f"{item['name']}={item['value']}")
                return "; ".join(cookies)
            elif isinstance(json_data, dict):
                return json_data.get('cookie_string') or json_data.get('cookie')
        except:
            pass
            
        # 2. Raw Text Check
        if "=" in text_data and ";" in text_data:
            return text_data
            
    except Exception:
        return None
    return None

# --- API HEADERS ---
def get_headers(cookie):
    return {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://www.sheinindia.in",
        "referer": "https://www.sheinindia.in/cart",
        "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "x-tenant-id": "SHEIN",
        "cookie": cookie
    }

# --- MAIN CHECKING LOOP ---
def run_protection_cycle(chat_id):
    if chat_id not in user_sessions: return

    try:
        bot.send_message(chat_id, "✅ **System Active.** Checks will run every 5 minutes.", parse_mode="Markdown")
    except: pass

    while True:
        if not BOT_ACTIVE:
            time.sleep(5)
            continue
        if chat_id not in user_sessions: break
        
        cookie = user_sessions[chat_id].get('cookie')
        vouchers = user_sessions[chat_id].get('vouchers')
        
        if not cookie or not vouchers:
            try:
                bot.send_message(chat_id, "⚠️ Data missing. Please restart.")
            except: pass
            break

        headers = get_headers(cookie)
        valid = []
        invalid = []
        
        try:
            status_msg = bot.send_message(chat_id, "⏳ **Initializing Check...**")
            total = len(vouchers)

            for index, code in enumerate(vouchers, 1):
                if index % 3 == 0 or index == total:
                    try:
                        bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=status_msg.message_id,
                            text=(
                                f"🔄 **Processing Vouchers...**\n\n"
                                f"🔸 Current: `{code}`\n"
                                f"📊 Progress: {index}/{total}\n"
                                f"✅ Valid: {len(valid)}\n"
                                f"❌ Invalid: {len(invalid)}"
                            ),
                            parse_mode="Markdown"
                        )
                    except: pass

                try:
                    payload = {"voucherId": code, "device": {"client_type": "mobile"}}
                    res = requests.post("https://www.sheinindia.in/api/cart/apply-voucher", 
                                        json=payload, headers=headers, timeout=10)
                    
                    is_valid = False
                    if res.status_code == 200:
                        resp_json = res.json()
                        if not (resp_json.get("errorMessage")):
                            is_valid = True
                    
                    if is_valid:
                        valid.append(code)
                        try:
                            requests.post("https://www.sheinindia.in/api/cart/reset-voucher", 
                                          json=payload, headers=headers, timeout=5)
                        except: pass 
                    else:
                        invalid.append(code)
                except:
                    invalid.append(code)
                
                time.sleep(1.2)

            try:
                bot.delete_message(chat_id, status_msg.message_id)
            except: pass

            if valid:
                f = BytesIO("\n".join(valid).encode())
                f.name = "valid_vouchers.txt"
                bot.send_document(chat_id, f, caption=f"✅ **Valid Vouchers ({len(valid)})**")
            
            if invalid:
                f = BytesIO("\n".join(invalid).encode())
                f.name = "invalid_vouchers.txt"
                bot.send_document(chat_id, f, caption=f"❌ **Invalid Vouchers ({len(invalid)})**")

            bot.send_message(chat_id, "💤 **Cycle Complete.** Waiting 5 minutes for next check...")
        except Exception as e:
            print(f"Error in cycle: {e}")
            
        time.sleep(300)

@bot.message_handler(commands=['start'])
def start(m):
    user_sessions[m.chat.id] = {} 
    bot.reply_to(m, "👋 **Welcome.**\n\nPlease send your `cookies.json` file to begin.")

@bot.message_handler(content_types=['document'])
def handle_files(m):
    chat_id = m.chat.id
    fname = m.document.file_name.lower()
    
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}

    if "voucher" in fname:
        if 'cookie' not in user_sessions[chat_id]:
            bot.reply_to(m, "⚠️ **Wait!** Please send Cookie file first.")
            return

        try:
            file_info = bot.get_file(m.document.file_id)
            content = bot.download_file(file_info.file_path).decode('utf-8')
            codes = [x.strip() for x in content.split() if x.strip()]
            
            if not codes:
                bot.reply_to(m, "❌ File is empty.")
                return

            user_sessions[chat_id]['vouchers'] = codes
            bot.reply_to(m, f"📥 Received **{len(codes)}** vouchers.\nStarting protection engine...")
            
            threading.Thread(target=run_protection_cycle, args=(chat_id,), daemon=True).start()
        except:
            bot.reply_to(m, "❌ Error reading voucher file.")
        return

    if "json" in fname or "cookie" in fname or "txt" in fname:
        try:
            file_info = bot.get_file(m.document.file_id)
            content = bot.download_file(file_info.file_path)
            
            cookie_str = smart_cookie_parser(content)
            
            if cookie_str:
                user_sessions[chat_id]['cookie'] = cookie_str
                bot.reply_to(m, "✅ **Cookies Verified.**\n\nNow, please send the `vouchers.txt` file.")
            else:
                bot.reply_to(m, "❌ **Invalid Cookie File.**\nEnsure file name is correct or check content.")
        except:
            bot.reply_to(m, "❌ Error processing file.")
        return

@bot.message_handler(func=lambda m: True)
def handle_text(m):
    if not BOT_ACTIVE:
        return
    chat_id = m.chat.id
    if chat_id in user_sessions and 'cookie' in user_sessions[chat_id]:
        codes = [x.strip() for x in m.text.split() if x.strip()]
        if codes:
            user_sessions[chat_id]['vouchers'] = codes
            bot.reply_to(m, f"📥 Detected **{len(codes)}** codes.\nStarting engine...")
            threading.Thread(target=run_protection_cycle, args=(chat_id,), daemon=True).start()
    else:
        bot.reply_to(m, "⚠️ Please send the **Cookie file** first.")

if __name__ == "__main__":
    print("Bot is starting...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot polling error: {e}")
            time.sleep(5)
