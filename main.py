    from flask import Flask
import threading
import os
import logging
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from PIL import Image
import io

app = Flask(__name__)
@app.route('/')
def home():
    return "SR WORLD VAO Bot LIVE!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

threading.Thread(target=run_flask).start()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
# Use 2.0 flash - more quota, stable
model = genai.GenerativeModel("gemini-2.0-flash")
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🙏 Namaste! SR WORLD VAO Bot LIVE!\n\nPhoto kalsi - Kannada + English answer!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Photo sigide, solving... 10 sec wait maadi")
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    image = Image.open(io.BytesIO(photo_bytes))
    prompt = "You are Karnataka VAO exam expert. Extract question from image, solve step by step in Kannada and English."
    for attempt in range(3):
        try:
            response = model.generate_content([prompt, image])
            await update.message.reply_text(response.text[:4096])
            return
        except Exception as e:
            err = str(e)
            if "429" in err and attempt < 2:
                await update.message.reply_text(f"⏳ Quota full, {20*(attempt+1)} sec wait... retrying")
                time.sleep(20)
                continue
            else:
                await update.message.reply_text(f"🙏 Swamy 1 min wait maadi, malli photo kalsi. Quota: {err[:200]}")
                return

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for attempt in range(3):
        try:
            prompt = f"Karnataka VAO question: {update.message.text}. Answer Kannada + English"
            response = model.generate_content(prompt)
            await update.message.reply_text(response.text[:4096])
            return
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(20)
                continue
            else:
                await update.message.reply_text("⏳ 1 min wait maadi, malli Hi antha kalsi 🙏")
                return

def main():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app_bot.run_polling()

if __name__ == "__main__":
    main()
