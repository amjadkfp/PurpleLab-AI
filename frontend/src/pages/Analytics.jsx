import { useEffect, useState } from "react";
import { Bar, Doughnut } from "react-chartjs-2";
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from "chart.js";
import Topbar from "../components/Layout/Topbar.jsx";
import { api } from "../api/client.js";

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

const CHART_TEXT_COLOR = "#8B8A9E";
const GRID_COLOR = "#26263D";

const commonOptions = {
  plugins: { legend: { labels: { color: CHART_TEXT_COLOR } } },
  scales: {
    x: { ticks: { color: CHART_TEXT_COLOR }, grid: { color: GRID_COLOR } },
    y: { ticks: { color: CHART_TEXT_COLOR }, grid: { color: GRID_COLOR } },
  },
};

export default function Analytics() {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    api.analyticsSummary().then(setSummary).catch(() => {});
  }, []);

  if (!summary) {
    return (
      <div>
        <Topbar title="Analytics" subtitle="Aggregate statistics across all scenario runs" />
        <p className="p-8 text-sm text-ink-muted">Loading analytics…</p>
      </div>
    );
  }

  const severityData = {
    labels: Object.keys(summary.event_severity_breakdown),
    datasets: [
      {
        data: Object.values(summary.event_severity_breakdown),
        backgroundColor: ["#F43F5E", "#FB923C", "#FBBF24", "#8B8A9E", "#5C5B70"],
        borderWidth: 0,
      },
    ],
  };

  const tacticData = {
    labels: Object.keys(summary.tactic_breakdown),
    datasets: [
      {
        label: "Events per tactic",
        data: Object.values(summary.tactic_breakdown),
        backgroundColor: "#8B5CF6",
        borderRadius: 4,
      },
    ],
  };

  const scenarioData = {
    labels: Object.keys(summary.runs_by_scenario),
    datasets: [
      {
        label: "Runs",
        data: Object.values(summary.runs_by_scenario),
        backgroundColor: "#22D3EE",
        borderRadius: 4,
      },
    ],
  };

  return (
    <div>
      <Topbar title="Analytics" subtitle="Aggregate statistics across all scenario runs" />
      <div className="p-8 grid md:grid-cols-2 gap-6">
        <div className="panel p-5">
          <h3 className="font-semibold mb-4">Event Severity Distribution</h3>
          <Doughnut data={severityData} options={{ plugins: commonOptions.plugins }} />
        </div>
        <div className="panel p-5">
          <h3 className="font-semibold mb-4">Events by MITRE Tactic</h3>
          <Bar data={tacticData} options={commonOptions} />
        </div>
        <div className="panel p-5 md:col-span-2">
          <h3 className="font-semibold mb-4">Runs by Scenario</h3>
          <Bar data={scenarioData} options={commonOptions} />
        </div>
      </div>
    </div>
  );
}
