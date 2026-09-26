from dotenv import load_dotenv
load_dotenv()

import io
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db import conn, init, search
from pnl import CATEGORIES, monthly_pnl, variances
from categorize import categorize_rows, flag_all, norm
import chat

init()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def read_table(raw, name):
    df = pd.read_excel(io.BytesIO(raw)) if name.lower().endswith((".xlsx", ".xls")) else pd.read_csv(io.BytesIO(raw))
    cols = {c.lower().strip(): c for c in df.columns}
    def find(*keys):
        for low, orig in cols.items():
            if any(k in low for k in keys):
                return orig
    dcol = find("date")
    ncol = find("descr", "narr", "detail", "memo", "particular", "payee")
    deb, cre, acol = find("debit", "withdraw"), find("credit", "deposit"), find("amount", "amt")
    if not dcol or not ncol:
        raise ValueError(f"Need date and description columns. Found: {list(df.columns)}")
    num = lambda s: pd.to_numeric(s.astype(str).str.replace(",", "").str.replace("$", "", regex=False).str.strip(), errors="coerce")
    if deb and cre:
        amount = num(df[cre]).fillna(0) - num(df[deb]).fillna(0)
    elif acol:
        amount = num(df[acol])
    else:
        raise ValueError("Need an amount column (or debit + credit columns).")
    date = None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
        d = pd.to_datetime(df[dcol], format=fmt, errors="coerce")
        if d.notna().mean() > 0.9:
            date = d
            break
    if date is None:
        date = pd.to_datetime(df[dcol], errors="coerce")
    ok = date.notna() & amount.notna()
    rows = [{"date": d.strftime("%Y-%m-%d"), "month": d.strftime("%Y-%m"),
             "description": str(t).strip(), "amount": float(a)}
            for d, t, a in zip(date[ok], df[ncol][ok], amount[ok])]
    return rows, int((~ok).sum())

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    raw = await file.read()
    try:
        rows, skipped = read_table(raw, file.filename)
    except Exception as e:
        raise HTTPException(400, f"Could not read file: {e}")
    cats = categorize_rows(rows)
    with conn() as c:
        c.execute("DELETE FROM transactions")
        for r, (cat, conf, src) in zip(rows, cats):
            c.execute("INSERT INTO transactions(date,month,description,amount,category,confidence,source) VALUES(?,?,?,?,?,?,?)",
                      (r["date"], r["month"], r["description"], r["amount"], cat, conf, src))
    flag_all()
    with conn() as c:
        n = c.execute("SELECT COUNT(*) FROM transactions WHERE needs_review=1").fetchone()[0]
    return {"saved": len(rows), "skipped": skipped, "needs_review": n}

@app.get("/api/categories")
def categories():
    return [{"name": k, "line": v} for k, v in CATEGORIES.items()]

@app.get("/api/transactions")
def transactions(month: str = "", category: str = "", review: int = 0, text: str = ""):
    return search(month, category, text, review)

class Fix(BaseModel):
    category: str

@app.patch("/api/transactions/{tid}")
def fix(tid: int, body: Fix):
    if body.category not in CATEGORIES:
        raise HTTPException(400, "Unknown category")
    with conn() as c:
        r = c.execute("SELECT description FROM transactions WHERE id=?", (tid,)).fetchone()
        if not r:
            raise HTTPException(404, "Not found")
        c.execute("UPDATE transactions SET category=?, confidence=1, source='user', resolved=1, needs_review=0, review_reason='' WHERE id=?",
                  (body.category, tid))
        c.execute("INSERT OR REPLACE INTO corrections VALUES(?,?)", (norm(r["description"]), body.category))
    flag_all()
    return {"ok": True}

@app.post("/api/transactions/{tid}/resolve")
def resolve(tid: int):
    with conn() as c:
        c.execute("UPDATE transactions SET resolved=1, needs_review=0, review_reason='' WHERE id=?", (tid,))
    return {"ok": True}

@app.get("/api/pnl")
def pnl():
    return monthly_pnl()

@app.get("/api/variances")
def var():
    return variances()

@app.get("/api/check")
def check():
    with conn() as c:
        total = c.execute("SELECT SUM(amount) FROM transactions").fetchone()[0] or 0
    calc = sum(m["operating_profit"] + m["excluded"] for m in monthly_pnl())
    return {"transactions_total": round(total, 2), "pnl_plus_excluded": round(calc, 2), "ok": abs(total - calc) < 0.01}

class Chat(BaseModel):
    question: str
    history: list = []

@app.post("/api/chat")
def chat_api(body: Chat):
    return chat.ask(body.question, body.history)