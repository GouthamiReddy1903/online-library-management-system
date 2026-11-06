import os
import sqlite3
from datetime import date, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-for-production")
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "data", "library.db"))
FINE_PER_DAY = float(os.environ.get("FINE_PER_DAY", "5"))
LOAN_DAYS = int(os.environ.get("LOAN_DAYS", "14"))

def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student'
        );
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE,
            total_copies INTEGER NOT NULL DEFAULT 1,
            available_copies INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES users(id),
            book_id INTEGER NOT NULL REFERENCES books(id),
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            fine REAL NOT NULL DEFAULT 0
        );
        """)
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@library.com")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        existing = db.execute("SELECT id FROM users WHERE email=?", (admin_email,)).fetchone()
        if not existing:
            db.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
                       ("Library Admin", admin_email, generate_password_hash(admin_password), "admin"))
        db.commit()

def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in first.", "warning")
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("You do not have permission to access that page.", "danger")
                return redirect(url_for("index"))
            return view(*args, **kwargs)
        return wrapped
    return decorator

@app.route("/")
def index():
    db = get_db()
    query = request.args.get("q", "").strip()
    if query:
        books = db.execute("SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ? ORDER BY title",
                           (f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()
    else:
        books = db.execute("SELECT * FROM books ORDER BY title").fetchall()
    return render_template("index.html", books=books, query=query)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name, email = request.form.get("name", "").strip(), request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Enter your name, email and a password of at least 6 characters.", "danger")
        else:
            try:
                db = get_db()
                db.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
                           (name, email, generate_password_hash(password), "student"))
                db.commit()
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("That email address is already registered.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            session.clear()
            session.update(user_id=user["id"], name=user["name"], role=user["role"])
            flash(f"Welcome, {user['name']}!", "success")
            return redirect(url_for("index"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

@app.route("/admin/books/add", methods=["GET", "POST"])
@login_required("admin")
def add_book():
    if request.method == "POST":
        title, author = request.form.get("title", "").strip(), request.form.get("author", "").strip()
        isbn = request.form.get("isbn", "").strip() or None
        try:
            copies = max(1, int(request.form.get("copies", "1")))
            if not title or not author:
                raise ValueError()
            db = get_db()
            db.execute("INSERT INTO books(title,author,isbn,total_copies,available_copies) VALUES(?,?,?,?,?)",
                       (title, author, isbn, copies, copies))
            db.commit()
            flash("Book added successfully.", "success")
            return redirect(url_for("index"))
        except (ValueError, sqlite3.IntegrityError):
            flash("Check the book details. ISBN must be unique and copies must be a positive number.", "danger")
    return render_template("book_form.html", book=None)

@app.route("/admin/books/<int:book_id>/edit", methods=["GET", "POST"])
@login_required("admin")
def edit_book(book_id):
    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    if not book:
        flash("Book not found.", "danger")
        return redirect(url_for("index"))
    if request.method == "POST":
        title, author = request.form.get("title", "").strip(), request.form.get("author", "").strip()
        isbn = request.form.get("isbn", "").strip() or None
        try:
            total = max(1, int(request.form.get("copies", "1")))
            borrowed = book["total_copies"] - book["available_copies"]
            if not title or not author or total < borrowed:
                raise ValueError()
            db.execute("""UPDATE books SET title=?,author=?,isbn=?,total_copies=?,available_copies=? WHERE id=?""",
                       (title, author, isbn, total, total-borrowed, book_id))
            db.commit()
            flash("Book details updated.", "success")
            return redirect(url_for("index"))
        except (ValueError, sqlite3.IntegrityError):
            flash("Invalid details. Copies cannot be fewer than currently issued copies; ISBN must be unique.", "danger")
    return render_template("book_form.html", book=book)

@app.route("/admin/books/<int:book_id>/delete", methods=["POST"])
@login_required("admin")
def delete_book(book_id):
    db = get_db()
    active = db.execute("SELECT COUNT(*) AS n FROM loans WHERE book_id=? AND return_date IS NULL", (book_id,)).fetchone()["n"]
    if active:
        flash("This book has active issues and cannot be deleted.", "danger")
    else:
        db.execute("DELETE FROM books WHERE id=?", (book_id,))
        db.commit()
        flash("Book deleted.", "success")
    return redirect(url_for("index"))

@app.route("/issue/<int:book_id>", methods=["POST"])
@login_required()
def issue_book(book_id):
    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    if not book:
        flash("Book not found.", "danger")
    elif book["available_copies"] < 1:
        flash("No copies are currently available.", "warning")
    else:
        today = date.today()
        due = date.fromordinal(today.toordinal() + LOAN_DAYS)
        db.execute("INSERT INTO loans(student_id,book_id,issue_date,due_date) VALUES(?,?,?,?)",
                   (session["user_id"], book_id, today.isoformat(), due.isoformat()))
        db.execute("UPDATE books SET available_copies=available_copies-1 WHERE id=?", (book_id,))
        db.commit()
        flash(f"Book issued. Return by {due.isoformat()}.", "success")
    return redirect(url_for("index"))

@app.route("/my-loans")
@login_required()
def my_loans():
    loans = get_db().execute("""
        SELECT loans.*, books.title, books.author
        FROM loans JOIN books ON books.id=loans.book_id
        WHERE loans.student_id=? ORDER BY loans.issue_date DESC
    """, (session["user_id"],)).fetchall()
    today = date.today()
    loan_rows = []
    for loan in loans:
        item = dict(loan)
        if not item["return_date"]:
            overdue = max(0, (today - date.fromisoformat(item["due_date"])).days)
            item["current_fine"] = round(overdue * FINE_PER_DAY, 2)
        else:
            item["current_fine"] = item["fine"]
        loan_rows.append(item)
    return render_template("loans.html", loans=loan_rows)

@app.route("/admin/loans")
@login_required("admin")
def all_loans():
    loans = get_db().execute("""
        SELECT loans.*, books.title, users.name AS student_name, users.email
        FROM loans JOIN books ON books.id=loans.book_id JOIN users ON users.id=loans.student_id
        ORDER BY loans.issue_date DESC
    """).fetchall()
    today = date.today()
    rows = []
    for loan in loans:
        item = dict(loan)
        item["current_fine"] = item["fine"] if item["return_date"] else round(max(0, (today-date.fromisoformat(item["due_date"])).days)*FINE_PER_DAY, 2)
        rows.append(item)
    return render_template("admin_loans.html", loans=rows)

@app.route("/return/<int:loan_id>", methods=["POST"])
@login_required()
def return_book(loan_id):
    db = get_db()
    loan = db.execute("SELECT * FROM loans WHERE id=?", (loan_id,)).fetchone()
    if not loan or (session.get("role") != "admin" and loan["student_id"] != session["user_id"]):
        flash("Loan not found or access denied.", "danger")
    elif loan["return_date"]:
        flash("This book has already been returned.", "info")
    else:
        returned = date.today()
        overdue = max(0, (returned - date.fromisoformat(loan["due_date"])).days)
        fine = round(overdue * FINE_PER_DAY, 2)
        db.execute("UPDATE loans SET return_date=?,fine=? WHERE id=?", (returned.isoformat(), fine, loan_id))
        db.execute("UPDATE books SET available_copies=available_copies+1 WHERE id=?", (loan["book_id"],))
        db.commit()
        flash(f"Book returned. Overdue fine: ₹{fine:.2f}.", "success")
    return redirect(url_for("all_loans" if session.get("role") == "admin" else "my_loans"))

@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
