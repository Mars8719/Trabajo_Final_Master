import { Box, Typography } from '@mui/material';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine,
} from 'recharts';

const fallbackData = [
  { hour: '00h', cost: 4.2, budget: 12.5 },
  { hour: '04h', cost: 3.1, budget: 12.5 },
  { hour: '08h', cost: 8.7, budget: 12.5 },
  { hour: '12h', cost: 11.3, budget: 12.5 },
  { hour: '16h', cost: 9.5, budget: 12.5 },
  { hour: '20h', cost: 6.8, budget: 12.5 },
  { hour: 'Now', cost: 7.2, budget: 12.5 },
];

interface DataPoint {
  hour: string;
  cost: number;
  budget: number;
}

interface Props {
  data?: DataPoint[];
  budgetLimit?: number;
}

export default function DoWMonitor({ data = fallbackData, budgetLimit = 12.5 }: Props) {
  return (
    <Box sx={{ py: 1 }}>
      <Box sx={{ width: '100%', height: 200 }}>
        <ResponsiveContainer>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="hour" stroke="#999" fontSize={10} />
            <YAxis stroke="#999" fontSize={10} unit="$" />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e1e1e', border: '1px solid #333' }}
              formatter={(value: number) => [`$${value.toFixed(2)}`, '']}
            />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="cost" name="Coste/hora" fill="#29b6f6" radius={[4, 4, 0, 0]} />
            <ReferenceLine
              y={budgetLimit}
              stroke="#ff1744"
              strokeDasharray="5 5"
              label={{ value: `Límite $${budgetLimit}`, fill: '#ff1744', fontSize: 10 }}
            />
            <ReferenceLine
              y={budgetLimit * 0.8}
              stroke="#ffa726"
              strokeDasharray="3 3"
              label={{ value: '80%', fill: '#ffa726', fontSize: 9 }}
            />
          </BarChart>
        </ResponsiveContainer>
      </Box>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
        OWASP LLM10 / NIS2 Art.21 — Coste por inferencia vs presupuesto
      </Typography>
    </Box>
  );
}
