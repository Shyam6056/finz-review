import { fmt } from "../format";
import { api } from "../api";

export default function TxTable({ rows, categories, onChanged }) {
  async function fix(id, category) {
    await api.patch(`/api/transactions/${id}`, { category });
    onChanged();
  }
  async function approve(id) {
    await api.post(`/api/transactions/${id}/resolve`, {});
    onChanged();
  }

  return (
    <table>
      <thead>
        <tr>
          <th>ID</th><th>Date</th><th>Description</th><th>Amount</th>
          <th>Category</th><th>Source</th><th>Review</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id} className={r.needs_review ? "flag" : ""}>
            <td>{r.id}</td>
            <td>{r.date}</td>
            <td>{r.description}</td>
            <td className="num">{fmt(r.amount)}</td>
            <td>
              <select value={r.category} onChange={(e) => fix(r.id, e.target.value)}>
                {categories.map((c) => (
                  <option key={c.name} value={c.name}>{c.name}</option>
                ))}
              </select>
            </td>
            <td>{r.source} {Math.round(r.confidence * 100)}%</td>
            <td>
              {r.needs_review ? (
                <>
                  {r.review_reason} <button onClick={() => approve(r.id)}>Approve</button>
                </>
              ) : ""}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
