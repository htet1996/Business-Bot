from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging
from utils import (
    send_to_channel, 
    get_formatted_exchange_rates, 
    get_formatted_crypto_prices, 
    get_formatted_crypto_news_translated
)

scheduler = AsyncIOScheduler()

async def post_exchange_rates(bot):
    try:
        message = await get_formatted_exchange_rates()
        await send_to_channel(bot, message)
        logging.info(f"✅ Exchange rates posted at {datetime.now()}")
    except Exception as e:
        logging.error(f"❌ Failed to post exchange rates: {e}")

async def post_crypto_prices(bot):
    try:
        message = await get_formatted_crypto_prices()
        await send_to_channel(bot, message)
        logging.info(f"✅ Crypto prices posted at {datetime.now()}")
    except Exception as e:
        logging.error(f"❌ Failed to post crypto prices: {e}")

async def post_crypto_news(bot):
    try:
        message = await get_formatted_crypto_news_translated()
        await send_to_channel(bot, message)
        logging.info(f"✅ Crypto news (Myanmar) posted at {datetime.now()}")
    except Exception as e:
        logging.error(f"❌ Failed to post crypto news: {e}")

def setup_scheduler(bot):
    scheduler.add_job(post_exchange_rates, IntervalTrigger(hours=2), args=[bot], id="exchange_rates", replace_existing=True)
    scheduler.add_job(post_crypto_prices, IntervalTrigger(minutes=45), args=[bot], id="crypto_prices", replace_existing=True)
    scheduler.add_job(post_crypto_news, IntervalTrigger(hours=3, minutes=30), args=[bot], id="crypto_news", replace_existing=True)
    scheduler.start()
    
    logging.info("=" * 50)
    logging.info("✅ Auto-posting scheduler started!")
    logging.info("💱 Exchange rates: every 2 hours")
    logging.info("₿ Crypto prices: every 45 minutes")
    logging.info("📰 Crypto news: every 3 hours 30 minutes (Myanmar)")
    logging.info("=" * 50)