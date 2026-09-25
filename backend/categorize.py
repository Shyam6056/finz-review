import os, re, json, statistics
import anthropic
from db import conn
from pnl import CATEGORIES

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")

RULES = [
    (["payroll", "salary", "wages", "payroll taxes"], "Salaries & Wages"),
    (["rent", "lease"], "Rent"),
    (["electric", "utility", "utilities", "broadband", "internet", "water bill", "gas/water"], "Utilities"),
    (["google ads", "facebook ads", "meta ads", "advert", "marketing"], "Marketing"),
    (["pos settlement", "pos batch deposit", "zomato", "swiggy", "stripe", "razorpay",
      "catering invoice", "delivery marketplace payout", "food sales", "beverage sales"], "Sales Revenue"),
    (["food inventory", "beverage inventory", "vegetable", "grocery", "meat", "dairy",
      "ingredient", "wholesale", "produce", "butcher", "sysco", "us foods"], "Food & Ingredients"),
    (["packaging", "boxes", "disposables", "to-go"], "Packaging"),
    (["subscription", "software", "notion", "slack", "zoom", "aws", "pos/software"], "Software & Subscriptions"),
    (["insurance"], "Insurance"),
    (["bank fee", "service charge"], "Bank Fees"),
    (["loan", "emi"], "Loan Repayment"),
    (["owner", "drawings"], "Owner Draw"),
    (["transfer to", "transfer from", "own account"], "Internal Transfer"),
    (["gst", "tds", "income tax"], "Tax Payment"),
    (["equipment", "machine", "oven"], "Equipment Purchase"),
    (["accounting", "bookkeeping", "cleaning", "linen", "delivery platform commission",
      "commission"], "Other Expenses"),
]

def norm(text):
    return re.sub(r"[^a-z ]", "", (text or "").lower()).strip()

def rule_category(desc):
    d = (desc or "").lower()
    for words, cat in RULES:
        if any(re.search(r"\b" + re.escape(w), d) for w in words):
            return cat
    return None

def ai_categorize(items):
    if not items or not os.getenv("ANTHROPIC_API_KEY"):
        return {}
    client, out = anthropic.Anthropic(), {}
    for k in range(0, len(items), 40):
        batch = items[k:k + 40]
        prompt = ("Classify each bank transaction into ONE category from this list:\n" + ", ".join(CATEGORIES)
                  + "\nAmount > 0 is money in, < 0 is money out.\n"
                  'Return ONLY a JSON list like [{"i":0,"category":"Rent","confidence":0.9}]. '
                  "Give confidence below 0.7 when unsure.\n\n" + json.dumps(batch))
        try:
            r = client.messages.create(model=MODEL, max_tokens=3000,
                                       messages=[{"role": "user", "content": prompt}])
            t = r.content[0].text
            for x in json.loads(t[t.index("["): t.rindex("]") + 1]):
                out[x["i"]] = (x["category"], float(x["confidence"]))
        except Exception as e:
            print("AI categorize failed:", e)
    return out

def categorize_rows(rows):
    with conn() as c:
        learned = {r["pattern"]: r["category"] for r in c.execute("SELECT * FROM corrections")}
    result, need = [None] * len(rows), []
    for i, r in enumerate(rows):
        p = norm(r["description"])
        if p in learned:
            result[i] = (learned[p], 1.0, "user")
        elif rule_category(r["description"]):
            result[i] = (rule_category(r["description"]), 0.9, "rule")
        else:
            need.append({"i": i, "description": r["description"], "amount": r["amount"]})
    ai = ai_categorize(need)
    for n in need:
        cat, conf = ai.get(n["i"], ("Uncategorized", 0.0))
        if cat not in CATEGORIES:
            cat, conf = "Uncategorized", 0.0
        result[n["i"]] = (cat, conf, "ai" if n["i"] in ai else "none")
    return result

def flag_all():
    with conn() as c:
        rows = c.execute("SELECT * FROM transactions").fetchall()
        dup, amts = {}, {}
        for r in rows:
            k = (r["date"], r["amount"], r["description"])
            dup[k] = dup.get(k, 0) + 1
            amts.setdefault(r["category"], []).append(abs(r["amount"]))
        for r in rows:
            if r["resolved"]:
                continue
            why, line = [], CATEGORIES.get(r["category"], "Unknown")
            if r["confidence"] < 0.7: why.append("Category is uncertain")
            if line == "Non-P&L": why.append("Not a P&L item - may need different accounting treatment")
            if dup[(r["date"], r["amount"], r["description"])] > 1: why.append("Possible duplicate")
            a = amts[r["category"]]
            if len(a) >= 5 and abs(r["amount"]) > 3 * statistics.median(a): why.append("Unusually large for this category")
            if line in ("COGS", "Payroll", "Opex") and r["amount"] > 0: why.append("Money in for an expense category (refund?)")
            if line == "Revenue" and r["amount"] < 0: why.append("Money out for a revenue category")
            c.execute("UPDATE transactions SET needs_review=?, review_reason=? WHERE id=?",
                      (1 if why else 0, "; ".join(why), r["id"]))