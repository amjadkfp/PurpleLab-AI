import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useEdgesState,
  useNodesState,
} from "reactflow";
import "reactflow/dist/style.css";
import Topbar from "../components/Layout/Topbar.jsx";
import { api } from "../api/client.js";

function CustomNode({ data }) {
  return (
    <div
      className="px-4 py-3 rounded-lg border-2 min-w-[220px]"
      style={{ borderColor: data.color, background: "#12121F" }}
    >
      <p className="text-sm font-medium text-ink">{data.label}</p>
      <p className="mono text-xs mt-1" style={{ color: data.color }}>
        {data.subtitle}
      </p>
      {data.actor && (
        <p className="text-[10px] text-ink-muted mt-1 uppercase mono">{data.actor}</p>
      )}
    </div>
  );
}

const nodeTypes = { default: CustomNode };

export default function AttackFlowGraph() {
  const [params] = useSearchParams();
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(params.get("run_id") || "");
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.listRuns().then(setRuns).catch(() => {});
  }, []);

  const load = useCallback(async (runId) => {
    if (!runId) return;
    try {
      const graph = await api.getAttackGraph(runId);
      setNodes(
        graph.nodes.map((n) => ({
          ...n,
          position: { x: 40, y: n.position.y },
          style: { width: 260 },
        }))
      );
      setEdges(
        graph.edges.map((e) => ({
          ...e,
          style: { stroke: "#8B5CF6", strokeWidth: 2 },
          labelStyle: { fill: "#A78BFA", fontSize: 11 },
        }))
      );
    } catch (e) {
      setError(e.message);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    load(selectedRun);
  }, [selectedRun, load]);

  return (
    <div className="h-screen flex flex-col">
      <Topbar
        title="Attack Flow Graph"
        subtitle="Interactive, step-by-step visualization of a scenario's execution chain"
      />
      <div className="px-8 py-4 flex items-center gap-3">
        <label className="text-sm text-ink-muted">Run:</label>
        <select
          value={selectedRun}
          onChange={(e) => setSelectedRun(e.target.value)}
          className="bg-panel-raised border border-panel-border rounded-lg px-3 py-1.5 text-sm"
        >
          <option value="">Select a run…</option>
          {runs.map((r) => (
            <option key={r.id} value={r.id}>
              {r.scenario_name} — {new Date(r.started_at).toLocaleString()}
            </option>
          ))}
        </select>
        {error && <span className="text-red-team text-sm">{error}</span>}
      </div>
      <div className="flex-1">
        {nodes.length === 0 ? (
          <p className="px-8 text-sm text-ink-muted">
            Select a run to render its attack flow graph.
          </p>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#26263D" gap={24} />
            <Controls />
            <MiniMap
              nodeColor={() => "#8B5CF6"}
              maskColor="rgba(10,10,18,0.8)"
              style={{ background: "#12121F" }}
            />
          </ReactFlow>
        )}
      </div>
    </div>
  );
}
