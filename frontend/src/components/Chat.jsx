import { useState, useRef } from "react";
import { api } from "../api";

export default function Chat() {
  const [msgs, setMsgs] = useState([]);
  const [q, setQ] = useState("");
  const histRef = useRef([]);

  async function send() {
    const question = q.trim();
    if (!question) return;
    setQ("");
    setMsgs((m) => [...m, { role: "you", text: question }]);
    setMsgs((m) => [...m, { role: "ai", text: "Thinking...", pending: true }]);
    try {
      const r = await api.post("/api/chat", { question, history: histRef.current });
      histRef.current = [...histRef.current,
        { role: "user", content: question },
        { role: "assistant", content: r.answer }];
      setMsgs((m) => {
        const copy = [...m];
        copy[copy.length - 1] = { role: "ai", text: r.answer, evidence: r.evidence };
        return copy;
      });
    } catch (e) {
      setMsgs((m) => {
        const copy = [...m];
        copy[copy.length - 1] = { role: "ai", text: "Error: " + e.message };
        return copy;
      });
    }
  }

  return (
    <section>
      <h2>AI analyst</h2>
      <div className="msgs">
        {msgs.map((m, i) => (
          <div key={i} className={m.role === "you" ? "you" : "ai"}>
            {m.text}
            {m.evidence && m.evidence.length > 0 && (
              <details>
                <summary>Evidence ({m.evidence.length} tool calls)</summary>
                <pre style={{ overflow: "auto", maxHeight: 250 }}>
                  {JSON.stringify(m.evidence, null, 1)}
                </pre>
              </details>
            )}
          </div>
        ))}
      </div>
      <input
        type="text"
        value={q}
        placeholder="e.g. Why did operating profit change between February and March?"
        onChange={(e) => setQ(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && send()}
      />{" "}
      <button onClick={send}>Ask</button>
    </section>
  );
}
