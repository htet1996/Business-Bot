from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from datetime import datetime
import os

from database import get_db, get_dashboard
from keyboards import (
    main_menu, expense_menu, cancel_keyboard, budget_period_keyboard,
    currency_menu_keyboard, crypto_menu_keyboard, tutorial_menu_keyboard
)
from utils import *
from config import CHANNEL_ID, CHANNEL_LINK

router = Router()

# FSM States
class ExpenseEntry(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()
    entry_type = State()

class BudgetSetup(StatesGroup):
    waiting_for_amount = State()
    period = State()

previous_rates = {}

# ========== FORCE JOIN CHANNEL FUNCTIONS ==========
async def check_channel_membership(user_id: int, bot: Bot) -> tuple:
    """Check if user is a member of the channel"""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        is_member = member.status in ['member', 'creator', 'administrator']
        return is_member, None
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False, str(e)

async def ask_to_join_channel(message: Message, bot: Bot):
    """Send message asking user to join channel"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="✅ I've Joined", callback_data="check_joined")]
    ])
    
    await message.answer(
        "🔔 <b>Channel ကို Join လုပ်ပေးပါရန် လိုအပ်ပါသည်</b>\n\n"
        "ကျွန်ုပ်တို့၏ Bot ကို အသုံးပြုရန်အတွက် အောက်ပါ Channel ကို Join လုပ်ပေးပါ။\n\n"
        "👉 <b>Channel ကို Join လုပ်ပြီးပါက '✅ I've Joined' ကိုနှိပ်ပါ။</b>",
        parse_mode="HTML",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

@router.callback_query(F.data == "check_joined")
async def check_joined(callback: CallbackQuery, bot: Bot):
    """Check if user has joined after clicking button"""
    user_id = callback.from_user.id
    is_member, _ = await check_channel_membership(user_id, bot)
    
    if is_member:
        # Add user to database
        with get_db() as db:
            db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        
        await callback.message.delete()
        await callback.message.answer(
            "✅ ကျေးဇူးတင်ပါတယ်။ ယခု Bot ကို စတင်အသုံးပြုနိုင်ပါပြီ။\n\n"
            "👇 အောက်ပါ Menu မှ လိုအပ်တဲ့ Feature ကို ရွေးချယ်ပါ။",
            reply_markup=main_menu()
        )
        await callback.answer("✅ Channel join လုပ်ပြီးပါပြီ။")
    else:
        await callback.answer(
            "❌ သင်သည် Channel ကို မဝင်ရသေးပါ။ ကျေးဇူးပြု၍ Join လုပ်ပါ။",
            show_alert=True
        )

# ========== START COMMAND ==========
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    
    # Check if user joined channel
    is_member, _ = await check_channel_membership(message.from_user.id, bot)
    
    if not is_member:
        await ask_to_join_channel(message, bot)
        return
    
    # User is member, proceed normally
    with get_db() as db:
        db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
    
    await message.answer(
        f"🌟 <b>မင်္ဂလာပါ {message.from_user.first_name}</b> ခင်ဗျာ။\n\n"
        f"<b>🔥 Business Bot</b> မှ သင့်ရဲ့ ငွေကြေးစီမံခန့်ခွဲမှုကို ကူညီပေးပါမယ်။\n\n"
        f"✨ <b>ထူးခြားချက်များ</b> ✨\n"
        f"💰 နေ့စဉ်ငွေစာရင်း\n"
        f"💱 ငွေလဲနှုန်း (Live)\n"
        f"₿ Crypto Currency (Live)\n"
        f"📘 Crypto Tutorials\n\n"
        f"👇 အောက်ပါ Menu မှ လိုအပ်တဲ့ Feature ကို ရွေးချယ်ပါ။",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

# ========== EXPENSE TRACKER ==========
@router.callback_query(F.data == "menu_expense")
async def expense_menu_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    is_member, _ = await check_channel_membership(callback.from_user.id, bot)
    if not is_member:
        await ask_to_join_channel(callback.message, bot)
        await callback.answer()
        return
    
    await state.clear()
    await callback.message.edit_text(
        "💰 Expense Tracker Menu။\n\nအောက်ပါရွေးချယ်စရာများထဲမှ ရွေးချယ်ပါ။",
        reply_markup=expense_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "exp_dashboard")
async def show_dashboard(callback: CallbackQuery, bot: Bot):
    is_member, _ = await check_channel_membership(callback.from_user.id, bot)
    if not is_member:
        await ask_to_join_channel(callback.message, bot)
        await callback.answer()
        return
    
    data = get_dashboard(callback.from_user.id)
    dashboard_text = (
        f"📊 <b>ယနေ့ Dashboard</b> 📊\n━━━━━━━━━━━━━━━━━━━\n"
        f"💰 ယနေ့ဝင်ငွေ: <code>{data['today_income']:,.0f} MMK</code>\n"
        f"💸 ယနေ့သုံးစွဲငွေ: <code>{data['today_expense']:,.0f} MMK</code>\n"
        f"📌 ယနေ့လက်ကျန်: <code>{data['today_balance']:,.0f} MMK</code>\n\n"
        f"📊 <b>စုစုပေါင်း Dashboard</b> 📊\n━━━━━━━━━━━━━━━━━━━\n"
        f"💰 စုစုပေါင်းဝင်ငွေ: <code>{data['total_income']:,.0f} MMK</code>\n"
        f"💸 စုစုပေါင်းသုံးစွဲငွေ: <code>{data['total_expense']:,.0f} MMK</code>\n"
        f"📌 စုစုပေါင်းလက်ကျန်: <code>{data['total_balance']:,.0f} MMK</code>\n"
    )
    await callback.message.edit_text(dashboard_text, parse_mode="HTML", reply_markup=expense_menu())
    await callback.answer()

@router.callback_query(F.data == "exp_income")
async def add_income_start(callback: CallbackQuery, state: FSMContext, bot: Bot):
    is_member, _ = await check_channel_membership(callback.from_user.id, bot)
    if not is_member:
        await ask_to_join_channel(callback.message, bot)
        await callback.answer()
        return
    
    await state.set_state(ExpenseEntry.waiting_for_amount)
    await state.update_data(entry_type="income")
    await callback.message.edit_text(
        "💰 ဝင်ငွေပမာဏကို ဂဏန်းသက်သက်ဖြင့် ထည့်ပါ။\n\nဥပမာ - 500000\n\nမလုပ်တော့ပါက 'Cancel' ကိုနှိပ်ပါ။",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "exp_expense")
async def add_expense_start(callback: CallbackQuery, state: FSMContext, bot: Bot):
    is_member, _ = await check_channel_membership(callback.from_user.id, bot)
    if not is_member:
        await ask_to_join_channel(callback.message, bot)
        await callback.answer()
        return
    
    await state.set_state(ExpenseEntry.waiting_for_amount)
    await state.update_data(entry_type="expense")
    await callback.message.edit_text(
        "💸 သုံးစွဲငွေပမာဏကို ဂဏန်းသက်သက်ဖြင့် ထည့်ပါ။\n\nဥပမာ - 25000\n\nမလုပ်တော့ပါက 'Cancel' ကိုနှိပ်ပါ။",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    await callback.answer()

@router.message(ExpenseEntry.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            await message.answer("ကျေးဇူးပြု၍ အပေါင်းဂဏန်း (positive number) ထည့်ပါ။", reply_markup=cancel_keyboard())
            return
        await state.update_data(amount=amount)
        await state.set_state(ExpenseEntry.waiting_for_category)
        await message.answer(
            "📂 အမျိုးအစား (Category) ကိုထည့်ပါ။\n\nဥပမာ - စားသောက်ဆိုင်, ခရီးသွား, လစာ",
            reply_markup=cancel_keyboard()
        )
    except ValueError:
        await message.answer("ကျေးဇူးပြု၍ ဂဏန်းသက်သက်သာ ထည့်ပါ။", reply_markup=cancel_keyboard())

@router.message(ExpenseEntry.waiting_for_category)
async def process_category(message: Message, state: FSMContext):
    category = message.text.strip()
    if len(category) > 50:
        await message.answer("Category သည် အက္ခရာ 50 လုံးအောက်သာ ထည့်ပါ။", reply_markup=cancel_keyboard())
        return
    data = await state.get_data()
    amount = data['amount']
    entry_type = data['entry_type']
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db() as db:
        db.execute("INSERT INTO transactions (user_id, type, amount, category, date) VALUES (?, ?, ?, ?, ?)", (message.from_user.id, entry_type, amount, category, today))
    type_text = "ဝင်ငွေ" if entry_type == "income" else "သုံးစွဲငွေ"
    await message.answer(f"✅ အောင်မြင်ပါပြီ။\n\n{type_text}: <code>{amount:,.0f} MMK</code>\nCategory: <b>{category}</b>\n📅 {today}", parse_mode="HTML", reply_markup=expense_menu())
    await state.clear()

# ========== EXPORT TO GOOGLE SHEETS ==========
@router.callback_query(F.data == "exp_excel")
async def export_excel(callback: CallbackQuery, bot: Bot):
    is_member, _ = await check_channel_membership(callback.from_user.id, bot)
    if not is_member:
        await ask_to_join_channel(callback.message, bot)
        await callback.answer()
        return
    
    msg = await callback.message.edit_text("⏳ Google Sheets သို့ ထုတ်ယူနေပါသည်...")
    
    with get_db() as db:
        rows = db.execute(
            "SELECT date, type, amount, category FROM transactions WHERE user_id = ? ORDER BY date DESC",
            (callback.from_user.id,)
        ).fetchall()
    
    if not rows:
        await msg.edit_text("📭 ထုတ်ယူရန် အချက်အလက်မရှိပါ။", reply_markup=expense_menu())
        await callback.answer()
        return
    
    transactions = []
    for row in rows:
        transactions.append({
            'date': row['date'],
            'type': row['type'],
            'amount': float(row['amount']),
            'category': row['category']
        })
    
    # ========== EXPORT TO GOOGLE SHEETS (NOT EXCEL) ==========
    sheet_url = export_to_google_sheets(transactions, callback.from_user.id)
    
    if sheet_url:
        await msg.delete()
        await callback.message.answer(
            f"✅ သင့်ငွေစာရင်းကို Google Sheets သို့ ထုတ်ယူပြီးပါပြီ။\n\n"
            f"📊 ဒေတာများကို ဤနေရာတွင် ကြည့်ရှုနိုင်ပါသည်:\n"
            f"🔗 {sheet_url}\n\n"
            f"💡 Sheet ကို သင့် Google Drive တွင် သိမ်းဆည်းထားပါသည်။",
            reply_markup=expense_menu()
        )
    else:
        await msg.edit_text(
            "❌ Google Sheets သို့ ထုတ်ယူရာတွင် အမှားရှိပါသည်။\n\n"
            "ကျေးဇူးပြု၍ စစ်ဆေးရန်:\n"
            "1. `credentials.json` ဖိုင် ရှိမရှိ\n"
            "2. Service Account Email ကို Sheet သို့ Share ထားခြင်း\n"
            "3. SHEET_ID မှန်ကန်ခြင်း",
            reply_markup=expense_menu()
        )
    
    await callback.answer()

@router.callback_query(F.data == "exp_budget")
async def budget_menu(callback: CallbackQuery, bot: Bot):
    is_member, _ = await check_channel_membership(callback.from_user.id, bot)
    if not is_member:
        await ask_to_join_channel(callback.message, bot)
        await callback.answer()
        return
    
    with get_db() as db:
        budgets = db.execute("SELECT period, amount FROM budgets WHERE user_id = ?", (callback.from_user.id,)).fetchall()
    text = "🎯 <b>Budget Reminder</b>\n\n"
    for b in budgets:
        text += f"• {b['period'].capitalize()}: <code>{b['amount']:,.0f} MMK</code>\n"
    if not budgets:
        text += "ဘတ်ဂျက်သတ်မှတ်ထားခြင်း မရှိသေးပါ။\n"
    text += "\nဘတ်ဂျက်သစ်သတ်မှတ်ရန် အောက်ပါခလုတ်များကို နှိပ်ပါ။"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=budget_period_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("budget_"))
async def set_budget_amount(callback: CallbackQuery, state: FSMContext, bot: Bot):
    is_member, _ = await check_channel_membership(callback.from_user.id, bot)
    if not is_member:
        await ask_to_join_channel(callback.message, bot)
        await callback.answer()
        return
    
    period = callback.data.split("_")[1]
    await state.set_state(BudgetSetup.waiting_for_amount)
    await state.update_data(period=period)
    await callback.message.edit_text(f"📝 {period.capitalize()} ဘတ်ဂျက်ပမာဏကို ဂဏန်းသက်သက်ဖြင့် ထည့်ပါ။\n\nဥပမာ - {500000 if period == 'weekly' else 2000000}", reply_markup=cancel_keyboard())
    await callback.answer()

@router.message(BudgetSetup.waiting_for_amount)
async def process_budget_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            await message.answer("ကျေးဇူးပြု၍ အပေါင်းဂဏန်း ထည့်ပါ။", reply_markup=cancel_keyboard())
            return
        data = await state.get_data()
        period = data['period']
        today = datetime.now().strftime("%Y-%m-%d")
        with get_db() as db:
            db.execute("DELETE FROM budgets WHERE user_id = ? AND period = ?", (message.from_user.id, period))
            db.execute("INSERT INTO budgets (user_id, period, amount, start_date) VALUES (?, ?, ?, ?)", (message.from_user.id, period, amount, today))
        await message.answer(f"✅ {period.capitalize()} ဘတ်ဂျက် <code>{amount:,.0f} MMK</code> သတ်မှတ်ပြီးပါပြီ။\n\nသတ်မှတ်ထားသော ဘတ်ဂျက်၏ 70% ကျော်ပါက အကြောင်းကြားပါမည်။", parse_mode="HTML", reply_markup=expense_menu())
        await state.clear()
    except ValueError:
        await message.answer("ကျေးဇူးပြု၍ ဂဏန်းသက်သက်သာ ထည့်ပါ။", reply_markup=cancel_keyboard())

# ========== CURRENCY EXCHANGE ==========
@router.callback_query(F.data == "menu_currency")
async def currency_menu(callback: CallbackQuery, bot: Bot):
    is_member, _ = await check_channel_membership(callback.from_user.id, bot)
    if not is_member:
        await ask_to_join_channel(callback.message, bot)
        await callback.answer()
        return
    
    msg = await callback.message.edit_text("⏳ ငွေလဲနှုန်းများ ရယူနေပါသည်...")
    rates = await get_live_exchange_rates()
    with get_db() as db:
        user = db.execute("SELECT notify_rate FROM users WHERE user_id = ?", (callback.from_user.id,)).fetchone()
        notify_on = user['notify_rate'] if user else 0
    text = "💱 <b>Live ငွေလဲနှုန်းများ (MMK)</b>\n\n"
    for curr, rate in rates.items():
        text += f"• 1 {curr} = <code>{rate:,.0f} MMK</code>\n"
    text += "\n📌 ငွေကြေးတစ်ခုချင်းစီကို နှိပ်၍ copy လုပ်နိုင်ပါသည်။\n"
    text += f"\n🔔 Rate Alert: {'ON' if notify_on else 'OFF'}\n"
    await msg.edit_text(text, parse_mode="HTML", reply_markup=currency_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("currency_"))
async def show_currency_rate(callback: CallbackQuery):
    currency = callback.data.split("_")[1]
    if currency in ['alert']:
        return
    rates = await get_live_exchange_rates()
    rate = rates.get(currency, 0)
    await callback.answer(f"💱 1 {currency} = {rate:,.0f} MMK", show_alert=True)

@router.callback_query(F.data == "check_rates_now")
async def check_rates_now(callback: CallbackQuery, bot: Bot):
    is_member, _ = await check_channel_membership(callback.from_user.id, bot)
    if not is_member:
        await ask_to_join_channel(callback.message, bot)
        await callback.answer()
        return
    
    msg = await callback.message.edit_text("⏳ ငွေလဲနှုန်းများ စစ်ဆေးနေပါသည်...")
    try:
        current_rates = await get_live_exchange_rates()
        user_id = callback.from_user.id
        with get_db() as db:
            notify = db.execute("SELECT notify_rate FROM users WHERE user_id = ?", (user_id,)).fetchone()
            notify_on = notify['notify_rate'] if notify else 0
        global previous_rates
        old_rates = previous_rates.get(user_id, {})
        changes = []
        for currency, new_rate in current_rates.items():
            old_rate = old_rates.get(currency, new_rate)
            if old_rate > 0:
                percent_change = abs((new_rate - old_rate) / old_rate * 100)
                if percent_change >= 2:
                    changes.append(f"• {currency}: {old_rate:,.0f} → {new_rate:,.0f} ({percent_change:.1f}%)")
        previous_rates[user_id] = current_rates
        text = "💱 <b>လက်ရှိငွေလဲနှုန်းများ (MMK)</b>\n\n"
        for curr, rate in current_rates.items():
            text += f"• 1 {curr} = <code>{rate:,.0f} MMK</code>\n"
        if changes:
            text += "\n🔔 <b>သိသိသာသာပြောင်းလဲမှုများ:</b>\n" + "\n".join(changes)
        else:
            text += "\n✅ သိသိသာသာ ပြောင်းလဲမှု မရှိပါ။"
        text += f"\n\n🔔 Rate Alert: {'ON' if notify_on else 'OFF'}"
        await msg.edit_text(text, parse_mode="HTML", reply_markup=currency_menu_keyboard())
    except Exception as e:
        await msg.edit_text("❌ ငွေလဲနှုန်းများ စစ်ဆေးရာတွင် အမှားရှိပါသည်။", reply_markup=currency_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "toggle_rate_alert")
async def toggle_rate_alert(callback: CallbackQuery, bot: Bot):
    is_member, _ = await check_channel_membership(callback.from_user.id, bot)
    if not is_member:
        await ask_to_join_channel(callback.message, bot)
        await callback.answer()
        return
    
    with get_db() as db:
        current = db.execute("SELECT notify_rate FROM users WHERE user_id = ?", (callback.from_user.id,)).fetchone()
        new_value = 0 if current and current['notify_rate'] else 1
        db.execute("UPDATE users SET notify_rate = ? WHERE user_id = ?", (new_value, callback.from_user.id))
    status = "ON" if new_value else "OFF"
    await callback.answer(f"✅ Rate Alert {status}", show_alert=True)
    await currency_menu(callback, bot)

# ========== CRYPTO CURRENCY ==========
@router.callback_query(F.data == "menu_crypto")
async def crypto_menu(callback: CallbackQuery, bot: Bot):
    is_member, _ = await check_channel_membership(callback.from_user.id, bot)
    if not is_member:
        await ask_to_join_channel(callback.message, bot)
        await callback.answer()
        return
    
    await callback.message.edit_text("₿ <b>Crypto Currency</b>\n\nအောက်ပါရွေးချယ်စရာများထဲမှ ရွေးချယ်ပါ။", parse_mode="HTML", reply_markup=crypto_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "crypto_prices")
async def show_crypto_prices(callback: CallbackQuery, bot: Bot):
    is_member, _ = await check_channel_membership(callback.from_user.id, bot)
    if not is_member:
        await ask_to_join_channel(callback.message, bot)
        await callback.answer()
        return
    
    msg = await callback.message.edit_text("⏳ Crypto စျေးနှုန်းများ ရယူနေပါသည်...")
    cryptos = await get_live_crypto_prices()
    text = "₿ <b>Live Crypto စျေးနှုန်းများ</b>\n\n"
    for crypto in cryptos:
        mmk_price = crypto['price'] * 3500
        text += f"• {crypto['symbol']} - {crypto['name']}\n"
        text += f"  💰 <code>${crypto['price']:,.2f} USD</code>\n"
        text += f"  📊 ≈ <code>{mmk_price:,.0f} MMK</code>\n\n"
    await msg.edit_text(text, parse_mode="HTML", reply_markup=crypto_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "crypto_news")
async def show_crypto_news(callback: CallbackQuery, bot: Bot):
    is_member, _ = await check_channel_membership(callback.from_user.id, bot)
    if not is_member:
        await ask_to_join_channel(callback.message, bot)
        await callback.answer()
        return
    
    msg = await callback.message.edit_text("⏳ Crypto သတင်းများ ရယူနေပါသည်...")
    news_list = await get_live_crypto_news(limit=5)
    text = "📰 <b>နောက်ဆုံး Crypto သတင်းများ</b>\n\n"
    for i, news in enumerate(news_list, 1):
        title = await translate_to_myanmar(news['title'])
        text += f"{i}. <b>{title}</b>\n"
        text += f"   📌 {news['source']}\n"
        text += f"   🔗 <a href='{news['url']}'>အသေးစိတ်ဖတ်ရန်</a>\n\n"
    await msg.edit_text(text, parse_mode="HTML", reply_markup=crypto_menu_keyboard(), disable_web_page_preview=True)
    await callback.answer()

# ========== TUTORIAL ==========
@router.callback_query(F.data == "menu_tutorial")
async def tutorial_menu(callback: CallbackQuery, bot: Bot):
    is_member, _ = await check_channel_membership(callback.from_user.id, bot)
    if not is_member:
        await ask_to_join_channel(callback.message, bot)
        await callback.answer()
        return
    
    await callback.message.edit_text("📘 <b>Crypto Tutorials</b>\n\nအောက်ပါ YouTube Channel များမှ သင်ယူနိုင်ပါသည်။", parse_mode="HTML", reply_markup=tutorial_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "tutorial_list")
async def show_tutorials(callback: CallbackQuery, bot: Bot):
    is_member, _ = await check_channel_membership(callback.from_user.id, bot)
    if not is_member:
        await ask_to_join_channel(callback.message, bot)
        await callback.answer()
        return
    
    text = "📘 <b>Myanmar Crypto YouTube Channels</b>\n\n"
    for i, tutorial in enumerate(TUTORIALS, 1):
        text += f"{i}. <b>{tutorial['name']}</b>\n   📺 {tutorial['channel']}\n   💡 {tutorial['reason']}\n   🔗 <a href='{tutorial['url']}'>ကြည့်ရှုရန်</a>\n\n"
    buttons = [[InlineKeyboardButton(text=f"▶️ {t['name']}", url=t['url'])] for t in TUTORIALS[:5]]
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="menu_tutorial")])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), disable_web_page_preview=True)
    await callback.answer()

# ========== CANCEL & BACK ==========
@router.callback_query(F.data == "cancel_input")
async def cancel_input(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ လုပ်ဆောင်မှု ဖျက်သိမ်းပြီးပါပြီ။", reply_markup=expense_menu())
    await callback.answer()

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext, bot: Bot):
    is_member, _ = await check_channel_membership(callback.from_user.id, bot)
    if not is_member:
        await ask_to_join_channel(callback.message, bot)
        await callback.answer()
        return
    
    await state.clear()
    await callback.message.edit_text("🇲🇲 Business Bot ပင်မစာမျက်နှာသို့ ပြန်လည်ရောက်ရှိပါပြီ။", reply_markup=main_menu())
    await callback.answer()