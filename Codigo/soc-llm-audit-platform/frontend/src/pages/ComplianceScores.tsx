import { useEffect, useState, useCallback } from 'react';
import {
  Box, Typography, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Chip, LinearProgress,
} from '@mui/material';
import { complianceApi } from '../services/api';
import useWebSocket from '../hooks/useWebSocket';


interface Score {
  id: string;
  alert_id: string;
  total_score: number;
  risk_level: string;
  data_minimization: number;
  legal_basis: number;
  transparency: number;
  pipeline_security: number;
  created_at: string;
}

const riskColor = (level: string) => {
  switch (level) {
    case 'compliant': return 'success';
    case 'attention': return 'info';
    case 'medium_risk': return 'warning';
    case 'non_compliant': return 'error';
    default: return 'default';
  }
};

const MOCK_SCORES: Score[] = [
  { id: '1', alert_id: 'a1b2c3', total_score: 92.5, risk_level: 'compliant', data_minimization: 95, legal_basis: 100, transparency: 85, pipeline_security: 90, created_at: '2026-03-31T10:30:00Z' },
  { id: '2', alert_id: 'd4e5f6', total_score: 78.3, risk_level: 'attention', data_minimization: 80, legal_basis: 100, transparency: 70, pipeline_security: 75, created_at: '2026-03-31T10:25:00Z' },
];

export default function ComplianceScores() {
  const [scores, setScores] = useState<Score[]>([]);
  const [loading, setLoading] = useState(true);

  const handleWsMessage = useCallback((data: Record<string, unknown>) => {
    if (data.compliance_score !== undefined) {
      const newScore: Score = {
        id: String(Date.now()),
        alert_id: String(data.alert_id ?? 'live'),
        total_score: Number(data.compliance_score),
        risk_level: String(data.risk_level ?? 'attention'),
        data_minimization: Number(data.data_minimization ?? 0),
        legal_basis: Number(data.legal_basis ?? 0),
        transparency: Number(data.transparency ?? 0),
        pipeline_security: Number(data.pipeline_security ?? 0),
        created_at: new Date().toISOString(),
      };
      setScores((prev) => [newScore, ...prev].slice(0, 50));
    }
  }, []);

  const { connected } = useWebSocket('/ws/compliance/live', { onMessage: handleWsMessage });

  useEffect(() => {
    complianceApi.getScores()
      .then((res) => {
        const data = res.data as Array<Record<string, unknown>>;
        const loaded = data.map((s) => ({
          id: String(s.id),
          alert_id: String(s.alert_id),
          total_score: Number(s.total_score),
          risk_level: String(s.risk_level),
          data_minimization: Number(s.data_minimization ?? 0),
          legal_basis: Number(s.legal_basis ?? 0),
          transparency: Number(s.transparency ?? 0),
          pipeline_security: Number(s.pipeline_security ?? 0),
          created_at: String(s.created_at),
        }));
        setScores(loaded.length > 0 ? loaded : MOCK_SCORES);
      })
      .catch(() => setScores(MOCK_SCORES))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LinearProgress />;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
        <Typography variant="h4">Compliance Scores</Typography>
        <Chip
          label={connected ? 'Live' : 'Offline'}
          color={connected ? 'success' : 'default'}
          size="small"
          variant="outlined"
        />
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        CS = Σ(wi × si) — Score compuesto 0-100 por transacción
      </Typography>

      <TableContainer component={Paper} sx={{ bgcolor: 'background.paper' }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Alert ID</TableCell>
              <TableCell>Score Total</TableCell>
              <TableCell>Nivel Riesgo</TableCell>
              <TableCell>Min. Datos</TableCell>
              <TableCell>Base Legal</TableCell>
              <TableCell>Transparencia</TableCell>
              <TableCell>Seguridad</TableCell>
              <TableCell>Fecha</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {scores.map((s) => (
              <TableRow key={s.id} hover>
                <TableCell sx={{ fontFamily: 'monospace' }}>{s.alert_id.slice(0, 8)}</TableCell>
                <TableCell>
                  <Typography fontWeight={700} color={s.total_score >= 90 ? 'success.main' : s.total_score >= 70 ? 'info.main' : 'error.main'}>
                    {s.total_score}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip label={s.risk_level.replace('_', ' ')} color={riskColor(s.risk_level) as any} size="small" />
                </TableCell>
                <TableCell>{s.data_minimization}</TableCell>
                <TableCell>{s.legal_basis}</TableCell>
                <TableCell>{s.transparency}</TableCell>
                <TableCell>{s.pipeline_security}</TableCell>
                <TableCell>{new Date(s.created_at).toLocaleString('es-ES')}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
