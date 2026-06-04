import { useState, useEffect, useCallback } from "react";

const BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/+$/, "");
const api = (path) => `${BASE}${path.startsWith("/") ? path : "/" + path}`;

function StatusDot({ ok }) {
  return (
    <span
      className={`inline-block w-3 h-3 rounded-full ${ok ? "bg-green-500" : "bg-red-500"} mr-2`}
    />
  );
}

function Field({ label, value }) {
  if (!value) return null;
  const conf = ((value.confidence || 0) * 100).toFixed(0);
  return (
    <div className="flex gap-4 text-sm py-0.5 border-b border-gray-100 last:border-0">
      <span className="w-32 shrink-0 text-gray-500 font-medium">{label}</span>
      <span className="text-gray-900 break-words flex-1">{value.value}</span>
      <span className="w-20 shrink-0 text-right text-gray-400 text-xs leading-5">
        {conf}%
      </span>
    </div>
  );
}

function Card({ title, children, accent }) {
  const border = accent ? `border-l-4 border-l-${accent}-500` : "";
  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden ${border}`}>
      <div className="px-5 py-3 bg-gray-50 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-800 tracking-wide">{title}</h3>
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function Empty({ text }) {
  return <p className="text-sm text-gray-400 italic">{text}</p>;
}

function Section({ title, children }) {
  return (
    <div>
      <h2 className="text-lg font-bold text-gray-800 mb-3">{title}</h2>
      {children}
    </div>
  );
}

function MatchRow({ m }) {
  const bar = Math.min(m.score, 100);
  const color =
    bar >= 40 ? "bg-green-500" : bar >= 20 ? "bg-amber-500" : "bg-gray-400";
  return (
    <div className="flex items-center gap-3 py-1.5 text-sm border-b border-gray-100 last:border-0">
      <div className="w-8 shrink-0 text-right font-mono font-bold text-gray-500">
        {m.score.toFixed(0)}
      </div>
      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden shrink-0">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${bar}%` }} />
      </div>
      <span className="text-gray-900 font-medium truncate">{m.label}</span>
      <span
        className={`ml-auto text-xs px-2 py-0.5 rounded-full shrink-0 ${
          m.source_type === "tonnage"
            ? "bg-blue-100 text-blue-700"
            : m.source_type === "tc_fixture"
              ? "bg-purple-100 text-purple-700"
              : "bg-gray-100 text-gray-600"
        }`}
      >
        {m.source_type}
      </span>
      <span className="text-xs text-gray-400">→</span>
      <span
        className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${
          m.target_type === "vc_cargo"
            ? "bg-amber-100 text-amber-700"
            : m.target_type === "tc_fixture"
              ? "bg-purple-100 text-purple-700"
              : "bg-gray-100 text-gray-600"
        }`}
      >
        {m.target_type}
      </span>
    </div>
  );
}

function ResultPane({ data }) {
  const hasVessels = data.vessels && data.vessels.length > 0;
  const hasCargoes = data.cargoes && data.cargoes.length > 0;
  const hasTc = data.tc_fixtures && data.tc_fixtures.length > 0;
  const hasMatches = data.matches && data.matches.length > 0;

  return (
    <div className="space-y-6">
      {/* classification badge */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-500">Classification:</span>
        <span className="text-sm font-bold px-3 py-1 rounded-full bg-indigo-100 text-indigo-800">
          {data.classification || "—"}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* vessels */}
        <Section title={`Vessels (${data.vessels?.length || 0})`}>
          {hasVessels ? (
            <div className="space-y-3">
              {data.vessels.map((v, i) => (
                <Card key={i} title={`#${i + 1}`} accent="blue">
                  <Field label="Vessel" value={v.vessel_name} />
                  <Field label="Account" value={v.account_name} />
                  <Field label="Open Port" value={v.open_port} />
                  <Field label="Open Date" value={v.open_date} />
                  <Field label="Type" value={v.vessel_type} />
                  <Field label="DWT" value={v.vessel_size_dwt} />
                </Card>
              ))}
            </div>
          ) : (
            <Empty text="No vessels extracted" />
          )}
        </Section>

        {/* VC cargoes */}
        <Section title={`Cargoes (${data.cargoes?.length || 0})`}>
          {hasCargoes ? (
            <div className="space-y-3">
              {data.cargoes.map((c, i) => (
                <Card key={i} title={`#${i + 1}`} accent="amber">
                  <Field label="Account" value={c.account_name} />
                  <Field label="Cargo" value={c.cargo_name} />
                  <Field label="Loading Port" value={c.loading_port} />
                  <Field label="Discharge Port" value={c.discharge_port} />
                  <Field label="Laycan" value={c.laycan} />
                  <Field label="Type" value={c.cargo_type} />
                  <Field label="Qty Min" value={c.quantity_min_mt} />
                  <Field label="Qty Max" value={c.quantity_max_mt} />
                  <Field label="Load Rate" value={c.load_rate} />
                  <Field label="Disch Rate" value={c.discharge_rate} />
                  <Field label="Commission" value={c.commission_pct} />
                </Card>
              ))}
            </div>
          ) : (
            <Empty text="No cargoes extracted" />
          )}
        </Section>
      </div>

      {/* TC fixtures */}
      <Section title={`TC Fixtures (${data.tc_fixtures?.length || 0})`}>
        {hasTc ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {data.tc_fixtures.map((t, i) => (
              <Card key={i} title={`#${i + 1}`} accent="purple">
                <Field label="Account" value={t.account_name} />
                <Field label="Vessel" value={t.vessel_name} />
                <Field label="Delivery Port" value={t.delivery_port} />
                <Field label="Delivery Date" value={t.delivery_date} />
                <Field label="Redelivery Port" value={t.redelivery_port} />
                <Field label="Redelivery Date" value={t.redelivery_date} />
                <Field label="Charter Period" value={t.charter_period} />
                <Field label="Hire Rate" value={t.hire_rate} />
                <Field label="Commission" value={t.commission_pct} />
                <Field label="Intended Cargo" value={t.intended_cargo} />
                <Field label="Vessel DWT" value={t.vessel_dwt} />
              </Card>
            ))}
          </div>
        ) : (
          <Empty text="No TC fixtures extracted" />
        )}
      </Section>

      {/* Matches */}
      <Section title={`Matches (${data.matches?.length || 0})`}>
        {hasMatches ? (
          <Card title="Ranked Opportunities">
            {data.matches.map((m, i) => (
              <MatchRow key={i} m={m} />
            ))}
          </Card>
        ) : (
          <Empty text="No matches found" />
        )}
      </Section>
    </div>
  );
}

function App() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetch(api("/health"))
      .then((r) => r.json())
      .then((d) => setHealth(d))
      .catch(() => setHealth(null));
  }, []);

  const handleExtract = useCallback(async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await fetch(api("/extract"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body_text: text, run_matching: true }),
      });
      if (!r.ok) {
        const err = await r.json();
        throw new Error(err.detail || `HTTP ${r.status}`);
      }
      setResult(await r.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [text]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900 tracking-tight">
              Email Segregator
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Shipping email extraction &amp; matching demo
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <StatusDot ok={health !== null} />
            <span className="text-gray-500">
              API {health ? "connected" : "offline"}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        {/* input area */}
        <Card title="Email Content">
          <textarea
            className="w-full h-48 border border-gray-300 rounded-lg p-4 text-sm font-mono text-gray-900 resize-y focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent"
            placeholder="Paste email content here..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <div className="flex items-center gap-3 mt-4">
            <button
              onClick={handleExtract}
              disabled={loading || !text.trim()}
              className="px-6 py-2.5 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? "Extracting..." : "Extract"}
            </button>
            {text.trim() && (
              <span className="text-xs text-gray-400">
                {(text.length / 1024).toFixed(1)} KB
              </span>
            )}
          </div>
        </Card>

        {/* error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg px-5 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* results */}
        {result && <ResultPane data={result} />}
      </main>

      {/* quick samples */}
      <QuickSamples onSelect={setText} />
    </div>
  );
}

const SAMPLES = [
  {
    label: "Tonnage",
    text: `MV SHENG AN HAI DWT 56564 OPEN XIAMEN, CHINA O/A 2ND JUNE 2026
MV FENG HUI HAI DWT 63260 OPEN GUANGZHOU, CHINA O/A 6TH JUNE 2026`,
  },
  {
    label: "VC Cargo",
    text: `15,000 - 20,000 MTS 10PCT MOLOCHOPT
LOAD PORT: KOH SI CHANG, THAILAND
DISCHARGE PORT: KANDLA + CHENNAI
LAY CAN: MID JULY 2026
COM: 3.75 PCT TTL`,
  },
  {
    label: "TC Fixture",
    text: `ACC DAI AN OCEAN SHIPPING COMPANY LIMITED
DELIVERY TM VANCOUVER
LC 10-17 JUNE
1 TCT WITH GRAINS
REDELIVERY CHITTAGONG
3.75 ADDCOM PUS`,
  },
];

function QuickSamples({ onSelect }) {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-inner">
      <div className="max-w-6xl mx-auto px-6 py-3 flex items-center gap-3">
        <span className="text-xs text-gray-400 shrink-0">Quick fill:</span>
        {SAMPLES.map((s) => (
          <button
            key={s.label}
            onClick={() => onSelect(s.text)}
            className="px-3 py-1.5 text-xs font-medium rounded-md bg-gray-100 text-gray-700 hover:bg-indigo-100 hover:text-indigo-700 transition-colors"
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default App;
