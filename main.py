 from flask import Flask
import threading
import os
import logging
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
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

# Safety OFF - no block
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

model = genai.GenerativeModel("gemini-2.0-flash", safety_settings=safety_settings)
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Send me a clear photo 📸")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Photo sigide, solving... ⏳")
    try:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        image = Image.open(io.BytesIO(photo_bytes))
        prompt = "You are an expert teacher. Read this question paper image carefully. Even if blurry, try your best. Explain each question answer in Kannada and English. If you can't read, say 'Photo clear illa, swalpa hattira inda photo tagiri'"
        response = await model.generate_content_async([prompt, image])
        # Check if blocked
        if not response.candidates or not response.candidates[0].content.parts:
            await update.message.reply_text("Photo clear illa! Dayavittu hattira inda clear photo tagiri. / Please take a clearer photo closer to paper.")
            return
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:400]}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = await model.generate_content_async(update.message.text)
        if response.text:
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("Sorry, try again!")
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
