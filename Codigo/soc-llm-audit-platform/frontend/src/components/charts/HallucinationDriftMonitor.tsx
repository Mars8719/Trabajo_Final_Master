import { Box, Typography } from '@mui/material';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

const fallbackData = [
  { time: '00:00', hallucination: 8, drift: 12 },
  { time: '04:00', hallucination: 6, drift: 11 },
  { time: '08:00', hallucination: 10, drift: 14 },
  { time: '12:00', hallucination: 12, drift: 13 },
  { time: '16:00', hallucination: 9, drift: 15 },
  { time: '20:00', hallucination: 14, drift: 18 },
  { time: '24:00', hallucination: 11, drift: 16 },
];

interface DataPoint {
  time: string;
  hallucination: number;
  drift: number;
}

interface Props {
  data?: DataPoint[];
}

export default function HallucinationDriftMonitor({ data = fallbackData }: Props) {
  return (
    <Box sx={{ py: 1 }}>
      <Box sx={{ width: '100%', height: 200 }}>
        <ResponsiveContainer>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="time" stroke="#999" fontSize={10} />
            <YAxis stroke="#999" fontSize={10} domain={[0, 30]} unit="%" />
            <Tooltip contentStyle={{ backgroundColor: '#1e1e1e', border: '1px solid #333' }} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Line
              type="monotone" dataKey="hallucination" name="Alucinación %"
              stroke="#ef5350" strokeWidth={2} dot={{ r: 3 }}
            />
            <Line
              type="monotone" dataKey="drift" name="Drift Score"
              stroke="#ffa726" strokeWidth={2} dot={{ r: 3 }}
            />
            {/* Threshold line at 15% */}
            <Line
              type="monotone" dataKey={() => 15} name="Umbral 15%"
              stroke="#ff1744" strokeWidth={1} strokeDasharray="5 5" dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </Box>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
        NIS2 / AI Act — Tasa alucinación + drift score en tiempo real
      </Typography>
    </Box>
  );
}
