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


# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN topilmadi!")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY topilmadi!")


# =========================================================
# GROQ
# =========================================================

client = Groq(api_key=GROQ_API_KEY)

MODEL = "openai/gpt-oss-20b"


# =========================================================
# GRAND MOBILE RULES
# =========================================================

RULES_FILE = "grand_mobile_qoidalari.txt"

try:
    with open(RULES_FILE, "r", encoding="utf-8") as file:
        GRAND_RULES = file.read()
except FileNotFoundError:
    raise RuntimeError(
        "grand_mobile_qoidalari.txt topilmadi! "
        "GitHub repositoryda fayl borligini tekshiring."
    )


# =========================================================
# FLASK SERVER
# =========================================================

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "🎮 Grand Mobile Bot ishlayapti!"


@web_app.route("/health")
def health():
    return "OK"


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(
        host="0.0.0.0",
        port=port
    )


# =========================================================
# AI
# =========================================================

def ask_grand_mobile_ai(question: str) -> str:

    system_prompt = f"""
Sen Grand Mobile o'yini uchun maxsus Telegram AI yordamchisisan.

Sening vazifang:
- Grand Mobile qoidalarini tushuntirish
- Qaysi qoida buzilganini aniqlash
- Qoidada ko'rsatilgan jazoni aytish
- Foydalanuvchiga sodda va tushunarli javob berish

ENG MUHIM TALABLAR:

1. FAQAT quyida berilgan Grand Mobile qoidalaridan foydalan.

2. Qoidalarda mavjud bo'lmagan ma'lumotni O'ZINGDAN QO'SHMA.

3. Agar savolga javob qoidalarda bo'lmasa, aynan:
"Bu ma'lumot men mavjud Grand Mobile qoidalarida topilmadi."
deb ayt.

4. Jazo miqdorini o'zgartirma.

5. Yangi qoida yoki yangi jazo o'ylab topma.

6. Foydalanuvchi o'zbekcha yozsa — o'zbekcha javob ber.

7. Foydalanuvchi ruscha yozsa — ruscha javob ber.

8. Foydalanuvchi inglizcha yozsa — inglizcha javob ber.

9. Javobni imkon qadar qisqa va aniq qil.

10. Agar foydalanuvchi "MG nima?", "DM nima?", "RK nima?" kabi savol bersa,
shu atamani qoidalar asosida sodda tushuntir.

11. Agar foydalanuvchi vaziyatni yozsa,
qoidalar asosida tegishli bandni ko'rsat.

12. Agar vaziyat qoidalarda aniq ko'rsatilmagan bo'lsa,
"Bu vaziyatni mavjud qoidalar asosida aniq belgilab bo'lmaydi."
deb ayt.

13. Boshqa mavzudagi savollarga:
"Men faqat Grand Mobile qoidalari bo'yicha yordam bera olaman 🎮"
deb javob ber.

14. Qoidalarda ko'rsatilgan band raqami bo'lsa,
iloji bo'lsa band raqamini ham ko'rsat.

15. Javobni o'zingdan bezama va taxmin qilma.

==================================================
GRAND MOBILE QOIDALARI
==================================================

{GRAND_RULES}

==================================================
"""


    try:

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            temperature=0.1,
            max_tokens=700
        )

        answer = response.choices[0].message.content

        if not answer:
            return "⚠️ Javob olishda xatolik yuz berdi."

        return answer.strip()

    except Exception as error:

        print("GROQ XATOSI:", error)

        return (
            "⚠️ Hozircha AI javob bera olmayapti.\n"
            "Birozdan keyin qayta urinib ko'ring."
        )


# =========================================================
# /START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = """
🎮 GRAND MOBILE AI BOT

Assalomu alaykum!

Men faqat Grand Mobile qoidalari bo'yicha yordam beraman.

Menga oddiy qilib savol berishingiz mumkin:

❓ MG nima?
❓ DM uchun qancha jazo bor?
❓ RK nima?
❓ GZda odam o'ldirsa nima bo'ladi?
❓ 3 kishiga yolg'iz chiqish mumkinmi?
❓ PG nima?

📖 Savolingizni yozing — men mavjud Grand Mobile qoidalari asosida javob beraman.
"""

    await update.message.reply_text(text)


# =========================================================
# /RESET
# =========================================================

async def reset(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "♻️ Suhbat qayta boshlandi.\n\n"
        "🎮 Grand Mobile qoidalari bo'yicha savolingizni yozing."
    )


# =========================================================
# MESSAGE
# =========================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.message.text:
        return

    question = update.message.text.strip()

    if not question:
        return

    try:
        await update.message.chat.send_action("typing")
    except Exception:
        pass

    answer = ask_grand_mobile_ai(question)

    await update.message.reply_text(
        answer,
        disable_web_page_preview=True
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print("======================================")
    print("🎮 GRAND MOBILE BOT")
    print("======================================")
    print("Telegram token topildi.")
    print("Groq API key topildi.")
    print("Grand Mobile qoidalari yuklandi.")

    # Flask server
    web_thread = threading.Thread(
        target=run_web_server,
        daemon=True
    )

    web_thread.start()

    # Telegram bot
    application = (
        Application
        .builder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

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

    print("✅ Telegram polling boshlandi...")

    application.run_polling(
        drop_pending_updates=True
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
