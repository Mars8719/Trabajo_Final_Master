import { Box, Typography } from '@mui/material';

interface Agent {
  id: string;
  name: string;
  compliance: number; // 0-100
  x: number;
  y: number;
}

interface Edge {
  from: string;
  to: string;
  latency: number; // ms
}

const defaultAgents: Agent[] = [
  { id: 'coordinator', name: 'Coordinator', compliance: 95, x: 200, y: 30 },
  { id: 'triage', name: 'TriageAgent', compliance: 92, x: 80, y: 120 },
  { id: 'detector', name: 'DetectorAgent', compliance: 88, x: 200, y: 180 },
  { id: 'responder', name: 'ResponderAgent', compliance: 78, x: 320, y: 120 },
  { id: 'ethical_gate', name: 'EthicalGate', compliance: 99, x: 200, y: 100 },
];

const defaultEdges: Edge[] = [
  { from: 'coordinator', to: 'ethical_gate', latency: 12 },
  { from: 'ethical_gate', to: 'triage', latency: 45 },
  { from: 'ethical_gate', to: 'detector', latency: 38 },
  { from: 'ethical_gate', to: 'responder', latency: 52 },
  { from: 'triage', to: 'detector', latency: 23 },
  { from: 'detector', to: 'responder', latency: 31 },
];

function getNodeColor(compliance: number): string {
  if (compliance >= 90) return '#66bb6a';
  if (compliance >= 70) return '#ffa726';
  if (compliance >= 50) return '#ef5350';
  return '#b71c1c';
}

interface Props {
  agents?: Agent[];
  edges?: Edge[];
}

export default function AgentExecutionTrace({ agents = defaultAgents, edges = defaultEdges }: Props) {
  const getAgent = (id: string) => agents.find((a) => a.id === id);

  return (
    <Box sx={{ py: 1 }}>
      <svg width="100%" height="220" viewBox="0 0 400 220">
        {/* Edges */}
        {edges.map((edge, i) => {
          const from = getAgent(edge.from);
          const to = getAgent(edge.to);
          if (!from || !to) return null;
          const midX = (from.x + to.x) / 2;
          const midY = (from.y + to.y) / 2;
          return (
            <g key={i}>
              <line
                x1={from.x} y1={from.y} x2={to.x} y2={to.y}
                stroke="#555" strokeWidth={1.5} strokeDasharray="4,2"
              />
              <text x={midX} y={midY - 5} fill="#999" fontSize={8} textAnchor="middle">
                {edge.latency}ms
              </text>
            </g>
          );
        })}
        {/* Nodes */}
        {agents.map((agent) => (
          <g key={agent.id}>
            <circle
              cx={agent.x} cy={agent.y} r={18}
              fill={getNodeColor(agent.compliance) + '33'}
              stroke={getNodeColor(agent.compliance)}
              strokeWidth={2}
            />
            <text x={agent.x} y={agent.y + 3} fill="white" fontSize={8} textAnchor="middle" fontWeight="bold">
              {agent.compliance}
            </text>
            <text x={agent.x} y={agent.y + 32} fill="#ccc" fontSize={9} textAnchor="middle">
              {agent.name}
            </text>
          </g>
        ))}
      </svg>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
        NIS2 Art.21 / AI Act — Nodos coloreados por compliance, aristas = latencia
      </Typography>
    </Box>
  );
}
