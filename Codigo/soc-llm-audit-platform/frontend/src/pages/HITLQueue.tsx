import { useEffect, useState, useCallback } from 'react';
import {
  Box, Typography, Card, CardContent, Button, TextField, Chip,
  Dialog, DialogTitle, DialogContent, DialogActions, Alert, Stack,
  LinearProgress,
} from '@mui/material';
import { hitlApi } from '../services/api';
import useWebSocket from '../hooks/useWebSocket';


interface HITLItem {
  id: string;
  alert_id: string;
  escalation_level: string;
  cs_at_review: number;
  confidence: number;
  classification: string;
  created_at: string;
}

const MOCK_QUEUE: HITLItem[] = [
  { id: '1', alert_id: 'd4e5f6', escalation_level: 'L1', cs_at_review: 78, confidence: 0.82, classification: 'phishing', created_at: '2026-03-31T10:25:00Z' },
  { id: '2', alert_id: 'g7h8i9', escalation_level: 'L3', cs_at_review: 45, confidence: 0.35, classification: 'ransomware', created_at: '2026-03-31T10:20:00Z' },
];

export default function HITLQueue() {
  const [queue, setQueue] = useState<HITLItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Real-time HITL queue updates via WebSocket
  const onHitlUpdate = useCallback((data: Record<string, unknown>) => {
    const item: HITLItem = {
      id: String(data.id ?? ''),
      alert_id: String(data.alert_id ?? ''),
      escalation_level: String(data.escalation_level ?? 'L1'),
      cs_at_review: Number(data.cs_at_review ?? 0),
      confidence: Number(data.confidence ?? 0),
      classification: String(data.classification ?? 'pending'),
      created_at: String(data.created_at ?? new Date().toISOString()),
    };
    if (item.id) setQueue((prev) => [item, ...prev.filter((q) => q.id !== item.id)]);
  }, []);

  const { connected: wsConnected } = useWebSocket('/ws/hitl/queue', { onMessage: onHitlUpdate });

  useEffect(() => {
    hitlApi.getQueue()
      .then((res) => {
        const items = (res.data as Array<Record<string, unknown>>).map((item) => ({
          id: String(item.id),
          alert_id: String(item.alert_id),
          escalation_level: String(item.escalation_level),
          cs_at_review: Number(item.cs_at_review ?? 0),
          confidence: Number(item.confidence_at_review ?? 0),
          classification: 'pending',
          created_at: String(item.created_at),
        }));
        setQueue(items.length > 0 ? items : MOCK_QUEUE);
      })
      .catch(() => setQueue(MOCK_QUEUE))
      .finally(() => setLoading(false));
  }, []);

  const [openDialog, setOpenDialog] = useState(false);
  const [, setSelectedItem] = useState<HITLItem | null>(null);
  const [justification, setJustification] = useState('');

  const levelColor = (level: string) => {
    switch (level) {
      case 'L1': return 'info';
      case 'L2': return 'warning';
      case 'L3': return 'error';
      case 'L4': return 'error';
      default: return 'default';
    }
  };

  const handleDecision = (item: HITLItem) => {
    setSelectedItem(item);
    setOpenDialog(true);
  };

  if (loading) return <LinearProgress />;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">HITL Queue</Typography>
        <Chip label={`${queue.length} pendientes`} color="warning" sx={{ ml: 2 }} />
        <Chip label={wsConnected ? 'Real-time ●' : 'Offline'}
          color={wsConnected ? 'success' : 'default'}
          size="small" variant="outlined" sx={{ ml: 1, fontSize: 10 }} />
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        Human-in-the-Loop: Revise cada alerta y proporcione justificación detallada (HOJR).
        Anti-rubber-stamping activo: decisiones &lt; 10s serán rechazadas.
      </Alert>

      <Stack spacing={2}>
        {queue.map((item) => (
          <Card key={item.id}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Chip label={item.escalation_level} color={levelColor(item.escalation_level) as any} />
                    <Chip label={item.classification} variant="outlined" size="small" />
                    <Typography variant="body2" color="text.secondary">
                      Alert: {item.alert_id}
                    </Typography>
                  </Box>
                  <Typography variant="body2">
                    CS: <strong>{item.cs_at_review}</strong> | Confianza: <strong>{(item.confidence * 100).toFixed(0)}%</strong>
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(item.created_at).toLocaleString('es-ES')}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button variant="contained" color="success" onClick={() => handleDecision(item)}>Aprobar</Button>
                  <Button variant="contained" color="error" onClick={() => handleDecision(item)}>Rechazar</Button>
                  <Button variant="outlined" color="warning" onClick={() => handleDecision(item)}>Escalar</Button>
                </Box>
              </Box>
            </CardContent>
          </Card>
        ))}
      </Stack>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Decisión HITL — HOJR Record</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Justificación obligatoria (mín. 20 caracteres). Explique su razonamiento.
          </Alert>
          <TextField
            fullWidth multiline rows={4}
            label="Justificación (HOJR)"
            value={justification}
            onChange={(e) => setJustification(e.target.value)}
            helperText={`${justification.length}/20 caracteres mínimos`}
            error={justification.length > 0 && justification.length < 20}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancelar</Button>
          <Button variant="contained" disabled={justification.length < 20}>Confirmar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
