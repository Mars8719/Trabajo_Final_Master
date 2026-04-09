import { useEffect, useState } from 'react';
import { Box } from '@mui/material';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine,
} from 'recharts';
import { complianceApi } from '../../services/api';

const fallbackData = [
  { date: '25/03', score: 84, gdpr: 86, nis2: 82, bias: 88 },
  { date: '26/03', score: 86, gdpr: 88, nis2: 84, bias: 87 },
  { date: '27/03', score: 85, gdpr: 87, nis2: 83, bias: 86 },
  { date: '28/03', score: 88, gdpr: 90, nis2: 86, bias: 89 },
  { date: '29/03', score: 87, gdpr: 89, nis2: 85, bias: 88 },
  { date: '30/03', score: 89, gdpr: 91, nis2: 87, bias: 90 },
  { date: '31/03', score: 87, gdpr: 89, nis2: 85, bias: 88 },
];

export default function TrendLine() {
  const [data, setData] = useState(fallbackData);

  useEffect(() => {
    complianceApi.getTrends()
      .then((res) => {
        if (res.data && res.data.length > 0) setData(res.data);
      })
      .catch(() => {});
  }, []);

  return (
    <Box sx={{ width: '100%', height: 250 }}>
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="date" stroke="#999" fontSize={10} />
          <YAxis domain={[0, 100]} stroke="#999" fontSize={10} />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e1e1e', border: '1px solid #333' }}
          />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <Line type="monotone" dataKey="gdpr" name="GDPR" stroke="#66bb6a" strokeWidth={2} dot={{ r: 3 }} />
          <Line type="monotone" dataKey="nis2" name="NIS2" stroke="#29b6f6" strokeWidth={2} dot={{ r: 3 }} />
          <Line type="monotone" dataKey="bias" name="Bias/AI Act" stroke="#ce93d8" strokeWidth={2} dot={{ r: 3 }} />
          {/* Threshold bands */}
          <ReferenceLine y={85} stroke="#66bb6a" strokeDasharray="3 3" strokeWidth={0.5} />
          <ReferenceLine y={60} stroke="#ffa726" strokeDasharray="3 3" strokeWidth={0.5} />
          <ReferenceLine y={40} stroke="#ef5350" strokeDasharray="3 3" strokeWidth={0.5} />
        </LineChart>
      </ResponsiveContainer>
    </Box>
  );
}
