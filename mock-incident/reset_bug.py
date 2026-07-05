#!/usr/bin/env python3
"""Restore the planted checkout bug for repeat demos."""

from pathlib import Path

BUGGY = '''"""Mock checkout service — planted bug for incident-resolution demo."""


def process_checkout(cart: dict) -> dict:
    # BUG: empty carts have no "total" key → KeyError for customers
    total = cart["total"]
    tax = total * 0.1
    return {"total": total, "tax": tax, "amount_due": total + tax}
'''

if __name__ == "__main__":
    path = Path(__file__).resolve().parent / "app" / "checkout.py"
    path.write_text(BUGGY, encoding="utf-8")
    print(f"Reset buggy checkout → {path}")
