import { useState } from "react";
import { api } from "../api";

export default function Upload({ onDone }) {
  const [file, setFile] = useState(null);
  const [msg, setMsg] = useState("");

  async function handleUpload() {
    if (!file) return alert("Choose a file first");
    setMsg("Uploading and categorizing... this can take a minute.");
    try {
      const r = await api.upload("/api/upload", file);
      setMsg(`Done: ${r.saved} transactions saved, ${r.skipped} skipped, ${r.needs_review} need review.`);
      onDone();
    } catch (e) {
      setMsg("Error: " + e.message);
    }
  }

  return (
    <section>
      <h2>1. Upload bank transactions</h2>
      <input type="file" accept=".csv,.xlsx,.xls" onChange={(e) => setFile(e.target.files[0])} />{" "}
      <button onClick={handleUpload}>Upload</button>
      <p>{msg}</p>
    </section>
  );
}
