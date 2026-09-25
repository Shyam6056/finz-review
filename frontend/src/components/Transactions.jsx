import { useEffect, useState, useCallback } from "react";
import { api } from "../api";
import TxTable from "./TxTable";

export default function Transactions({ categories, months, refreshKey, presetMonth }) {
  const [month, setMonth] = useState(presetMonth || "");
  const [category, setCategory] = useState("");
  const [reviewOnly, setReviewOnly] = useState(false);
  const [rows, setRows] = useState([]);

  useEffect(() => { if (presetMonth) setMonth(presetMonth); }, [presetMonth]);

  const load = useCallback(async () => {
    const q = new URLSearchParams({ month, category, review: reviewOnly ? 1 : 0 });
    setRows(await api.get("/api/transactions?" + q));
  }, [month, category, reviewOnly]);

  useEffect(() => { load(); }, [load, refreshKey]);

  return (
    <section>
      <h2>Transactions</h2>
      <select value={month} onChange={(e) => setMonth(e.target.value)}>
        <option value="">All months</option>
        {months.map((m) => <option key={m} value={m}>{m}</option>)}
      </select>{" "}
      <select value={category} onChange={(e) => setCategory(e.target.value)}>
        <option value="">All categories</option>
        {categories.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
      </select>{" "}
      <label>
        <input type="checkbox" checked={reviewOnly} onChange={(e) => setReviewOnly(e.target.checked)} /> Only needs review
      </label>
      <div style={{ marginTop: 10 }}>
        <TxTable rows={rows} categories={categories} onChanged={load} />
      </div>
    </section>
  );
}
