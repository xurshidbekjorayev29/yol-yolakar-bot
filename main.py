import sqlite3
import telebot
from openai import OpenAI
from telebot import types

# ==========================================
# 1. API KALITLAR VA SOZLAMALAR
# ==========================================
BOT_TOKEN = "8745929395:AAGtESjD0aXGYMQ4EBjqiXZUOMC4BQPUaRA"
DEEPSEEK_KEY = "sk-3db2b2e3e58f4b62a65f49beee697bed"

bot = telebot.TeleBot(BOT_TOKEN)

# DeepSeek klientini ulash
ai_client = OpenAI(
    api_key=DEEPSEEK_KEY,
    base_url="https://api.deepseek.com"
)

# ==========================================
# 2. MA'LUMOTLAR BAZASI (SQLITE)
# ==========================================
def init_db():
    conn = sqlite3.connect("logistika.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            balance INTEGER DEFAULT 0,
            role TEXT DEFAULT 'user'
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, full_name):
    conn = sqlite3.connect("logistika.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, full_name) VALUES (?, ?)", (user_id, full_name))
    conn.commit()
    conn.close()

def get_user_balance(user_id):
    conn = sqlite3.connect("logistika.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

init_db()

# ==========================================
# 3. DEEPSEEK AI FUNKSIYASI
# ==========================================
def ask_deepseek(user_input):
    response = ai_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "Siz 'Yo‘l-yo‘lakay' logistika botining aqlli yordamchisisiz. Javoblaringizni o'zbek tilida, qisqa va aniq bering."},
            {"role": "user", "content": user_input}
        ],
        stream=False
    )
    return response.choices[0].message.content

# ==========================================
# 4. BOT MENYUSI VA HANDLERLAR
# ==========================================
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📦 Yuk bor (E'lon berish)")
    btn2 = types.KeyboardButton("🚚 Haydovchiman")
    btn3 = types.KeyboardButton("👤 Profil / Balans")
    markup.add(btn1, btn2)
    markup.add(btn3)
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    add_user(message.from_user.id, message.from_user.first_name)
    welcome_text = (
        f"Salom, <b>{message.from_user.first_name}</b>! 👋\n\n"
        f"<b>Yo‘l-yo‘lakay</b> AI logistika tizimiga xush kelibsiz.\n"
        f"Quyidagi menyudan kerakli bo'limni tanlang yoki AI ga savol yozing:"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="HTML", reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: m.text == "👤 Profil / Balans")
def profile_handler(message):
    balance = get_user_balance(message.from_user.id)
    text = (
        f"<b>👤 Sizning profilingiz:</b>\n\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"💰 Balansingiz: <b>{balance} so'm</b>\n\n"
        f"<i>E'lon berish yoki bog'lanish uchun balansni to'ldirishingiz kerak bo'ladi.</i>"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda message: True)
def handle_ai_message(message):
    msg = bot.send_message(message.chat.id, "⏳ <i>DeepSeek AI o'ylanmoqda...</i>", parse_mode="HTML")
    try:
        ai_response = ask_deepseek(message.text)
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_message(message.chat.id, ai_response)
    except Exception as e:
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_message(message.chat.id, f"❌ Xatolik yuz berdi: {str(e)}")

# ==========================================
# 5. BOTNI ISHGA TUSHIRISH
# ==========================================
if __name__ == "__main__":
    print("Bot DeepSeek AI moduli bilan ishga tushdi...")
    bot.infinity_polling()

