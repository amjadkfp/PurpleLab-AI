import { Route, Routes } from "react-router-dom";
import Sidebar from "./components/Layout/Sidebar.jsx";
import DashboardHome from "./pages/DashboardHome.jsx";
import ScenarioManager from "./pages/ScenarioManager.jsx";
import TimelineViewer from "./pages/TimelineViewer.jsx";
import AttackFlowGraph from "./pages/AttackFlowGraph.jsx";
import Copilot from "./pages/Copilot.jsx";
import MitreMapping from "./pages/MitreMapping.jsx";
import LogViewer from "./pages/LogViewer.jsx";
import Analytics from "./pages/Analytics.jsx";
import Reports from "./pages/Reports.jsx";

export default function App() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 min-w-0">
        <Routes>
          <Route path="/" element={<DashboardHome />} />
          <Route path="/scenarios" element={<ScenarioManager />} />
          <Route path="/timeline" element={<TimelineViewer />} />
          <Route path="/attack-graph" element={<AttackFlowGraph />} />
          <Route path="/copilot" element={<Copilot />} />
          <Route path="/mitre" element={<MitreMapping />} />
          <Route path="/logs" element={<LogViewer />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/reports" element={<Reports />} />
        </Routes>
      </main>
    </div>
  );
}
