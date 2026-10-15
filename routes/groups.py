from flask import Blueprint, render_template, request, redirect, url_for, session
from database.db import get_db_connection
from algorithms.balance import calculate_balances
from algorithms.settlement import minimize_transactions

groups = Blueprint("groups", __name__)


@groups.route("/groups")
def view_groups():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT g.group_id, g.group_name, g.description
        FROM `groups` g
        INNER JOIN group_members gm
            ON g.group_id = gm.group_id
        WHERE gm.user_id = %s
        ORDER BY g.created_at DESC
        """,
        (user_id,)
    )

    user_groups = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "groups.html",
        user_groups=user_groups
    )


@groups.route("/groups/create", methods=["POST"])
def create_group():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    group_name = request.form["group_name"]
    description = request.form["description"]
    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO `groups` (group_name, description, created_by)
        VALUES (%s, %s, %s)
        """,
        (group_name, description, user_id)
    )

    connection.commit()

    group_id = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO group_members (group_id, user_id)
        VALUES (%s, %s)
        """,
        (group_id, user_id)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("groups.view_groups"))

@groups.route("/groups/<int:group_id>")
def group_details(group_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT group_id, group_name, description
        FROM `groups`
        WHERE group_id = %s
        """,
        (group_id,)
    )

    group = cursor.fetchone()

    cursor.execute(
        """
        SELECT u.user_id, u.full_name, u.email
        FROM group_members gm
        JOIN users u
            ON gm.user_id = u.user_id
        WHERE gm.group_id = %s
        """,
        (group_id,)
    )

    members = cursor.fetchall()

    cursor.close()
    connection.close()

    if not group:
        return "Group not found!"

    return render_template(
        "group_details.html",
        group=group,
        members=members
    )

@groups.route("/groups/<int:group_id>/add-expense", methods=["GET", "POST"])
def add_expense(group_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get group
    cursor.execute(
        """
        SELECT group_id, group_name, description
        FROM `groups`
        WHERE group_id = %s
        """,
        (group_id,)
    )

    group = cursor.fetchone()

    if not group:
        cursor.close()
        connection.close()
        return "Group not found!"

    # Get group members
    cursor.execute(
        """
        SELECT u.user_id, u.full_name, u.email
        FROM group_members gm
        JOIN users u ON gm.user_id = u.user_id
        WHERE gm.group_id = %s
        """,
        (group_id,)
    )

    members = cursor.fetchall()

    # Save expense
    if request.method == "POST":

        description = request.form["description"]
        total_amount = float(request.form["total_amount"])
        paid_by = int(request.form["paid_by"])
        split_type = request.form["split_type"]
        expense_date = request.form["expense_date"]

        # Save expense
        cursor.execute(
            """
            INSERT INTO expenses
            (group_id, paid_by, description, total_amount, split_type, expense_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                group_id,
                paid_by,
                description,
                total_amount,
                split_type,
                expense_date
            )
        )

        expense_id = cursor.lastrowid

        # Equal split
        if split_type == "equal":

            share = round(total_amount / len(members), 2)

            for member in members:
                cursor.execute(
                    """
                    INSERT INTO expense_splits
                    (expense_id, user_id, amount_owed)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        expense_id,
                        member["user_id"],
                        share
                    )
                )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("groups.view_expenses", group_id=group_id))

    cursor.close()
    connection.close()

    return render_template(
        "add_expense.html",
        group=group,
        members=members
    )

@groups.route("/groups/<int:group_id>/expenses")
def view_expenses(group_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            e.expense_id,
            e.description,
            e.total_amount,
            e.split_type,
            e.expense_date,
            u.full_name AS paid_by_name
        FROM expenses e
        JOIN users u
            ON e.paid_by = u.user_id
        WHERE e.group_id = %s
        ORDER BY e.expense_date DESC
        """,
        (group_id,)
    )

    expenses = cursor.fetchall()

    cursor.execute(
        """
        SELECT group_id, group_name, description
        FROM `groups`
        WHERE group_id = %s
        """,
        (group_id,)
    )

    group = cursor.fetchone()

    cursor.close()
    connection.close()

    if not group:
        return "Group not found!"

    return render_template(
        "expenses.html",
        group=group,
        expenses=expenses
    )

    
@groups.route("/groups/<int:group_id>/balances")
def view_balances(group_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Get group information
        cursor.execute(
            "SELECT * FROM `groups` WHERE group_id = %s",
            (group_id,)
        )
        group = cursor.fetchone()

        if not group:
            return "Group not found!", 404

        # Get group members
        cursor.execute(
            """
            SELECT u.user_id, u.full_name
            FROM group_members gm
            JOIN users u ON gm.user_id = u.user_id
            WHERE gm.group_id = %s
            """,
            (group_id,)
        )
        members = cursor.fetchall()

        # Get expenses
        cursor.execute(
            """
            SELECT expense_id, paid_by, total_amount
            FROM expenses
            WHERE group_id = %s
            """,
            (group_id,)
        )
        expense_rows = cursor.fetchall()

        expenses = []

        # Get splits for each expense
        for expense in expense_rows:
            cursor.execute(
                """
                SELECT user_id, amount_owed
                FROM expense_splits
                WHERE expense_id = %s
                """,
                (expense["expense_id"],)
            )

            expense["splits"] = cursor.fetchall()
            expenses.append(expense)

        # Calculate balances from expenses
        balances = calculate_balances(expenses)

        # Subtract only completed settlements
        cursor.execute(
            """
            SELECT payer_id, receiver_id, amount
            FROM settlements
            WHERE group_id = %s AND status = 'paid'
            """,
            (group_id,)
        )
        paid_settlements = cursor.fetchall()

        for payment in paid_settlements:
            payer_id = payment["payer_id"]
            receiver_id = payment["receiver_id"]
            amount = float(payment["amount"])

            # The payer's debt decreases
            balances[payer_id] = round(
                balances.get(payer_id, 0) + amount, 2
            )

            # The receiver's credit decreases
            balances[receiver_id] = round(
                balances.get(receiver_id, 0) - amount, 2
            )

        # Include every group member, even with a zero balance
        for member in members:
            balances.setdefault(member["user_id"], 0.0)

        return render_template(
            "balances.html",
            group=group,
            members=members,
            balances=balances
        )

    finally:
        cursor.close()
        connection.close()


@groups.route("/groups/<int:group_id>/settlements")
def view_settlements(group_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Get group
        cursor.execute(
            "SELECT * FROM `groups` WHERE group_id = %s",
            (group_id,)
        )
        group = cursor.fetchone()

        if not group:
            return "Group not found!", 404

        # Get group members
        cursor.execute(
            """
            SELECT u.user_id, u.full_name
            FROM group_members gm
            JOIN users u ON gm.user_id = u.user_id
            WHERE gm.group_id = %s
            """,
            (group_id,)
        )
        members = cursor.fetchall()

        member_names = {
            member["user_id"]: member["full_name"]
            for member in members
        }
        member_ids = set(member_names.keys())

        # Get expenses
        cursor.execute(
            """
            SELECT expense_id, paid_by, total_amount
            FROM expenses
            WHERE group_id = %s
            """,
            (group_id,)
        )
        expense_rows = cursor.fetchall()

        expenses = []

        for expense in expense_rows:
            cursor.execute(
                """
                SELECT user_id, amount_owed
                FROM expense_splits
                WHERE expense_id = %s
                """,
                (expense["expense_id"],)
            )
            expense["splits"] = cursor.fetchall()
            expenses.append(expense)

        # Calculate balances from expenses
        balances = calculate_balances(expenses)

        # Include all group members
        for member_id in member_ids:
            balances.setdefault(member_id, 0.0)

        # Apply completed payments exactly once
        cursor.execute(
            """
            SELECT payer_id, receiver_id, amount
            FROM settlements
            WHERE group_id = %s AND status = 'paid'
            """,
            (group_id,)
        )
        paid_settlements = cursor.fetchall()

        for payment in paid_settlements:
            payer_id = payment["payer_id"]
            receiver_id = payment["receiver_id"]
            amount = float(payment["amount"])

            if payer_id in member_ids:
                balances[payer_id] = round(
                    balances.get(payer_id, 0) + amount, 2
                )

            if receiver_id in member_ids:
                balances[receiver_id] = round(
                    balances.get(receiver_id, 0) - amount, 2
                )

        # Generate suggestions only for group members
        group_balances = {
            member_id: balances[member_id]
            for member_id in member_ids
        }

        transactions = minimize_transactions(group_balances)

        for transaction in transactions:
            transaction["from_name"] = member_names.get(
                transaction["from_user"], "Unknown"
            )
            transaction["to_name"] = member_names.get(
                transaction["to_user"], "Unknown"
            )

        # Fetch saved settlements
        cursor.execute(
            """
            SELECT
                s.settlement_id,
                s.payer_id,
                s.receiver_id,
                s.amount,
                s.status,
                payer.full_name AS from_name,
                receiver.full_name AS to_name
            FROM settlements s
            JOIN users payer ON s.payer_id = payer.user_id
            JOIN users receiver ON s.receiver_id = receiver.user_id
            WHERE s.group_id = %s
            ORDER BY s.settlement_id DESC
            """,
            (group_id,)
        )
        saved_settlements = cursor.fetchall()

        return render_template(
            "settlements.html",
            group=group,
            transactions=transactions,
            saved_settlements=saved_settlements
        )

    finally:
        cursor.close()
        connection.close()


    


@groups.route("/groups/<int:group_id>/settlements/save", methods=["POST"])
def save_settlements(group_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Verify that the group exists
        cursor.execute(
            "SELECT group_id FROM `groups` WHERE group_id = %s",
            (group_id,)
        )
        group = cursor.fetchone()

        if not group:
            return "Group not found!", 404

        # Get group members
        cursor.execute(
            """
            SELECT user_id
            FROM group_members
            WHERE group_id = %s
            """,
            (group_id,)
        )
        member_ids = {row["user_id"] for row in cursor.fetchall()}

        # Stop if pending settlements already exist
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM settlements
            WHERE group_id = %s AND status = 'pending'
            """,
            (group_id,)
        )

        if cursor.fetchone()["total"] > 0:
            return redirect(
                url_for("groups.view_settlements", group_id=group_id)
            )

        # Get expenses
        cursor.execute(
            """
            SELECT expense_id, paid_by, total_amount
            FROM expenses
            WHERE group_id = %s
            """,
            (group_id,)
        )
        expense_rows = cursor.fetchall()

        expenses = []

        for expense in expense_rows:
            cursor.execute(
                """
                SELECT user_id, amount_owed
                FROM expense_splits
                WHERE expense_id = %s
                """,
                (expense["expense_id"],)
            )
            expense["splits"] = cursor.fetchall()
            expenses.append(expense)

        # Calculate current balances
        balances = calculate_balances(expenses)

        # Include all members and exclude non-members
        balances = {
            user_id: round(float(balances.get(user_id, 0)), 2)
            for user_id in member_ids
        }

        # Adjust balances for settlements already marked Paid
        cursor.execute(
            """
            SELECT payer_id, receiver_id, amount
            FROM settlements
            WHERE group_id = %s AND status = 'paid'
            """,
            (group_id,)
        )
        paid_settlements = cursor.fetchall()

        for payment in paid_settlements:
            payer_id = payment["payer_id"]
            receiver_id = payment["receiver_id"]
            amount = float(payment["amount"])

            if payer_id in member_ids and receiver_id in member_ids:
                balances[payer_id] = round(
                    balances.get(payer_id, 0) + amount, 2
                )
                balances[receiver_id] = round(
                    balances.get(receiver_id, 0) - amount, 2
                )

        # Generate remaining suggested payments
        transactions = minimize_transactions(balances)

        # Save the new suggestions
        for transaction in transactions:
            cursor.execute(
                """
                INSERT INTO settlements
                    (group_id, payer_id, receiver_id, amount, status)
                VALUES (%s, %s, %s, %s, 'pending')
                """,
                (
                    group_id,
                    transaction["from_user"],
                    transaction["to_user"],
                    transaction["amount"]
                )
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

    return redirect(
        url_for("groups.view_settlements", group_id=group_id)
    )


@groups.route(
    "/settlements/<int:settlement_id>/pay",
    methods=["POST"]
)
def mark_settlement_paid(settlement_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Find the settlement
    cursor.execute(
        """
        SELECT settlement_id, group_id, payer_id, status
        FROM settlements
        WHERE settlement_id = %s
        """,
        (settlement_id,)
    )

    settlement = cursor.fetchone()

    if not settlement:
        cursor.close()
        connection.close()
        return "Settlement not found!", 404

    # Only the payer or receiver can mark it as paid
    if session["user_id"] not in (
        settlement["payer_id"],
        # Receiver is checked below
    ):
        cursor.execute(
            """
            SELECT receiver_id
            FROM settlements
            WHERE settlement_id = %s
            """,
            (settlement_id,)
        )
        receiver = cursor.fetchone()

        if not receiver or session["user_id"] != receiver["receiver_id"]:
            cursor.close()
            connection.close()
            return "You are not allowed to update this settlement.", 403

    if settlement["status"] == "pending":
        cursor.execute(
            """
            UPDATE settlements
            SET status = 'paid', settled_at = NOW()
            WHERE settlement_id = %s
              AND status = 'pending'
            """,
            (settlement_id,)
        )
        connection.commit()

    group_id = settlement["group_id"]

    cursor.close()
    connection.close()

    return redirect(
        url_for("groups.view_settlements", group_id=group_id)
    )

