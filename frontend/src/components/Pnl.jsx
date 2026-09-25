import { useEffect, useState } from "react";
import { api } from "../api";
import { fmt } from "../format";

const ROWS = [
  ["Revenue", "revenue"],
  ["Cost of Goods Sold", "cogs"],
  ["Gross Profit", "gross_profit"],
  ["Payroll", "payroll"],
  ["Operating Expenses", "opex"],
  ["Operating Profit", "operating_profit"],
  ["Excluded (non-P&L / unknown)", "excluded"],
];

export default function Pnl({ refreshKey, onGoMonth }) {
  const [pnl, setPnl] = useState([]);
  const [check, setCheck] = useState(null);

  useEffect(() => {
    api.get("/api/pnl").then(setPnl);
    api.get("/api/check").then(setCheck);
  }, [refreshKey]);

  return (
    <section>
      <h2>Monthly P&amp;L</h2>
      <table>
        <thead>
          <tr>
            <th></th>
            {pnl.map((m) => (
              <th key={m.month}>
                <a href="#" onClick={(e) => { e.preventDefault(); onGoMonth(m.month); }}>{m.month}</a>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {ROWS.map(([label, key]) => (
            <tr key={key} className={key.includes("profit") ? "bold" : ""}>
              <td>{label}</td>
              {pnl.map((m) => <td key={m.month} className="num">{fmt(m[key])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
      {check && (
        <p>
          {check.ok ? "✔ Reconciled: " : "✘ Mismatch: "}
          all transactions = {fmt(check.transactions_total)}, P&amp;L + excluded = {fmt(check.pnl_plus_excluded)}
        </p>
      )}
      <small>Click a month to see its transactions. Non-P&amp;L items are excluded.</small>
    </section>
  );
}
