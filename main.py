import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from flask import Flask, request, jsonify
import threading

from database import init_db
from handlers import router
from scheduler import setup_scheduler

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Create bot and dispatcher instances
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
dp.include_router(router)

# Flask app for Choreo webhook
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Handle Telegram webhook requests"""
    try:
        update_data = request.get_json()
        if update_data:
            await dp.feed_update(bot, update_data)
            return "OK", 200
        return "No data", 400
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return f"Error: {e}", 500

@app.route('/health')
def health():
    return "OK", 200

@app.route('/')
def index():
    return "Business Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

async def main():
    """Main function to run the bot"""
    init_db()
    
    if CHANNEL_ID:
        logging.info(f"📢 Channel ID found: {CHANNEL_ID}")
        logging.info("🔄 Starting auto-posting scheduler...")
        setup_scheduler(bot)
    else:
        logging.warning("⚠️ CHANNEL_ID not set. Auto-posting disabled.")
    
    # Start Flask in background thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Set webhook (for Choreo)
    webhook_url = os.environ.get("WEBHOOK_URL")
    if webhook_url:
        await bot.set_webhook(url=webhook_url)
        logging.info(f"✅ Webhook set to {webhook_url}")
    else:
        logging.warning("⚠️ WEBHOOK_URL not set. Using polling...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())