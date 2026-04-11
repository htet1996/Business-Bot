from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Expense Tracker", callback_data="menu_expense"),
        InlineKeyboardButton(text="💱 Currency Exchange", callback_data="menu_currency")
    )
    builder.row(
        InlineKeyboardButton(text="₿ Crypto Currency", callback_data="menu_crypto"),
        InlineKeyboardButton(text="📘 Tutorial", callback_data="menu_tutorial")
    )
    return builder.as_markup()

def expense_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Add Income", callback_data="exp_income"),
        InlineKeyboardButton(text="➖ Add Expense", callback_data="exp_expense")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Dashboard", callback_data="exp_dashboard"),
        InlineKeyboardButton(text="📁 Export Excel", callback_data="exp_excel")
    )
    builder.row(
        InlineKeyboardButton(text="🎯 Budget Reminder", callback_data="exp_budget"),
        InlineKeyboardButton(text="🔙 Back", callback_data="back_main")
    )
    return builder.as_markup()

def cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_input")]
    ])

def budget_period_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 Weekly Budget", callback_data="budget_weekly"),
        InlineKeyboardButton(text="📆 Monthly Budget", callback_data="budget_monthly")
    )
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="menu_expense"))
    return builder.as_markup()

def currency_menu_keyboard():
    currencies = ['USD', 'SGD', 'THB', 'JPY', 'CNY', 'KRW', 'AED', 'EUR']
    builder = InlineKeyboardBuilder()
    for curr in currencies:
        builder.add(InlineKeyboardButton(text=curr, callback_data=f"currency_{curr}"))
    builder.adjust(4)
    builder.row(InlineKeyboardButton(text="🔄 Refresh", callback_data="check_rates_now"))
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="back_main"))
    return builder.as_markup()

def crypto_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 View Prices", callback_data="crypto_prices"),
        InlineKeyboardButton(text="📰 Crypto News", callback_data="crypto_news")
    )
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="back_main"))
    return builder.as_markup()

def tutorial_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🇲🇲 Myanmar Crypto Tutorials", callback_data="tutorial_list"))
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="back_main"))
    return builder.as_markup()