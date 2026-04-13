# utils.py - Full Code (No static fallback, live RSS only with timeout)
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
import csv
from aiogram import Bot
from deep_translator import GoogleTranslator

MM_TZ = pytz.timezone('Asia/Yangon')
translator = GoogleTranslator(source='en', target='my')

# ========== MYANMAR CURRENCY API ONLY ==========
async def get_live_exchange_rates():
    """
    Get exchange rates from Myanmar Currency API (CBM Reference Rate)
    """
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
                    
                    rates['MMK'] = 1
                    
                    print(f"✅ Myanmar Currency API rates fetched at {datetime.now()}")
                    return rates
                else:
                    print(f"❌ API returned status {response.status}")
                    raise Exception(f"API returned {response.status}")
                    
    except Exception as e:
        print(f"❌ Failed to fetch exchange rates: {e}")
        raise Exception(f"Cannot fetch exchange rates: {e}")

# ========== LIVE CRYPTO NEWS WITH TIMEOUT ==========
async def get_live_crypto_news(limit: int = 5):
    """Get latest crypto news from RSS feeds with timeout"""
    try:
        rss_feeds = [
            "https://cointelegraph.com/rss",
            "https://cryptoslate.com/feed/",
            "https://decrypt.co/feed",
        ]
        all_news = []
        
        for feed_url in rss_feeds:
            try:
                # Parse RSS with timeout
                loop = asyncio.get_event_loop()
                feed = await asyncio.wait_for(
                    loop.run_in_executor(None, feedparser.parse, feed_url),
                    timeout=5
                )
                for entry in feed.entries[:2]:
                    all_news.append({
                        'title': entry.get('title', 'No Title'),
                        'source': feed.feed.get('title', 'Unknown'),
                        'url': entry.get('link', '#'),
                        'published_at': entry.get('published', '')
                    })
            except asyncio.TimeoutError:
                print(f"⚠️ Timeout for {feed_url}")
                continue
            except Exception as e:
                print(f"⚠️ Error for {feed_url}: {e}")
                continue
        
        if all_news:
            return all_news[:limit]
        else:
            raise Exception("No news available from RSS feeds")
            
    except Exception as e:
        print(f"RSS news error: {e}")
        raise Exception(f"Cannot fetch crypto news: {e}")

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

# ========== CSV EXPORT ==========
def export_to_csv(transactions: list) -> io.BytesIO:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Amount (MMK)", "Category"])
    for trans in transactions:
        writer.writerow([
            trans.get('date', ''),
            trans.get('type', '').capitalize(),
            trans.get('amount', 0),
            trans.get('category', '')
        ])
    total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    balance = total_income - total_expense
    writer.writerow([])
    writer.writerow(["SUMMARY", "", "", ""])
    writer.writerow(["Total Income", "", f"{total_income:,.0f}", ""])
    writer.writerow(["Total Expense", "", f"{total_expense:,.0f}", ""])
    writer.writerow(["Balance", "", f"{balance:,.0f}", ""])
    
    csv_bytes = io.BytesIO(output.getvalue().encode('utf-8-sig'))
    return csv_bytes

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
        if curr != 'MMK':
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
        raise Exception("Failed to fetch crypto prices")

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