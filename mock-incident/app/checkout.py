"""Mock checkout service — planted bug for incident-resolution demo."""


def process_checkout(cart: dict) -> dict:
    # BUG: empty carts have no "total" key → KeyError for customers
    total = cart.get("total", 0)
    tax = total * 0.1
    return {"total": total, "tax": tax, "amount_due": total + tax}
