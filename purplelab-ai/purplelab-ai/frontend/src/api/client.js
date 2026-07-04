/**
 * api/client.js
 * ==============
 * Thin fetch wrapper for the PurpleLab AI backend. Every dashboard module
 * imports its endpoints from here rather than calling fetch() ad hoc.
 */
const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* no-op */
    }
    throw new Error(detail);
  }
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return res.json();
  return res.text();
}

export const api = {
  health: () => request("/health"),

  // Scenario Manager
  listScenarios: () => request("/scenarios"),
  runScenario: (scenario_key) =>
    request("/scenarios/run", { method: "POST", body: JSON.stringify({ scenario_key }) }),
  listRuns: () => request("/scenarios/runs"),
  getRun: (runId) => request(`/scenarios/runs/${runId}`),

  // Timeline / Log Viewer / Attack Graph
  listEvents: (params = {}) => request(`/events?${new URLSearchParams(params)}`),
  listLogEvents: (params = {}) => request(`/events/logs?${new URLSearchParams(params)}`),
  getAttackGraph: (runId) => request(`/events/graph/${runId}`),

  // MITRE Mapping
  listTechniques: () => request("/mitre/techniques"),
  observedTechniques: () => request("/mitre/observed"),

  // AI Security Copilot
  askCopilot: (question, { runId, eventId } = {}) =>
    request("/copilot/ask", {
      method: "POST",
      body: JSON.stringify({ question, run_id: runId, event_id: eventId }),
    }),

  // Reports
  generateReport: (runId, format = "html") =>
    request(`/reports/${runId}/generate?format=${format}`, { method: "POST" }),
  listReports: () => request("/reports"),

  // Analytics
  analyticsSummary: () => request("/analytics/summary"),
};
