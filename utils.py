import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from openpyxl import Workbook
from datetime import datetime
import pytz
import aiohttp
import asyncio
import feedparser
import os
from aiogram import Bot
from deep_translator import GoogleTranslator

MM_TZ = pytz.timezone('Asia/Yangon')
translator = GoogleTranslator(source='en', target='my')

# ========== TRANSLATION ==========
async def translate_to_myanmar(text: str) -> str:
    if not text or len(text.strip()) == 0:
        return text
    try:
        loop = asyncio.get_event_loop()
        translated = await loop.run_in_executor(None, translator.translate, text)
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text

# ========== CHART ==========
def create_expense_chart(data: dict, title: str) -> io.BytesIO:
    if not data:
        return None
    categories = list(data.keys())
    amounts = list(data.values())
    plt.figure(figsize=(8, 6))
    plt.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90)
    plt.title(title)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf

# ========== EXCEL EXPORT ==========
def export_to_excel(transactions: list) -> io.BytesIO:
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Transactions"
        headers = ["Date", "Type", "Amount (MMK)", "Category"]
        ws.append(headers)
        for trans in transactions:
            ws.append([
                trans.get('date', ''),
                trans.get('type', '').capitalize(),
                trans.get('amount', 0),
                trans.get('category', '')
            ])
        for col in ['A', 'B', 'C', 'D']:
            ws.column_dimensions[col].width = 15
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf
    except Exception as e:
        raise Exception(f"Excel export failed: {str(e)}")

# ========== SEND TO CHANNEL ==========
async def send_to_channel(bot: Bot, message: str):
    channel_id = os.getenv("CHANNEL_ID")
    if channel_id:
        try:
            await bot.send_message(chat_id=channel_id, text=message, parse_mode="HTML")
            print(f"✅ Message sent to channel: {channel_id}")
        except Exception as e:
            print(f"❌ Failed to send to channel: {e}")

# ========== FORMATTED MESSAGES ==========
async def get_formatted_exchange_rates() -> str:
    rates = await get_live_exchange_rates()
    message = "💱 <b>Live Exchange Rates (MMK)</b>\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━\n"
    for curr, rate in rates.items():
        message += f"• 1 {curr} = <code>{rate:,.0f} MMK</code>\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += f"🕐 {datetime.now(MM_TZ).strftime('%Y-%m-%d %H:%M:%S')}"
    return message

async def get_formatted_crypto_prices() -> str:
    cryptos = await get_live_crypto_prices()
    message = "₿ <b>Live Crypto Prices</b>\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━\n"
    for crypto in cryptos[:5]:
        mmk_price = crypto['price'] * 3500
        message += f"• {crypto['symbol']} - {crypto['name']}\n"
        message += f"  💰 <code>${crypto['price']:,.2f} USD</code>\n"
        message += f"  📊 ≈ <code>{mmk_price:,.0f} MMK</code>\n\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += f"🕐 {datetime.now(MM_TZ).strftime('%Y-%m-%d %H:%M:%S')}"
    return message

async def get_formatted_crypto_news_translated() -> str:
    news_list = await get_live_crypto_news(limit=3)
    message = "📰 <b>နောက်ဆုံး Crypto သတင်းများ (မြန်မာလို)</b>\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for news in news_list:
        title_mm = await translate_to_myanmar(news['title'])
        message += f"📌 <b>{title_mm}</b>\n"
        message += f"   📍 {news['source']}\n"
        message += f"   🔗 <a href='{news['url']}'>အသေးစိတ်ဖတ်ရန်</a>\n\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += f"🕐 {datetime.now(MM_TZ).strftime('%Y-%m-%d %H:%M:%S')}"
    return message

# ========== LIVE CRYPTO PRICES ==========
async def get_live_crypto_prices():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,binancecoin,solana,ripple,dogecoin,cardano,avalanche-2,polkadot,polygon&vs_currencies=usd"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return [
                        {'symbol': 'BTC', 'name': 'Bitcoin', 'price': data.get('bitcoin', {}).get('usd', 65000)},
                        {'symbol': 'ETH', 'name': 'Ethereum', 'price': data.get('ethereum', {}).get('usd', 3500)},
                        {'symbol': 'BNB', 'name': 'Binance Coin', 'price': data.get('binancecoin', {}).get('usd', 600)},
                        {'symbol': 'SOL', 'name': 'Solana', 'price': data.get('solana', {}).get('usd', 180)},
                        {'symbol': 'XRP', 'name': 'Ripple', 'price': data.get('ripple', {}).get('usd', 0.6)},
                        {'symbol': 'DOGE', 'name': 'Dogecoin', 'price': data.get('dogecoin', {}).get('usd', 0.15)},
                        {'symbol': 'ADA', 'name': 'Cardano', 'price': data.get('cardano', {}).get('usd', 0.45)},
                        {'symbol': 'AVAX', 'name': 'Avalanche', 'price': data.get('avalanche-2', {}).get('usd', 35)},
                        {'symbol': 'DOT', 'name': 'Polkadot', 'price': data.get('polkadot', {}).get('usd', 7)},
                        {'symbol': 'MATIC', 'name': 'Polygon', 'price': data.get('polygon', {}).get('usd', 0.8)}
                    ]
    except Exception as e:
        print(f"Crypto API error: {e}")
        return get_static_crypto_prices()

def get_static_crypto_prices():
    return [
        {'symbol': 'BTC', 'name': 'Bitcoin', 'price': 65000},
        {'symbol': 'ETH', 'name': 'Ethereum', 'price': 3500},
        {'symbol': 'BNB', 'name': 'Binance Coin', 'price': 600},
        {'symbol': 'SOL', 'name': 'Solana', 'price': 180},
        {'symbol': 'XRP', 'name': 'Ripple', 'price': 0.6},
        {'symbol': 'DOGE', 'name': 'Dogecoin', 'price': 0.15},
        {'symbol': 'ADA', 'name': 'Cardano', 'price': 0.45},
        {'symbol': 'AVAX', 'name': 'Avalanche', 'price': 35},
        {'symbol': 'DOT', 'name': 'Polkadot', 'price': 7},
        {'symbol': 'MATIC', 'name': 'Polygon', 'price': 0.8}
    ]

# ========== LIVE EXCHANGE RATES ==========
async def get_live_exchange_rates():
    try:
        url = "https://myanmar-currency-api.github.io/api/latest.json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    rates = {}
                    for item in data.get('data', []):
                        currency = item.get('currency', '')
                        if currency in ['USD', 'SGD', 'THB', 'JPY', 'CNY', 'KRW', 'AED', 'EUR']:
                            rates[currency] = float(item.get('sell', 0))
                    if 'AED' not in rates and 'USD' in rates:
                        rates['AED'] = rates['USD'] * 3.67
                    if 'KRW' not in rates and 'USD' in rates:
                        rates['KRW'] = rates['USD'] / 1300
                    return rates
    except Exception as e:
        print(f"Exchange rate API error: {e}")
        return get_static_exchange_rates()

def get_static_exchange_rates():
    return {
        'USD': 3500, 'SGD': 2600, 'THB': 100, 'JPY': 23,
        'CNY': 480, 'KRW': 2.6, 'AED': 950, 'EUR': 3800
    }

# ========== LIVE CRYPTO NEWS ==========
async def get_live_crypto_news(limit: int = 10):
    try:
        rss_feeds = [
            "https://cointelegraph.com/rss",
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://cryptoslate.com/feed/",
            "https://decrypt.co/feed",
            "https://u.today/rss",
            "https://news.bitcoin.com/feed/",
        ]
        all_news = []
        for feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:3]:
                    all_news.append({
                        'title': entry.get('title', 'No Title'),
                        'source': feed.feed.get('title', 'Unknown'),
                        'url': entry.get('link', '#'),
                        'published_at': entry.get('published', '')
                    })
            except Exception as e:
                print(f"RSS feed error for {feed_url}: {e}")
                continue
        all_news = all_news[:limit]
        if all_news:
            return all_news
        else:
            return get_static_crypto_news()
    except Exception as e:
        print(f"RSS news error: {e}")
        return get_static_crypto_news()

def get_static_crypto_news():
    return [
        {"title": "Bitcoin ETF များ ထပ်မံခွင့်ပြု", "source": "Crypto News", "url": "https://cointelegraph.com", "published_at": ""},
        {"title": "Ethereum 2.0 Upgrade ပြီးစီး", "source": "Blockchain Journal", "url": "https://coindesk.com", "published_at": ""},
        {"title": "Binance မှ လုပ်ငန်းသစ်များ မိတ်ဆက်", "source": "Crypto Times", "url": "https://cryptoslate.com", "published_at": ""},
    ]

# ========== TUTORIALS ==========
TUTORIALS = [
    {"name": "Myan Crypto", "channel": "Crypto Myanmar", "reason": "အခြေခံမှစ၍ ရှင်းလင်းချက်ကောင်း", "url": "https://youtube.com/@myancrypto"},
    {"name": "Blockchain Academy Myanmar", "channel": "Blockchain Academy", "reason": "ပညာဒါန သင်ခန်းစာများ", "url": "https://youtube.com/@blockchainacademy"},
    {"name": "MM Crypto Guide", "channel": "MM Crypto", "reason": "လက်တွေ့ကျသော အကြံပြုချက်များ", "url": "https://youtube.com/@mmcrypto"},
    {"name": "Myan Crypto101", "channel": "Crypto News", "reason": "နောက်ဆုံးရ Crypto သတင်းများ", "url": "https://www.youtube.com/@myancrypto101"},
    {"name": "Crypto Hunter MM", "channel": "Crypto Hunter", "reason": "Airdrop နှင့် လက်ဆောင်များ", "url": "https://youtube.com/@cryptohunter"},
    {"name": "Smart Money Myanmar", "channel": "Smart Money", "reason": "ဘေးကင်းရေး သတိပေးချက်များ", "url": "https://youtube.com/@smartmoney"},
    {"name": "Crypto Wave MM", "channel": "Crypto Wave", "reason": "Market analysis အချိန်နှင့်တစ်ပြေးညီ", "url": "https://youtube.com/@cryptowave"},
    {"name": "Digital Gold Myanmar", "channel": "Digital Gold MM", "reason": "Bitcoin သမိုင်းနှင့် အနာဂတ်", "url": "https://youtube.com/@digitalgold"},
    {"name": "Crypto Master MM", "channel": "Crypto Master", "reason": "Trading strategies အဆင့်မြင့်", "url": "https://youtube.com/@cryptomaster"},
    {"name": "MM Bitcoin Trading", "channel": "Bitcoin Trading", "reason": "Bitcoin trading နည်းပညာများ", "url": "https://youtube.com/@mmbitcointrading"},
    {"name": "Crypto Finance Myanmar", "channel": "Crypto Finance", "reason": "ဘဏ္ဍာရေးနှင့် ရင်းနှီးမြှုပ်နှံမှု", "url": "https://youtube.com/@cryptofinancemm"},
    {"name": "DeFi Myanmar", "channel": "DeFi MM", "reason": "Decentralized Finance အကြောင်း", "url": "https://youtube.com/@defimyanmar"},
    {"name": "NFT Myanmar Hub", "channel": "NFT Hub", "reason": "NFT နှင့် Digital Art အကြောင်း", "url": "https://youtube.com/@nftmyanmar"},
    {"name": "Crypto Tips Myanmar", "channel": "Crypto Tips", "reason": "အမြန်လမ်းညွှန်ချက်များ", "url": "https://youtube.com/@cryptotipsmm"},
    {"name": "Web3 Myanmar", "channel": "Web3 MM", "reason": "Web3 နည်းပညာအကြောင်း", "url": "https://youtube.com/@web3myanmar"},
]

# ========== BUDGET STATUS ==========
def check_budget_status(used: float, limit: float) -> tuple:
    if limit == 0:
        return 0, False
    percentage = (used / limit) * 100
    should_notify = percentage >= 70
    return percentage, should_notify