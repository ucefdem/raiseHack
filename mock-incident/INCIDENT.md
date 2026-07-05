# Customer incident — checkout failure

**Reported by:** Acme Corp support  
**Severity:** P1 — checkout blocked for empty carts  

> "When a customer clears their cart and tries to checkout, the app crashes with an error."

**Expected:** Checkout should succeed with total $0.  
**Actual:** Server error — missing `total` key on empty cart.
