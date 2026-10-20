 from flask import Flask
import threading
import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image
import io

app = Flask(__name__)
@app.route('/')
def home():
    return "SR Vai Bot is Running! - ONLY ENGLISH MODE"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask).start()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

model = genai.GenerativeModel("gemini-2.0-flash", safety_settings=safety_settings)
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I am SR Vai Bot. Send me a clear photo. I will answer ONLY in English like Meta AI.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Photo received, solving in English... Please wait ⏳")
    try:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        image = Image.open(io.BytesIO(photo_bytes))
        prompt = "You are VAO KPSC expert. Solve this question paper. RULE: Answer ONLY in ENGLISH. Never use Kannada. Explain clearly."
        response = await model.generate_content_async([prompt, image])
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:400]}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        q = f"Answer ONLY in English, never Kannada. User says: {update.message.text}"
        response = await model.generate_content_async(q)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:400]}")

if __name__ == "__main__":
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Bot Started - Only English Mode")
    app_bot.run_polling()
