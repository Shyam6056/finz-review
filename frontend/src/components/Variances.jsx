import { useEffect, useState } from "react";
import { api } from "../api";
import { fmt, LABEL } from "../format";

export default function Variances({ refreshKey }) {
  const [vars, setVars] = useState([]);
  const [explain, setExplain] = useState({});

  useEffect(() => { api.get("/api/variances").then(setVars); }, [refreshKey]);

  async function runExplain(i, v) {
    setExplain((s) => ({ ...s, [i]: "Thinking..." }));
    const r = await api.post("/api/chat", {
      question: `Explain why ${LABEL[v.line]} changed from ${v.from} to ${v.to}.`,
      history: [],
    });
    setExplain((s) => ({ ...s, [i]: r.answer }));
  }

  if (!vars.length) return <section><h2>Material variances</h2><p>No material variances yet. Upload data first.</p></section>;

  return (
    <section>
      <h2>Material variances</h2>
      {vars.map((x, i) => (
        <div className="card" key={i}>
          <b>{LABEL[x.line]}</b>: {x.from} → {x.to}: {fmt(x.before)} → {fmt(x.after)}{" "}
          ({x.change >= 0 ? "+" : ""}{fmt(x.change)}{x.pct !== null ? `, ${x.pct}%` : ""})
          <ul>
            {x.drivers.map((d, j) =>
              d.type === "line" ? (
                <li key={j}>{LABEL[d.name]} effect on profit: {fmt(d.impact)}</li>
              ) : (
                <li key={j}>
                  {d.name}: {fmt(d.change)}
                  <br />
                  <small>
                    {d.transactions.map((t) => `#${t.id} ${t.date} ${t.description} ${fmt(t.amount)}`).join(" | ")}
                  </small>
                </li>
              )
            )}
          </ul>
          <button onClick={() => runExplain(i, x)}>Explain with AI</button>
          <div className="pre">{explain[i]}</div>
        </div>
      ))}
    </section>
  );
}
