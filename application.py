import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from functools import wraps
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")

# Flask decorator to ensure that the user is logged in
def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please login first")
            return redirect("/login")
        else:
            return f(*args, **kwargs)
    return decorated_function

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1:
            flash("Unregistered username")
            return redirect(request.url)
        elif not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid password")
            return redirect(request.url)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Select row in database for the inputted username
        row = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username") )

        # Check the validity of the username
        if len(row) != 0:
            flash("Username taken")
            return redirect(request.url)

        # Check the validity of the password
        elif request.form.get("confirmation") != request.form.get("password"):
            flash("Passwords do not match")
            return redirect(request.url)

        # Register user into the database
        db.execute("INSERT INTO users (username, hash) VALUES(:username, :password)",
        username = request.form.get("username"), password = generate_password_hash(request.form.get("password")) )

        # Redirect users to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/")
@login_required
def home():
    food = 0
    trans = 0
    house = 0
    ut = 0
    insurance = 0
    rec = 0
    invest = 0
    mis = 0
    balance = 0

    rows = db.execute("SELECT * FROM history WHERE id=:username", username=session["user_id"])
    for row in rows:
        if row["type"] == "Earnings":
            balance += float(row["amount"])
        else:
            balance -= float(row["amount"])

        if row["type"] == "Food":
            food += float(row["amount"])
        elif row["type"] == "Transportation":
            trans += float(row["amount"])
        elif row["type"] == "Housing":
            house += float(row["amount"])
        elif row["type"] == "Utilities":
            ut += float(row["amount"])
        elif row["type"] == "Insurance":
            insurance += float(row["amount"])
        elif row["type"] == "Recreation":
            rec += float(row["amount"])
        elif row["type"] == "Investment":
            invest += float(row["amount"])
        elif row["type"] == "Micellaneous":
            mis += float(row["amount"])

    return render_template ("home.html", food=food, trans=trans, house=house, ut=ut, rec=rec, insurance=insurance, invest=invest, mis=mis, balance=balance)

@app.route("/expenses", methods=["GET","POST"])
@login_required
def expenses():
    if request.method == "POST":
        amount = request.form.get("value")
        select = request.form.get("type")
        date = request.form.get("date")
        note = request.form.get("note")
        db.execute("INSERT INTO history (id,amount,type,date,note) VALUES(:username,:amount,:expense_type,:date,:note)", username=session["user_id"], amount=amount, expense_type=select, date=date, note=note)
        return redirect("/")
    else:
        return render_template ("expenses.html")

@app.route("/earning", methods=["GET","POST"])
@login_required
def earning():
    if request.method == "POST":
        amount = request.form.get("value")
        date = request.form.get("date")
        note = request.form.get("note")
        db.execute("INSERT INTO history (id,amount,type,date,note) VALUES(:username,:amount,:expense_type,:date,:note)", username=session["user_id"], amount=amount, expense_type="Earnings", date=date, note=note)
        return redirect("/")
    else:
        return render_template ("earning.html")

@app.route("/history", methods=["GET","POST"])
@login_required
def history():
    amounts=[]
    types=[]
    dates=[]
    notes=[]
    colours=[]

    if request.method == "GET":
        rows = db.execute("SELECT * FROM history WHERE id=:username ORDER BY date DESC", username=session["user_id"])

        for row in rows:
            amounts.append(row["amount"])
            types.append(row["type"])
            if row["type"] == "Earnings":
                colours.append("table-success")
            else:
                colours.append("table-warning")
            dates.append(row["date"])
            notes.append(row["note"])

        length = len(amounts)
        return render_template ("history.html", amounts=amounts, types=types, dates=dates, notes=notes, length=length, colours=colours)

    else:
        search = request.form.get("search").lower().capitalize()
        rows = db.execute("SELECT * FROM history WHERE id=:username AND type=:search_type ORDER BY date DESC", username=session["user_id"], search_type=search)

        if len(rows) == 0:
            flash("Invalid type")
            return redirect("/history")

        for row in rows:
            amounts.append(row["amount"])
            types.append(row["type"])
            if row["type"] == "Earnings":
                colours.append("table-success")
            else:
                colours.append("table-warning")
            dates.append(row["date"])
            notes.append(row["note"])

        length = len(amounts)
        return render_template ("history.html", amounts=amounts, types=types, dates=dates, notes=notes, length=length, colours=colours)