import { useEffect, useState, useCallback } from 'react';
import {
  Box, Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, Paper, LinearProgress,
} from '@mui/material';
import { alertsApi, complianceApi } from '../services/api';
import useWebSocket from '../hooks/useWebSocket';


interface Alert {
  id: string;
  source: string;
  severity_score: number;
  compliance_score: number;
  llm_classification: string;
  hitl_level: number;
  hitl_status: string;
  created_at: string;
}

const severityColor = (score: number) => {
  if (score >= 80) return 'error';
  if (score >= 60) return 'warning';
  return 'success';
};

const MOCK_ALERTS: Alert[] = [
  { id: 'a1b2c3', source: 'Splunk', severity_score: 85, compliance_score: 92, llm_classification: 'malware', hitl_level: 0, hitl_status: 'auto_processed', created_at: '2026-03-31T10:30:00Z' },
  { id: 'd4e5f6', source: 'Sentinel', severity_score: 72, compliance_score: 78, llm_classification: 'phishing', hitl_level: 1, hitl_status: 'pending', created_at: '2026-03-31T10:25:00Z' },
  { id: 'g7h8i9', source: 'Elastic', severity_score: 95, compliance_score: 45, llm_classification: 'ransomware', hitl_level: 3, hitl_status: 'pending', created_at: '2026-03-31T10:20:00Z' },
];

export default function AlertTriage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  // Real-time alert stream via WebSocket
  const onWsAlert = useCallback((data: Record<string, unknown>) => {
    const newAlert: Alert = {
      id: String(data.id ?? ''),
      source: String(data.source ?? 'WS'),
      severity_score: Number(data.severity_score ?? 0),
      compliance_score: Number(data.compliance_score ?? 0),
      llm_classification: String(data.llm_classification ?? 'pending'),
      hitl_level: Number(data.hitl_level ?? 0),
      hitl_status: String(data.hitl_status ?? 'pending'),
      created_at: String(data.created_at ?? new Date().toISOString()),
    };
    if (newAlert.id) setAlerts((prev) => [newAlert, ...prev].slice(0, 100));
  }, []);

  const { connected: wsConnected } = useWebSocket('/ws/alerts/stream', { onMessage: onWsAlert });

  useEffect(() => {
    complianceApi.getScores({ page_size: 50 })
      .then(async (res) => {
        const scores = res.data as Array<{ alert_id: string; total_score: number }>;
        const loaded: Alert[] = [];
        for (const s of scores.slice(0, 20)) {
          try {
            const alertRes = await alertsApi.getById(s.alert_id);
            const a = alertRes.data;
            loaded.push({
              id: a.id,
              source: a.source,
              severity_score: a.severity_score ?? 0,
              compliance_score: a.compliance_score ?? s.total_score,
              llm_classification: a.llm_classification ?? 'unknown',
              hitl_level: a.hitl_level ?? 0,
              hitl_status: a.hitl_status ?? 'unknown',
              created_at: a.created_at,
            });
          } catch { /* skip */ }
        }
        setAlerts(loaded.length > 0 ? loaded : MOCK_ALERTS);
      })
      .catch(() => setAlerts(MOCK_ALERTS))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LinearProgress />;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Alert Triage</Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
        <Typography variant="body2" color="text.secondary">
          Alertas procesadas por el pipeline LLM con clasificación y scoring automático
        </Typography>
        <Chip label={wsConnected ? 'Real-time ●' : 'Offline'}
          color={wsConnected ? 'success' : 'default'}
          size="small" variant="outlined" sx={{ fontSize: 10 }} />
      </Box>

      <TableContainer component={Paper} sx={{ bgcolor: 'background.paper' }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Fuente</TableCell>
              <TableCell>Clasificación</TableCell>
              <TableCell>Severidad</TableCell>
              <TableCell>Compliance</TableCell>
              <TableCell>HITL Level</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell>Fecha</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {alerts.map((alert) => (
              <TableRow key={alert.id} hover>
                <TableCell sx={{ fontFamily: 'monospace' }}>{alert.id.slice(0, 8)}</TableCell>
                <TableCell>{alert.source}</TableCell>
                <TableCell>
                  <Chip label={alert.llm_classification} size="small" variant="outlined" />
                </TableCell>
                <TableCell>
                  <Chip label={alert.severity_score} color={severityColor(alert.severity_score)} size="small" />
                </TableCell>
                <TableCell>{alert.compliance_score}</TableCell>
                <TableCell>L{alert.hitl_level}</TableCell>
                <TableCell>
                  <Chip label={alert.hitl_status} size="small"
                    color={alert.hitl_status === 'pending' ? 'warning' : 'success'} />
                </TableCell>
                <TableCell>{new Date(alert.created_at).toLocaleString('es-ES')}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
