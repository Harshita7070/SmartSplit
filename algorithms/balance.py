
def calculate_balances(expenses):
    balances = {}

    for expense in expenses:
        paid_by = expense["paid_by"]
        total_amount = float(expense["total_amount"])

        # Record the amount paid by this member
        balances[paid_by] = balances.get(paid_by, 0) + total_amount

        # Subtract each member's share of the expense
        for split in expense["splits"]:
            user_id = split["user_id"]
            amount_owed = float(split["amount_owed"])

            balances[user_id] = balances.get(user_id, 0) - amount_owed

    # Round balances to two decimal places
    return {
        user_id: round(balance, 2)
        for user_id, balance in balances.items()
    }
