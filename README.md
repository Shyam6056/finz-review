# Finz Financial Review

An AI-native application that turns raw bank transactions into an explainable monthly P&L, built for the Finz Software Engineering Internship challenge.

- **Dataset used:** NYC Restaurant Co. - Raw Transactions (provided by Finz)
- **Backend:** FastAPI + SQLite (`/backend`) — all financial math is deterministic code, never AI-generated.
- **Frontend:** React + Vite (`/frontend`) — talks to the backend over HTTP.
- **AI:** Claude API (Anthropic) is used only for categorizing transactions the rule-based classifier can't confidently label, explaining variances in plain language, and the AI analyst chat, which can only answer using tool calls into the real, structured data.

## Setup

### 1. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # then put your ANTHROPIC_API_KEY in .env
uvicorn main:app --reload    # runs on http://127.0.0.1:8000
```

### 2. Frontend
In a second terminal:
```bash
cd frontend
npm install
npm run dev                  # runs on http://127.0.0.1:5173
```

Open http://127.0.0.1:5173, and upload a transaction file (CSV or Excel). The parser looks for a date column, a description column, and either one amount column or debit/credit columns, and handles amounts formatted with `$` and commas.

## Core workflow

1. **Ingest** — upload a bank transaction file, parsed into a structured table.
2. **Categorize** — a rules engine matches common transaction wording first (fast, deterministic, free); anything it can't confidently classify is escalated to Claude, which returns a category and a confidence score. Anything still uncertain, unusual, or non-P&L in nature is flagged for review.
3. **P&L** — Revenue, COGS, Gross Profit, Payroll, Operating Expenses, and Operating Profit are all computed directly from the transaction data in Python — an LLM never generates or touches these totals.
4. **Variances** — month-over-month changes above a materiality threshold (10% and $500) are surfaced automatically, each with the specific categories and transactions driving the change.
5. **Review** — uncertain, duplicate, unusually large, or non-P&L transactions are queued for human review, with the reason shown and a one-click Approve or recategorize action.
6. **AI analyst chat** — a conversational interface that answers questions by calling tools (`get_pnl`, `get_variances`, `search_transactions`, `list_review_items`) against the real database, never by inventing numbers.

## Where AI is used vs. where deterministic code is used

| Task | Approach | Why |
|---|---|---|
| Common transaction categorization | Deterministic rules (keyword matching) | Fast, free, and reliable for well-known vendors/patterns |
| Ambiguous transaction categorization | Claude API | Requires judgment/language understanding a rules list can't cover |
| P&L totals, variance %s, reconciliation | Deterministic Python | Financial accuracy is non-negotiable; an LLM must never generate a number that ends up in a financial statement |
| Review flag reasons (duplicate, uncertain, unusual amount, non-P&L, sign mismatch) | Deterministic rules | These are objective, rule-based checks, not judgment calls |
| Variance explanations, chat answers | Claude API, restricted to tool calls | Natural-language explanation is where AI adds real value, but every number it cites must come from a tool call, not its own arithmetic |

## How incorrect or unsupported answers are prevented

The chat model's system prompt explicitly instructs it to never calculate or invent numbers, to use only numbers returned by its tools, to cite transaction IDs when explaining drivers, and to say "I don't know" if the tools can't answer the question. It has no path to generate a financial figure on its own — every number in the UI, including numbers the AI narrates, originates from the same deterministic P&L/variance functions.

## How output is verified

- `/api/check` sums every transaction and compares it against (P&L totals + excluded non-P&L items); the UI shows a ✔/✘ reconciliation line so any discrepancy is immediately visible.
- Every chat answer includes an "Evidence" panel showing the exact tool calls and raw data the model used to answer.
- Every P&L month links to its underlying transactions, and every variance driver lists the specific transaction IDs, dates, and amounts behind it.

## Key decisions

- **Materiality threshold:** a variance is flagged when it changes by both ≥10% and ≥$500, to avoid noise from small, immaterial fluctuations.
- **Non-P&L items** (loans, owner draws, equipment purchases, tax payments, internal transfers) are excluded from the P&L and separately reconciled, since they need different accounting treatment.
- **Corrections are learned:** when a user recategorizes a transaction, that description pattern is remembered and applied automatically on future uploads.

## Current status / known limitation

The AI-dependent features (ambiguous-transaction categorization, "Explain with AI," and the chat analyst) require `ANTHROPIC_API_KEY` to be set in `backend/.env`. At the time of this submission, that key had not yet been provisioned (a billing/card issue on the Anthropic Console), so those features are implemented and unit-testable but not demonstrated live in the submitted video. Every deterministic feature — ingestion, rule-based categorization, P&L, variances, review flagging, and reconciliation — is fully functional and was tested end-to-end against the provided NYC Restaurant Co. dataset (181 transactions, 0 skipped, reconciliation passes).

## Deploying

- Deploy `/backend` as a web service (e.g. Render): root directory `backend`, build `pip install -r requirements.txt`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`, with `ANTHROPIC_API_KEY` set as an environment variable.
- Deploy `/frontend` as a static site: root directory `frontend`, build `npm install && npm run build`, publish directory `dist`. Update `BASE` in `frontend/src/api.js` to the deployed backend's URL before building.
