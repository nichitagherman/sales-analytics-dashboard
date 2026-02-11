from sqlalchemy import create_engine, MetaData, Table, select, update

from helpers import login_required

from flask import Flask, abort, render_template, redirect, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure connection to db
engine = create_engine("sqlite:///dry_cleaning.db", connect_args={"autocommit": False})
metadata = MetaData()
users_tab = Table("users", metadata, autoload_with=engine)

@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    if session.get("user_id") is not None:
        # Redirect user to home page
        return redirect("/")

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return abort(400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return abort(400)

        # Query database for username
        with engine.connect() as conn:
            stmt = select(users_tab).where(users_tab.c.username == request.form.get("username"))
            rows = conn.execute(stmt).mappings().all()
        
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["password_hash"], request.form.get("password")
        ):
            return abort(401)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["rights"] = rows[0]["rights"]

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        new_password = request.form.get("new_password")
        # Ensure password was submitted
        if not request.form.get("old_password") or \
            not new_password or \
                not request.form.get("confirm_password"):
            return abort(400)

        # Query database for username
        with engine.connect() as conn:
            stmt = select(users_tab).where(users_tab.c.id == session["user_id"])
            rows = conn.execute(stmt).mappings().all()
        
        # Ensure old password was typed in correctly
        if len(rows) != 1 or not check_password_hash(
            rows[0]["password_hash"], request.form.get("old_password")
        ):
            return abort(401, description="Incorrect old password.")
        
        if new_password != request.form.get("confirm_password"):
            return abort(400, description="New passwords don't match.")
        
        if new_password == request.form.get("old_password"):
            return abort(400, description="Old and new passwords are identical.")

        with engine.begin() as conn:
            stmt = (
                update(users_tab)
                .where(users_tab.c.id == session["user_id"])
                .values(password_hash=generate_password_hash(new_password))
            )
            result = conn.execute(stmt)

            if result.rowcount == 0:
                return abort(500)

        session.clear()
        session["password_changed"] = 1
        
        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("change_password.html")

@app.context_processor
def inject_session():

    if session.get("user_id") is not None:
        logged = 1
        rights = session["rights"]
    else:
        logged = 0
        rights = None
    
    if session.get("password_changed") is not None:
        password_changed = 1
        session["password_changed"] = None
    else:
        password_changed = 0
        
    return dict(logged=logged, rights=rights, password_changed=password_changed)

@app.errorhandler(400)
def page_not_found(e):
    return render_template('400.html', error_message=str(e)), 400

@app.errorhandler(401)
def page_not_found(e):
    return render_template('401.html', error_message=str(e)), 400