import sqlite3

def get_db():
    """
    Database connection ကို ယူပါ။
    """
    conn = sqlite3.connect("finance.db")
    # Row တွေကို dictionary လိုမျိုး ခေါ်လို့ရအောင် လုပ်ပေးပါတယ်
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Database table တွေကို (မရှိသေးရင်) တည်ဆောက်ပါမယ်။
    """
    conn = get_db()
    
    # User table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    
    # Categories table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL
    )
    """)
    
    # Transactions table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        note TEXT,
        date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    conn.commit()
    conn.close()

# ဒီ file ကို တိုက်ရိုက် run ရင် database ကို initialize လုပ်မယ်
if __name__ == "__main__":
    init_db()
    print("Database 'finance.db' ကို အောင်မြင်စွာ တည်ဆောက်ပြီးပါပြီ။")