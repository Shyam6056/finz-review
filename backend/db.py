import sqlite3

DB = "finz.db"

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, month TEXT, description TEXT, amount REAL,
            category TEXT, confidence REAL, source TEXT,
            needs_review INTEGER DEFAULT 0, review_reason TEXT DEFAULT '',
            resolved INTEGER DEFAULT 0)""")
        c.execute("CREATE TABLE IF NOT EXISTS corrections(pattern TEXT PRIMARY KEY, category TEXT)")

def search(month="", category="", text="", review=0, limit=500):
    sql, p = "SELECT * FROM transactions WHERE 1=1", []
    if month: sql += " AND month=?"; p.append(month)
    if category: sql += " AND category=?"; p.append(category)
    if text: sql += " AND description LIKE ?"; p.append(f"%{text}%")
    if review: sql += " AND needs_review=1"
    sql += " ORDER BY date, id LIMIT ?"; p.append(limit)
    with conn() as c:
        return [dict(r) for r in c.execute(sql, p)]
