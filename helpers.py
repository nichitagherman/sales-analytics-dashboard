from functools import wraps
from flask import redirect, session

def login_required(f):
    """
    Decorate routes to require login.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def admin_required(f):
    """
    Decorate routes to require admin rights
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("rights") != "admin":
            return redirect("/")
        return f(*args, **kwargs)

    return decorated_function

def usd(value):
    """Format value as USD."""
    return f"${value:,.0f}"


def process_data_for_chart(data):
    """
    Processes the result of SQLAlchemy query execute
    from [{}, {}, {}] into {[], []} format,
    convenient for JS charts
    """

    processed_data = {}
    for row in data:
        for col, val in row.items():
            if col not in processed_data:
                processed_data[col] = [val]
            else:
                processed_data[col].append(val)
    
    return processed_data