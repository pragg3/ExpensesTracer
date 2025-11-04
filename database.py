import sqlite3

DB_NAME = "expenses.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Monthly balances
    c.execute("""
        CREATE TABLE IF NOT EXISTS balance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT UNIQUE,
            total_money REAL,
            currency TEXT DEFAULT 'EUR'
        )
    """)

    # Expenses
    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            amount REAL,
            date TEXT,
            month TEXT
        )
    """)

    conn.commit()
    conn.close()



def get_months():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT month FROM balance ORDER BY month DESC")
    months = [row["month"] for row in c.fetchall()]
    conn.close()
    return months


def add_month(month, currency="EUR"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM balance WHERE month = ?", (month,))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO balance (month, total_money, currency) VALUES (?, ?, ?)", (month, 0, currency))
        conn.commit()
    conn.close()


def remove_month(month):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE month = ?", (month,))
    c.execute("DELETE FROM balance WHERE month = ?", (month,))
    conn.commit()
    conn.close()




def get_balance(month):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT total_money, currency FROM balance WHERE month = ? LIMIT 1", (month,))
    result = c.fetchone()
    conn.close()
    return (result["total_money"], result["currency"]) if result else (0, "EUR")


def update_balance(month, amount, currency):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE balance SET total_money = ?, currency = ? WHERE month = ?", (amount, currency, month))
    conn.commit()
    conn.close()



def add_expense(description, amount, date, month):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO expenses (description, amount, date, month) VALUES (?, ?, ?, ?)",
        (description, amount, date, month),
    )
    conn.commit()
    conn.close()


def get_expenses(month):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM expenses WHERE month = ? ORDER BY date", (month,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_expense(expense_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()


def edit_expense(expense_id, new_desc, new_amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE expenses SET description = ?, amount = ? WHERE id = ?", (new_desc, new_amount, expense_id))
    conn.commit()
    conn.close()
