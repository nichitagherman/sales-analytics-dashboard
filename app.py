from sqlalchemy import (
    create_engine, 
    MetaData, 
    Table, 
    Column, 
    Integer, 
    Float, 
    ForeignKey, 
    select, 
    update, 
    func, 
    desc
)

from helpers import login_required, usd, process_data_for_chart

from flask import Flask, abort, render_template, redirect, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

app = Flask(__name__)

app.jinja_env.filters["usd"] = usd

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure connection to db and tables
engine = create_engine("sqlite:///dry_cleaning.db", connect_args={"autocommit": False})
metadata = MetaData()
users_tab = Table(
    "users", 
    metadata, 
    autoload_with=engine
)
customers_tab = Table(
    "customers", 
    metadata,
    Column("id", Integer, primary_key=True),
    autoload_with=engine
)
items_tab = Table(
    "items", 
    metadata,
    Column("id", Integer, primary_key=True),
    autoload_with=engine
)
orders_tab = Table(
    "orders", 
    metadata,
    Column("id", Integer, primary_key=True),
    Column("total", Float),
    Column("customer_id", Integer, ForeignKey("customers.id")),
    Column("item_id", Integer, ForeignKey("items.id")),
    autoload_with=engine
)

# Number of top customers to display on the main dashboard webpage
N_TOP_CUST = 10

# Number of top countries by sales to be represented on pie chart explicitly
N_TOP_COUNTRIES = 10

@app.route("/")
@login_required
def index():

    # Collect total sales number by dates
    with engine.connect() as conn:
        stmt = (
            select(orders_tab.c.order_date, 
                   func.sum(orders_tab.c.total).label("total_sales"), 
                   func.sum(orders_tab.c.quantity).label("total_quantity"))
            .group_by(orders_tab.c.order_date)
            .order_by(orders_tab.c.order_date)
        )
        orders = conn.execute(stmt).mappings().all()

    orders_processed = process_data_for_chart(orders)
    orders_processed['order_date'] = [d.split(' ')[0] for d in orders_processed["order_date"]]

    # Collect top n customers by total sales
    with engine.connect() as conn:
        stmt = (
            select(
                customers_tab.c.name.label("name"),
                customers_tab.c.country.label("country"),
                func.sum(orders_tab.c.total).label("total_sales")
            )
            .join(customers_tab, orders_tab.c.customer_id == customers_tab.c.id)
            .group_by(customers_tab.c.id)
            .order_by(desc(func.sum(orders_tab.c.total)))
            .limit(N_TOP_CUST)
        )
        top_customers = conn.execute(stmt).mappings().all()
    
    # Collect total sales by customers' country
    with engine.connect() as conn:
        stmt = (
            select(
                customers_tab.c.country.label("country"),
                func.sum(orders_tab.c.total).label("total_sales")
            )
            .join(customers_tab, orders_tab.c.customer_id == customers_tab.c.id)
            .group_by(customers_tab.c.country)
            .order_by(desc(func.sum(orders_tab.c.total)))
        )
        countries = conn.execute(stmt).mappings().all()
    countries_processed = process_data_for_chart(countries)
    # Truncate countries_processed to include N top countries and the rest put in Others category
    countries_processed["country"] = countries_processed["country"][:N_TOP_COUNTRIES]
    total_sales = sum(countries_processed["total_sales"])
    total_sales_other = sum(countries_processed["total_sales"][N_TOP_COUNTRIES:])
    countries_processed["total_sales"] = countries_processed["total_sales"][:N_TOP_COUNTRIES]
    assert (total_sales - (total_sales_other + sum(countries_processed["total_sales"]))) < 1e-7
    countries_processed["country"].append("Other")
    countries_processed["total_sales"].append(total_sales_other)

    # Collect total sales by item name
    with engine.connect() as conn:
        stmt = (
            select(
                items_tab.c.name.label("name"),
                func.sum(orders_tab.c.total).label("total_sales")
            )
            .join(items_tab, orders_tab.c.item_id == items_tab.c.id)
            .group_by(items_tab.c.name)
            .order_by(desc(func.sum(orders_tab.c.total)))
        )
        items = conn.execute(stmt).mappings().all()
    items_processed = process_data_for_chart(items)
    
    return render_template(
        "index.html",
        ts_sales=orders_processed,
        sales_countries=countries_processed,
        sales_items=items_processed,
        top_customers=top_customers
    )


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