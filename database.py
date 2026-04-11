import sqlite3
from datetime import datetime
from contextlib import contextmanager
import os
import tempfile

# Use temporary directory for cloud platforms
DB_PATH = os.path.join(tempfile.gettempdir(), "finance_bot.db")

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    with get_db() as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                currency TEXT DEFAULT 'MMK',
                notify_rate INTEGER DEFAULT 0,
                budget_weekly REAL DEFAULT 0,
                budget_monthly REAL DEFAULT 0
            )
        ''')
        
        db.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT CHECK(type IN ('income', 'expense')),
                amount REAL,
                category TEXT,
                date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        db.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                period TEXT CHECK(period IN ('weekly', 'monthly')),
                amount REAL,
                start_date TEXT,
                last_notified REAL DEFAULT 0
            )
        ''')
        
        db.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_date ON transactions(user_id, date)
        ''')
        
        print(f"✅ Database initialized at: {DB_PATH}")

def get_dashboard(user_id: int):
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db() as db:
        result = db.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND type = 'income' AND date = ?",
            (user_id, today)
        ).fetchone()
        today_income = result['total'] if result else 0
        
        result = db.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND type = 'expense' AND date = ?",
            (user_id, today)
        ).fetchone()
        today_expense = result['total'] if result else 0
        
        result = db.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND type = 'income'",
            (user_id,)
        ).fetchone()
        total_income = result['total'] if result else 0
        
        result = db.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND type = 'expense'",
            (user_id,)
        ).fetchone()
        total_expense = result['total'] if result else 0
        
    balance = total_income - total_expense
    today_balance = today_income - today_expense
    
    return {
        'today_income': today_income,
        'today_expense': today_expense,
        'today_balance': today_balance,
        'total_income': total_income,
        'total_expense': total_expense,
        'total_balance': balance
    }