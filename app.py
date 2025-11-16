from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
from datetime import datetime
import sqlite3 # error handling အတွက် ထည့်ထားနိုင်သည်

app = Flask(__name__)
# Session (login) အတွက် secret key တစ်ခု လိုအပ်ပါသည်
app.secret_key = "your_super_secret_key_change_this"

# --- LOGIN SYSTEM ---

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Login page - user ဝင်ခြင်း
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Register page - user အသစ် ဖွင့်ခြင်း (PDF ထဲမပါ၊ ထပ်တိုး)
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        # Password ကို hash လုပ်ပါ (လုံခြုံရေးအတွက်)
        hashed_password = generate_password_hash(password)
        
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )
            db.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            # Username က unique မဖြစ်ရင် (ရှိပြီးသားဖြစ်ရင်)
            return render_template("register.html", error="Username (အမည်) က ရှိပြီးသား ဖြစ်နေပါသည်။")
            
    return render_template("register.html")


@app.route("/logout")
def logout():
    """
    User ထွက်ခြင်း
    """
    session.clear()
    return redirect(url_for("login"))

# --- CORE APP ---

def is_logged_in():
    """
    Login ဝင်ထားမထား စစ်ဆေးပေးသည်
    """
    return "user_id" in session

@app.route("/")
def index():
    """
    Home page - စာရင်းအားလုံးကို ပြသသည်
    """
    if not is_logged_in():
        return redirect(url_for("login"))
    
    db = get_db()
    # လက်ရှိ user ရဲ့ စာရင်းတွေကို နေ့စွဲအလိုက် အသစ်ဆုံးကနေ ပြမယ်
    records = db.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC",
        (session["user_id"],)
    ).fetchall()
    
    # Balance တွက်ချက်ခြင်း
    income_row = db.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'income'", (session["user_id"],)).fetchone()
    expense_row = db.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'expense'", (session["user_id"],)).fetchone()
    
    total_income = income_row[0] or 0
    total_expense = expense_row[0] or 0
    balance = total_income - total_expense
    
    return render_template("index.html", 
                           records=records, 
                           balance=balance, 
                           total_income=total_income, 
                           total_expense=total_expense)

@app.route("/add", methods=["GET", "POST"])
def add():
    """
    စာရင်းအသစ် ထည့်သွင်းခြင်း
    """
    if not is_logged_in():
        return redirect(url_for("login"))
    
    db = get_db()
    
    if request.method == "POST":
        trans_type = request.form["type"]
        amount = float(request.form["amount"])
        category = request.form["category"]
        note = request.form["note"]
        # နေ့စွဲကို default ယနေ့ရက်စွဲ ထားပေးမယ်
        date = request.form["date"] or datetime.now().strftime("%Y-%m-%d")
        
        db.execute(
            "INSERT INTO transactions (user_id, type, amount, category, note, date) VALUES (?, ?, ?, ?, ?, ?)",
            (session["user_id"], trans_type, amount, category, note, date)
        )
        db.commit()
        return redirect(url_for("index"))
    
    # Categories တွေကို database ကနေ ယူမယ်
    categories = db.execute("SELECT * FROM categories ORDER BY type, name").fetchall()
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("add.html", categories=categories, today=today)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    """
    စာရင်းကို ပြင်ဆင်ခြင်း
    """
    if not is_logged_in():
        return redirect(url_for("login"))
    
    db = get_db()
    # မှန်ကန်တဲ့ user ရဲ့ transaction ဟုတ် မဟုတ် စစ်ဆေးသင့်ပါတယ် (လုံခြုံရေး)
    record = db.execute(
        "SELECT * FROM transactions WHERE id = ? AND user_id = ?", 
        (id, session["user_id"])
    ).fetchone()
    
    if not record:
        # Transaction မရှိရင် (သို့) user မပိုင်ရင် home ကို ပြန်ပို့
        return redirect(url_for("index"))

    if request.method == "POST":
        trans_type = request.form["type"]
        amount = float(request.form["amount"])
        category = request.form["category"]
        note = request.form["note"]
        date = request.form["date"]
        
        db.execute(
            "UPDATE transactions SET type = ?, amount = ?, category = ?, note = ?, date = ? WHERE id = ?",
            (trans_type, amount, category, note, date, id)
        )
        db.commit()
        return redirect(url_for("index"))
        
    categories = db.execute("SELECT * FROM categories ORDER BY type, name").fetchall()
    return render_template("edit.html", record=record, categories=categories)

@app.route("/delete/<int:id>")
def delete(id):
    """
    စာရင်းကို ဖျက်ခြင်း
    """
    if not is_logged_in():
        return redirect(url_for("login"))
    
    db = get_db()
    # User ပိုင်ဆိုင်သော transaction ကိုသာ ဖျက်ခွင့်ပြု
    db.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (id, session["user_id"]))
    db.commit()
    return redirect(url_for("index"))

# --- CATEGORY MANAGEMENT ---

@app.route("/categories", methods=["GET", "POST"])
def categories():
    """
    Category များကို ထည့်ခြင်း/ကြည့်ခြင်း
    """
    if not is_logged_in():
        return redirect(url_for("login"))
    
    db = get_db()
    
    if request.method == "POST":
        name = request.form["name"]
        trans_type = request.form["type"]
        if name: # name မထည့်ထားရင် မသိမ်းပါ
            db.execute("INSERT INTO categories (name, type) VALUES (?, ?)", (name, trans_type))
            db.commit()
        return redirect(url_for("categories"))
        
    cats = db.execute("SELECT * FROM categories ORDER BY type, name").fetchall()
    return render_template("categories.html", categories=cats)

@app.route("/delete_category/<int:id>")
def delete_category(id):
    """
    Category ကို ဖျက်ခြင်း (ထပ်တိုး)
    """
    if not is_logged_in():
        return redirect(url_for("login"))
    
    db = get_db()
    db.execute("DELETE FROM categories WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("categories"))

# --- SUMMARY & CHARTS ---

@app.route("/summary")
def summary():
    """
    အနှစ်ချုပ် နှင့် Chart များ
    """
    if not is_logged_in():
        return redirect(url_for("login"))
        
    db = get_db()
    
    # Total Income/Expense
    income_row = db.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'income'", (session["user_id"],)).fetchone()
    expense_row = db.execute("SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'expense'", (session["user_id"],)).fetchone()
    
    total_income = income_row[0] or 0
    total_expense = expense_row[0] or 0
    balance = total_income - total_expense

    # Expense by Category
    expense_by_cat = db.execute("""
        SELECT category, SUM(amount) as total 
        FROM transactions 
        WHERE user_id = ? AND type = 'expense' 
        GROUP BY category 
        ORDER BY total DESC
    """, (session["user_id"],)).fetchall()

    # Chart.js အတွက် data ပြင်ဆင်ခြင်း
    chart_labels = [row['category'] for row in expense_by_cat]
    chart_data = [row['total'] for row in expense_by_cat]

    return render_template("summary.html", 
                           total_income=total_income, 
                           total_expense=total_expense,
                           balance=balance,
                           expense_by_cat=expense_by_cat,
                           chart_labels=chart_labels,
                           chart_data=chart_data)

# --- RUN APP ---
if __name__ == "__main__":
    app.run(debug=True, port=5000)