from flask import Flask
import threading
import os
import logging
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
model = genai.GenerativeModel("gemini-flash-latest")
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🙏 Namaste! SR WORLD VAO Bot LIVE aagide!\n\nPhoto kalsi - Nanu Kannada + English nalli answer madthini!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Photo sigide, solving...")
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    image = Image.open(io.BytesIO(photo_bytes))
    prompt = "You are Karnataka VAO exam expert. Extract question from image and answer in Kannada + English with explanation."
    try:
        response = model.generate_content([prompt, image])
        await update.message.reply_text(response.text[:4096])
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        prompt = f"Karnataka VAO exam question: {update.message.text}. Answer in Kannada + English"
        response = model.generate_content(prompt)
        await update.message.reply_text(response.text[:4096])
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app_bot.run_polling()

if __name__ == "__main__":
    main()
