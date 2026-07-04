import { useEffect, useRef, useState } from "react";
import Topbar from "../components/Layout/Topbar.jsx";
import { api } from "../api/client.js";

const SUGGESTIONS = [
  "What does T1110 (Brute Force) mean and how would I detect it?",
  "Summarize the risk of the most recent scenario run.",
  "How should I harden this VM against the user_management scenario?",
];

export default function Copilot() {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text:
        "I'm the PurpleLab AI Security Copilot. Ask me about any MITRE technique, scenario, or event - optionally scope me to a specific run below.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    api.listRuns().then(setRuns).catch(() => {});
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function send(text) {
    const question = (text ?? input).trim();
    if (!question || loading) return;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setLoading(true);
    try {
      const { answer } = await api.askCopilot(question, { runId: selectedRun || undefined });
      setMessages((m) => [...m, { role: "assistant", text: answer }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", text: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-screen flex flex-col">
      <Topbar title="AI Security Copilot" subtitle="Ask questions about events, techniques, and scenarios" />
      <div className="px-8 py-3 flex items-center gap-3 border-b border-panel-border">
        <label className="text-sm text-ink-muted">Scope to run:</label>
        <select
          value={selectedRun}
          onChange={(e) => setSelectedRun(e.target.value)}
          className="bg-panel-raised border border-panel-border rounded-lg px-3 py-1.5 text-sm"
        >
          <option value="">General (no run context)</option>
          {runs.map((r) => (
            <option key={r.id} value={r.id}>
              {r.scenario_name} — {new Date(r.started_at).toLocaleString()}
            </option>
          ))}
        </select>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-8 py-6 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-2xl rounded-xl px-4 py-3 text-sm whitespace-pre-wrap ${
                m.role === "user"
                  ? "bg-purple-dim/40 border border-purple/40"
                  : "panel"
              }`}
            >
              {m.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="panel px-4 py-3 text-sm text-ink-muted mono">Thinking…</div>
          </div>
        )}
      </div>

      <div className="px-8 py-4 border-t border-panel-border">
        <div className="flex gap-2 mb-3 flex-wrap">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="text-xs px-3 py-1.5 rounded-full border border-panel-border text-ink-muted hover:border-purple/50 hover:text-ink transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
          className="flex gap-3"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the Security Copilot…"
            className="flex-1 bg-panel-raised border border-panel-border rounded-lg px-4 py-2.5 text-sm focus:border-purple/60"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-red-team/80 to-blue-team/80 text-void font-medium text-sm disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
