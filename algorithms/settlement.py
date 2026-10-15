
import heapq


def minimize_transactions(balances):
    creditors = []
    debtors = []

    for user_id, balance in balances.items():
        balance = round(float(balance), 2)

        if balance > 0:
            heapq.heappush(
                creditors, (-balance, user_id)
            )
        elif balance < 0:
            heapq.heappush(
                debtors, (balance, user_id)
            )

    transactions = []

    while creditors and debtors:
        credit, creditor_id = heapq.heappop(creditors)
        debt, debtor_id = heapq.heappop(debtors)

        credit = -credit
        debt = -debt

        payment = min(credit, debt)

        transactions.append({
            "from_user": debtor_id,
            "to_user": creditor_id,
            "amount": round(payment, 2)
        })

        credit = round(credit - payment, 2)
        debt = round(debt - payment, 2)

        if credit > 0:
            heapq.heappush(
                creditors, (-credit, creditor_id)
            )

        if debt > 0:
            heapq.heappush(
                debtors, (-debt, debtor_id)
            )

    return transactions
