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
    return "SR Vai Bot is Running! - ONLY ENGLISH MODE"

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
    await update.message.reply_text("Hi! I am SR Vai Bot. Send me a clear photo of question paper. I will answer ONLY in English.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Photo received, solving... Please wait ⏳")
    try:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        image = Image.open(io.BytesIO(photo_bytes))
        prompt = """You are an expert teacher for VAO, KPSC, PDO exams.
        Read this question paper image carefully and solve ALL questions.
        
        IMPORTANT RULES - FOLLOW STRICTLY:
        1. Answer ONLY in ENGLISH language.
        2. NEVER use Kannada language. 
        3. Format: For each question: Question Number, Correct Answer, Detailed Explanation in English.
        4. If the image is a crop/farm, identify the crop in English.
        5. Be accurate and helpful like Meta AI.
        """
        response = await model.generate_content_async([prompt, image])
        if not response.candidates or not response.candidates[0].content.parts:
            await update.message.reply_text("Photo is not clear. Please take a clearer photo.")
            return
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:400]}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # FORCE ONLY ENGLISH FOR TEXT ALSO
        english_prompt = f"Answer ONLY in English language. User question: {update.message.text}"
        response = await model.generate_content_async(english_prompt)
        if response.text:
            await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:400]}")

# Build bot
from telegram.ext import Application
import asyncio

async def main_bot():
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    await app_bot.run_polling()

# Run
if __name__ == "__main__":
    # To avoid conflict with Flask thread
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main_bot()) 
