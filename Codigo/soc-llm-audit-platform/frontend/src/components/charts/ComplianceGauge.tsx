import { Box, Typography } from '@mui/material';

interface Props {
  score: number;
}

export default function ComplianceGauge({ score }: Props) {
  const radius = 80;
  const circumference = Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 90 ? '#66bb6a' : score >= 70 ? '#29b6f6' : score >= 50 ? '#ffa726' : '#ef5350';

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 2 }}>
      <svg width="200" height="120" viewBox="0 0 200 120">
        <path
          d="M 10 110 A 80 80 0 0 1 190 110"
          fill="none" stroke="#333" strokeWidth="16" strokeLinecap="round"
        />
        <path
          d="M 10 110 A 80 80 0 0 1 190 110"
          fill="none" stroke={color} strokeWidth="16" strokeLinecap="round"
          strokeDasharray={`${circumference}`}
          strokeDashoffset={offset}
        />
        <text x="100" y="100" textAnchor="middle" fill="white" fontSize="28" fontWeight="bold">
          {score.toFixed(1)}
        </text>
        <text x="100" y="115" textAnchor="middle" fill="#999" fontSize="10">
          / 100
        </text>
      </svg>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
        CS = Σ(wi × si)
      </Typography>
    </Box>
  );
}
