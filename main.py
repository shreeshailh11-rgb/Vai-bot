 from flask import Flask
import threading
import os
import logging
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from PIL import Image
import io

app = Flask(__name__)
@app.route('/')
def home():
    return "SR Vai Bot is Running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask).start()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
# Use 2.0 flash - no quota issue
model = genai.GenerativeModel("gemini-2.0-flash")
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Send me a photo 📸")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Analyzing... ⏳")
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    image = Image.open(io.BytesIO(photo_bytes))
    prompt = "You are a helpful assistant. Describe this image."
    for attempt in range(3):
        try:
            response = await model.generate_content_async([prompt, image])
            await update.message.reply_text(response.text)
            return
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                if attempt < 2:
                    await update.message.reply_text(f"Busy, retrying in 20 sec... ({attempt+1}/3)")
                    time.sleep(20)
                    continue
            await update.message.reply_text(f"Error: {err[:200]}")
            return

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = await model.generate_content_async(update.message.text)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:200]}")

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.run_polling()

if __name__ == "__main__":
    main()
