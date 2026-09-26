import os
import threading
from flask import Flask
from groq import Groq
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# SOZLAMALAR
# =========================

TELEGRAM_TOKEN = os.getenv("8865716202:AAH4YKEdum7ed3PKYsJ6iSmiXXC0K0F3SoY")
GROQ_API_KEY = os.getenv("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")

MODEL = "openai/gpt-oss-20b"

if not TELEGRAM_TOKEN:
    raise RuntimeError("8865716202:AAH4YKEdum7ed3PKYsJ6iSmiXXC0K0F3SoY")

if not GROQ_API_KEY:
    raise RuntimeError("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")

client = Groq(api_key=GROQ_API_KEY)

# =========================
# GRAND MOBILE QOIDALARINI O'QISH
# =========================

RULES_FILE = "grand_mobile_qoidalari.txt"

try:
    with open(RULES_FILE, "r", encoding="utf-8") as f:
        GRAND_RULES = f.read()
except FileNotFoundError:
    raise RuntimeError(
        "grand_mobile_qoidalari.txt topilmadi! "
        "GitHub repositoryga fayl yuklanganini tekshiring."
    )

# =========================
# WEB SERVER — RENDER UCHUN
# =========================

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Grand Mobile Bot ishlayapti!"


@web_app.route("/health")
def health():
    return "OK"


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


# =========================
# AI JAVOB FUNKSIYASI
# =========================

def ask_grand_mobile_ai(question: str) -> str:

    system_prompt = f"""
Sen Grand Mobile o'yini uchun maxsus Telegram AI yordamchisisan.

Sening asosiy vazifang:
- Grand Mobile qoidalarini tushuntirish
- Qaysi qoida buzilganini aniqlash
- Qoidada ko'rsatilgan jazoni aytish
- Foydalanuvchi savoliga sodda va tushunarli javob berish

MUHIM QOIDALAR:

1. Javoblaring FAQAT quyida berilgan Grand Mobile qoidalariga asoslanishi kerak.

2. Qoidalarda mavjud bo'lmagan ma'lumotni o'zingdan qo'shma.

3. Agar kerakli ma'lumot qoidalarda bo'lmasa:
"Bu ma'lumot men mavjud Grand Mobile qoidalarida topilmadi."
deb ayt.

4. Jazo miqdorini o'zgartirma.

5. O'zingdan yangi qoida, yangi jazo yoki yangi taqiq o'ylab topma.

6. Foydalanuvchi o'zbekcha yozsa — o'zbekcha javob ber.
Ruscha yozsa — ruscha javob ber.
Inglizcha yozsa — inglizcha javob ber.

7. Javoblarni juda uzun qilma. Avval qisqa va aniq javob ber.

8. Agar foydalanuvchi "bu nima?", "nima degani?" deb so'rasa, tegishli atamani sodda tushuntir.

9. Agar foydalanuvchi vaziyatni yozsa, qoidalar asosida qaysi bandga yaqinligini tushuntir.
Lekin qoidada aniq bo'lmasa, "aniq belgilab bo'lmaydi" deb ayt.

10. Foydalanuvchi boshqa mavzuda savol bersa:
"Men faqat Grand Mobile qoidalari bo'yicha yordam bera olaman 🎮"
deb javob ber.

GRAND MOBILE QOIDALARI:

{GRAND_RULES}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            temperature=0.2,
            max_tokens=700,
        )

        answer = response.choices[0].message.content

        if not answer:
            return "Javob olishda xatolik yuz berdi."

        return answer.strip()

    except Exception as e:
        print("Groq xatosi:", e)
        return "⚠️ Hozircha AI javob bera olmayapti. Birozdan keyin qayta urinib ko'ring."


# =========================
# /START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
🎮 GRAND MOBILE AI BOT

Assalomu alaykum!

Men faqat Grand Mobile qoidalari bo'yicha yordam beraman.

Menga masalan:

❓ "MG nima?"

❓ "DM uchun qancha jazo bor?"

❓ "3 kishiga yolg'iz chiqish mumkinmi?"

❓ "GZda odam o'ldirsa nima bo'ladi?"

❓ "RK nima?"

kabi savollar berishingiz mumkin.

📖 Savolingizni oddiy yozing — men Grand Mobile qoidalari asosida javob beraman.
"""

    await update.message.reply_text(text)


# =========================
# /RESET
# =========================

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "♻️ Suhbat konteksti tozalandi.\n\n"
        "🎮 Grand Mobile qoidalari bo'yicha savolingizni yozing."
    )


# =========================
# XABARLARNI QABUL QILISH
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    question = update.message.text.strip()

    if not question:
        return

    # Foydalanuvchiga javob tayyorlanayotganini ko'rsatish
    await update.message.chat.send_action("typing")

    answer = ask_grand_mobile_ai(question)

    await update.message.reply_text(
        answer,
        disable_web_page_preview=True
    )


# =========================
# BOTNI ISHGA TUSHIRISH
# =========================

def main():

    print("====================================")
    print("🎮 GRAND MOBILE BOT ISHGA TUSHDI")
    print("====================================")

    # Flask serverni alohida thread'da ishga tushiramiz
    web_thread = threading.Thread(
        target=run_web_server,
        daemon=True
    )

    web_thread.start()

    # Telegram bot
    application = Application.builder().token(
        TELEGRAM_TOKEN
    ).build()

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("reset", reset)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("Telegram polling boshlandi...")

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
