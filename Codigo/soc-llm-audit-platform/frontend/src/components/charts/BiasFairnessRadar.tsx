import { Box, Typography } from '@mui/material';

interface BiasData {
  dimension: string;
  score: number; // 0-100
  threshold: number;
  passed: boolean;
}

const defaultData: BiasData[] = [
  { dimension: 'Geographic', score: 85, threshold: 80, passed: true },
  { dimension: 'Temporal', score: 92, threshold: 80, passed: true },
  { dimension: 'Linguistic', score: 68, threshold: 80, passed: false },
  { dimension: 'Severity', score: 88, threshold: 80, passed: true },
  { dimension: 'Source', score: 78, threshold: 80, passed: false },
];

interface Props {
  data?: BiasData[];
}

export default function BiasFairnessRadar({ data = defaultData }: Props) {
  const cx = 150;
  const cy = 130;
  const maxR = 100;
  const levels = [20, 40, 60, 80, 100];
  const n = data.length;
  const angleStep = (2 * Math.PI) / n;

  const getPoint = (index: number, value: number) => {
    const angle = -Math.PI / 2 + index * angleStep;
    const r = (value / 100) * maxR;
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  };

  const dataPoints = data.map((d, i) => getPoint(i, d.score));
  const dataPath = dataPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z';

  const thresholdPoints = data.map((d, i) => getPoint(i, d.threshold));
  const thresholdPath = thresholdPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z';

  return (
    <Box sx={{ py: 1 }}>
      <Box sx={{ display: 'flex', gap: 2 }}>
        {/* Radar chart */}
        <svg width="300" height="270" viewBox="0 0 300 270">
          {/* Level circles */}
          {levels.map((level) => {
            const r = (level / 100) * maxR;
            return (
              <circle key={level} cx={cx} cy={cy} r={r}
                fill="none" stroke="#333" strokeWidth={0.5} />
            );
          })}
          {/* Axis lines */}
          {data.map((_, i) => {
            const endPoint = getPoint(i, 100);
            return (
              <line key={i} x1={cx} y1={cy} x2={endPoint.x} y2={endPoint.y}
                stroke="#444" strokeWidth={0.5} />
            );
          })}
          {/* Threshold polygon */}
          <path d={thresholdPath} fill="none" stroke="#ffa726" strokeWidth={1.5} strokeDasharray="4 2" />
          {/* Data polygon */}
          <path d={dataPath} fill="#29b6f633" stroke="#29b6f6" strokeWidth={2} />
          {/* Data points */}
          {dataPoints.map((p, i) => (
            <circle key={i} cx={p.x} cy={p.y} r={4}
              fill={data[i].passed ? '#66bb6a' : '#ef5350'} stroke="white" strokeWidth={1} />
          ))}
          {/* Labels */}
          {data.map((d, i) => {
            const labelPoint = getPoint(i, 118);
            return (
              <text key={i} x={labelPoint.x} y={labelPoint.y}
                fill={d.passed ? '#66bb6a' : '#ef5350'}
                fontSize={9} textAnchor="middle" fontWeight="bold">
                {d.dimension}
              </text>
            );
          })}
        </svg>
        {/* Bar distribution */}
        <Box sx={{ flex: 1, pt: 1 }}>
          {data.map((d) => (
            <Box key={d.dimension} sx={{ mb: 1.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.3 }}>
                <Typography variant="caption" sx={{ fontSize: 10 }}>{d.dimension}</Typography>
                <Typography variant="caption" sx={{ fontSize: 10, color: d.passed ? '#66bb6a' : '#ef5350', fontWeight: 700 }}>
                  {d.score}%
                </Typography>
              </Box>
              <Box sx={{ height: 8, bgcolor: '#333', borderRadius: 1, position: 'relative' }}>
                <Box sx={{
                  height: '100%', width: `${d.score}%`,
                  bgcolor: d.passed ? '#66bb6a' : '#ef5350',
                  borderRadius: 1,
                }} />
                <Box sx={{
                  position: 'absolute', top: -2, left: `${d.threshold}%`,
                  width: 2, height: 12, bgcolor: '#ffa726',
                }} />
              </Box>
            </Box>
          ))}
        </Box>
      </Box>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
        AI Act Art.10/13 — Radar 5 dimensiones + distribución por grupo (umbral naranja)
      </Typography>
    </Box>
  );
}
