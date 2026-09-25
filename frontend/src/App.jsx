import { useEffect, useState, useCallback } from "react";
import { api } from "./api";
import Upload from "./components/Upload";
import Transactions from "./components/Transactions";
import Pnl from "./components/Pnl";
import Variances from "./components/Variances";
import Review from "./components/Review";
import Chat from "./components/Chat";

const TABS = ["upload", "transactions", "pnl", "variances", "review", "chat"];

export default function App() {
  const [tab, setTab] = useState("upload");
  const [categories, setCategories] = useState([]);
  const [months, setMonths] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);
  const [presetMonth, setPresetMonth] = useState("");

  const loadMeta = useCallback(async () => {
    setCategories(await api.get("/api/categories"));
    const pnl = await api.get("/api/pnl");
    setMonths(pnl.map((m) => m.month));
  }, []);

  useEffect(() => { loadMeta(); }, [loadMeta]);

  function refreshAll() {
    setRefreshKey((k) => k + 1);
    loadMeta();
  }

  function goMonth(m) {
    setPresetMonth(m);
    setTab("transactions");
  }

  return (
    <>
      <header>
        <b>Finz Financial Review</b>
        <nav>
          {TABS.map((t) => (
            <button key={t} className={tab === t ? "on" : ""} onClick={() => setTab(t)}>
              {t}
            </button>
          ))}
        </nav>
      </header>
      <main>
        {tab === "upload" && <Upload onDone={refreshAll} />}
        {tab === "transactions" && (
          <Transactions categories={categories} months={months} refreshKey={refreshKey} presetMonth={presetMonth} />
        )}
        {tab === "pnl" && <Pnl refreshKey={refreshKey} onGoMonth={goMonth} />}
        {tab === "variances" && <Variances refreshKey={refreshKey} />}
        {tab === "review" && <Review categories={categories} refreshKey={refreshKey} />}
        {tab === "chat" && <Chat />}
      </main>
    </>
  );
}
