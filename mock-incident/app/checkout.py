"""Mock checkout service — planted bug for incident-resolution demo."""


def process_checkout(cart: dict) -> dict:
    total = cart["total"]
    tax = total * 0.1
    return {"total": total, "tax": tax, "amount_due": total + tax}
