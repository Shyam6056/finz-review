import { useEffect, useState, useCallback } from "react";
import { api } from "../api";
import TxTable from "./TxTable";

export default function Review({ categories, refreshKey }) {
  const [rows, setRows] = useState([]);

  const load = useCallback(async () => {
    setRows(await api.get("/api/transactions?review=1"));
  }, []);

  useEffect(() => { load(); }, [load, refreshKey]);

  return (
    <section>
      <h2>Items needing review</h2>
      {rows.length ? <TxTable rows={rows} categories={categories} onChanged={load} /> : <p>Nothing to review.</p>}
    </section>
  );
}
