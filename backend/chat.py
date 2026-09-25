import os, json
import anthropic
from db import search
from pnl import monthly_pnl, variances

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")

SYSTEM = """You are a financial analyst assistant.
Rules:
1. Never calculate or invent numbers. Use only numbers returned by tools.
2. If the tools cannot answer, say you do not know.
3. Mention months and cite transaction IDs like #12 when explaining drivers.
4. Non-P&L items (loans, owner draws, equipment, taxes, transfers) are excluded from the P&L.
5. Keep answers short and simple."""

TOOLS = [
    {"name": "get_pnl", "description": "Monthly P&L calculated by code. Optional month YYYY-MM.",
     "input_schema": {"type": "object", "properties": {"month": {"type": "string"}}}},
    {"name": "get_variances", "description": "Material month-over-month changes with drivers and transaction ids. Optional to_month YYYY-MM.",
     "input_schema": {"type": "object", "properties": {"to_month": {"type": "string"}}}},
    {"name": "search_transactions", "description": "Find transactions by month, category or description text.",
     "input_schema": {"type": "object", "properties": {"month": {"type": "string"}, "category": {"type": "string"},
                                                       "text": {"type": "string"}, "limit": {"type": "integer"}}}},
    {"name": "list_review_items", "description": "Transactions that need human review.",
     "input_schema": {"type": "object", "properties": {}}},
]

def run_tool(name, a):
    if name == "get_pnl":
        p = monthly_pnl()
        return [m for m in p if m["month"] == a["month"]] if a.get("month") else p
    if name == "get_variances":
        return variances(a.get("to_month"))
    if name == "search_transactions":
        return search(a.get("month", ""), a.get("category", ""), a.get("text", ""), 0, min(int(a.get("limit", 20)), 50))
    if name == "list_review_items":
        return search(review=1, limit=50)
    return {"error": "unknown tool"}

def ask(question, history):
    if not os.getenv("ANTHROPIC_API_KEY"):
        return {"answer": "No API key set. Add ANTHROPIC_API_KEY to .env.", "evidence": []}
    client, evidence = anthropic.Anthropic(), []
    messages = list(history) + [{"role": "user", "content": question}]
    for _ in range(6):
        r = client.messages.create(model=MODEL, max_tokens=1500, system=SYSTEM, tools=TOOLS, messages=messages)
        if r.stop_reason != "tool_use":
            return {"answer": "".join(b.text for b in r.content if b.type == "text"), "evidence": evidence}
        messages.append({"role": "assistant", "content": r.content})
        results = []
        for b in r.content:
            if b.type == "tool_use":
                out = run_tool(b.name, b.input)
                evidence.append({"tool": b.name, "input": b.input, "output": out})
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(out)})
        messages.append({"role": "user", "content": results})
    return {"answer": "Sorry, I could not finish that.", "evidence": evidence}