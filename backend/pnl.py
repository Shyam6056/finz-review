from db import conn

CATEGORIES = {
    "Sales Revenue": "Revenue",
    "Food & Ingredients": "COGS", "Packaging": "COGS",
    "Salaries & Wages": "Payroll",
    "Rent": "Opex", "Utilities": "Opex", "Marketing": "Opex",
    "Software & Subscriptions": "Opex", "Insurance": "Opex",
    "Bank Fees": "Opex", "Other Expenses": "Opex",
    "Loan Repayment": "Non-P&L", "Owner Draw": "Non-P&L",
    "Equipment Purchase": "Non-P&L", "Tax Payment": "Non-P&L",
    "Internal Transfer": "Non-P&L",
    "Uncategorized": "Unknown",
}
LINES = ["revenue", "cogs", "gross_profit", "payroll", "opex", "operating_profit"]
LINE_OF = {"Revenue": "revenue", "COGS": "cogs", "Payroll": "payroll", "Opex": "opex"}
SIGN = {"revenue": 1, "cogs": -1, "payroll": -1, "opex": -1}

def monthly_pnl():
    with conn() as c:
        rows = c.execute("SELECT month, category, SUM(amount) AS total FROM transactions GROUP BY month, category").fetchall()
    months = {}
    for r in rows:
        m = months.setdefault(r["month"], {"month": r["month"], "revenue": 0.0, "cogs": 0.0,
                                           "payroll": 0.0, "opex": 0.0, "excluded": 0.0, "by_category": {}})
        line, t = CATEGORIES.get(r["category"], "Unknown"), r["total"]
        if line == "Revenue":
            m["revenue"] += t; m["by_category"][r["category"]] = t
        elif line in ("COGS", "Payroll", "Opex"):
            m[line.lower()] -= t; m["by_category"][r["category"]] = -t
        else:
            m["excluded"] += t
    out = []
    for k in sorted(months):
        m = months[k]
        m["gross_profit"] = m["revenue"] - m["cogs"]
        m["operating_profit"] = m["gross_profit"] - m["payroll"] - m["opex"]
        for f in ("revenue", "cogs", "payroll", "opex", "excluded", "gross_profit", "operating_profit"):
            m[f] = round(m[f], 2)
        m["by_category"] = {a: round(b, 2) for a, b in m["by_category"].items()}
        out.append(m)
    return out

def top_transactions(month, category, n=5):
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT id,date,description,amount FROM transactions WHERE month=? AND category=? ORDER BY ABS(amount) DESC LIMIT ?",
            (month, category, n))]

def drivers(prev, cur, key):
    if key in ("gross_profit", "operating_profit"):
        parts = ["revenue", "cogs"] if key == "gross_profit" else ["revenue", "cogs", "payroll", "opex"]
        d = [{"type": "line", "name": p, "impact": round(SIGN[p] * (cur[p] - prev[p]), 2)} for p in parts]
        return sorted(d, key=lambda x: -abs(x["impact"]))
    d = []
    for cat in set(prev["by_category"]) | set(cur["by_category"]):
        if LINE_OF.get(CATEGORIES.get(cat)) != key:
            continue
        delta = cur["by_category"].get(cat, 0) - prev["by_category"].get(cat, 0)
        d.append({"type": "category", "name": cat, "change": round(delta, 2),
                  "transactions": top_transactions(cur["month"], cat)})
    return sorted(d, key=lambda x: -abs(x["change"]))[:3]

def variances(to_month=None, pct=10, min_abs=500):
    p, out = monthly_pnl(), []
    for prev, cur in zip(p, p[1:]):
        if to_month and cur["month"] != to_month:
            continue
        for key in LINES:
            change = round(cur[key] - prev[key], 2)
            pc = round(change / abs(prev[key]) * 100, 1) if prev[key] else None
            if abs(change) >= min_abs and (pc is None or abs(pc) >= pct):
                out.append({"from": prev["month"], "to": cur["month"], "line": key,
                            "before": prev[key], "after": cur[key], "change": change,
                            "pct": pc, "drivers": drivers(prev, cur, key)})
    return out
