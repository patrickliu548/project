import os
import secrets
import sqlite3

from flask import Flask, render_template, redirect, request, g
from flask_login import LoginManager, login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect("database.db")
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

class User:
    def __init__(self, id, name, email, password_hash, created_at):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()

    if row is None:
        return None
    
    user = User(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        password_hash=row["password_hash"],
        created_at=row["created_at"]
    )
    return user

def apology(message, code=400):
    """Render message as an apology to user."""

    return render_template("apology.html", top=code, bottom=message), code

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")
        if not email or not password:
            return apology("must provide email and password", 403)
        
        db = get_db()
        row = db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        if row is None or not check_password_hash(row["password_hash"], password):
            return apology("invalid email and/or password", 403)
        
        user = User(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            password_hash=row["password_hash"],
            created_at=row["created_at"]
        )
        login_user(user, remember=bool(request.form.get("remember")))

        return redirect("/")
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    logout_user()
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        name = request.form.get("name")
        if not name:
            return apology("must provide name", 400)
        email = request.form.get("email")
        if not email:
            return apology("must provide email", 400)
        password = request.form.get("password")
        if not password:
            return apology("must provide password", 400)
        confirmation = request.form.get("confirmation")
        if password != confirmation:
            return apology("passwords must match", 400)
        
        pwhash = generate_password_hash(password)

        try: 
            db = get_db()
            db.execute(
                """
                INSERT INTO users (
                    name, email, password_hash) VALUES (?, ?, ?)
                """,
                (name, email, pwhash)
            )
            db.commit()
        except sqlite3.IntegrityError:
            return apology("email already registered", 400)
        
        return redirect("/login")
    
    return render_template("register.html")