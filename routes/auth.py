from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db_connection

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user and check_password_hash(user["password_hash"], password):

            session["user_id"] = user["user_id"]
            session["user_name"] = user["full_name"]

            return redirect(url_for("auth.dashboard"))

        return "Invalid email or password!"

    return render_template("login.html")

@auth.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    conn = get_db_connection()

    try:
        cursor = conn.cursor(dictionary=True)

        # 1. Count groups this user belongs to
        cursor.execute("""
            SELECT COUNT(DISTINCT group_id) AS total_groups
            FROM group_members
            WHERE user_id = %s
        """, (user_id,))

        group_data = cursor.fetchone()
        total_groups = group_data["total_groups"] or 0

        # 2. Count expenses in this user's groups
        cursor.execute("""
            SELECT COUNT(*) AS total_expenses
            FROM expenses e
            JOIN group_members gm ON gm.group_id = e.group_id
            WHERE gm.user_id = %s
        """, (user_id,))

        expense_data = cursor.fetchone()
        total_expenses = expense_data["total_expenses"] or 0

        # 3. Calculate how much this user paid
        cursor.execute("""
            SELECT COALESCE(SUM(e.total_amount), 0) AS total_paid
            FROM expenses e
            JOIN group_members gm ON gm.group_id = e.group_id
            WHERE gm.user_id = %s
              AND e.paid_by = %s
        """, (user_id, user_id))

        paid_data = cursor.fetchone()
        total_paid = float(paid_data["total_paid"] or 0)

        # 4. Calculate this user's share of group expenses
        cursor.execute("""
            SELECT COALESCE(SUM(es.amount_owed), 0) AS total_owed
            FROM expense_splits es
            JOIN expenses e ON e.expense_id = es.expense_id
            JOIN group_members gm ON gm.group_id = e.group_id
            WHERE gm.user_id = %s
              AND es.user_id = %s
        """, (user_id, user_id))

        owed_data = cursor.fetchone()
        total_share = float(owed_data["total_owed"] or 0)

        # Positive = others owe this user.
        # Negative = this user owes others.
        net_balance = round(total_paid - total_share, 2)

        you_are_owed = max(net_balance, 0)
        you_owe = max(-net_balance, 0)

        return render_template(
            "dashboard.html",
            total_groups=total_groups,
            total_expenses=total_expenses,
            you_owe=you_owe,
            you_are_owed=you_are_owed
        )

    finally:
        conn.close()

@auth.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("auth.login"))

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users (full_name, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (full_name, email, password_hash)
        )

        connection.commit()

        cursor.close()
        connection.close()

        return "Registration successful! 🎉"

    return render_template("register.html")