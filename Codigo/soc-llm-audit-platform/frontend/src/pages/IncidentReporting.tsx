import { useState, useCallback, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Chip, Grid, Button,
  Stepper, Step, StepLabel, Alert,
} from '@mui/material';
import useWebSocket from '../hooks/useWebSocket';
import SLATimerChart from '../components/charts/SLATimerChart';
import { incidentsApi } from '../services/api';

interface Incident {
  id: string;
  type: string;
  severity: string;
  status: string;
  created_at: string;
  preliminary_deadline: string;
  detailed_deadline: string;
  final_deadline: string;
}

function computeSLAItems(incidents: Incident[]) {
  const now = Date.now();
  return incidents.map((inc) => {
    const created = new Date(inc.created_at).getTime();
    const elapsedMs = now - created;
    const elapsedHours = elapsedMs / (1000 * 60 * 60);
    return {
      incident_id: inc.id,
      sla_24h_pct: Math.min(100, (elapsedHours / 24) * 100),
      sla_72h_pct: Math.min(100, (elapsedHours / 72) * 100),
      elapsed_hours: Math.round(elapsedHours),
    };
  });
}

export default function IncidentReporting() {
  const [incidents, setIncidents] = useState<Incident[]>([
    {
      id: 'INC-2026-001', type: 'ransomware', severity: 'critical', status: 'preliminary_sent',
      created_at: '2026-03-31T03:00:00Z',
      preliminary_deadline: '2026-04-01T03:00:00Z',
      detailed_deadline: '2026-04-03T03:00:00Z',
      final_deadline: '2026-04-30T03:00:00Z',
    },
  ]);

  useEffect(() => {
    incidentsApi.list()
      .then((res) => {
        const data = res.data as Incident[];
        if (data && data.length > 0) setIncidents(data);
      })
      .catch(() => { /* keep mock data */ });
  }, []);

  const handleWsMessage = useCallback((data: Record<string, unknown>) => {
    if (data.type === 'incident_update' && data.incident) {
      const updated = data.incident as Incident;
      setIncidents((prev) => {
        const exists = prev.find((i) => i.id === updated.id);
        if (exists) return prev.map((i) => (i.id === updated.id ? updated : i));
        return [updated, ...prev];
      });
    }
  }, []);

  const { connected } = useWebSocket('/ws/alerts/stream', { onMessage: handleWsMessage });

  const statusSteps = ['Detectado', 'Preliminar (24h)', 'Detallado (72h)', 'Final (1 mes)', 'Cerrado'];
  const getActiveStep = (status: string) => {
    switch (status) {
      case 'detected': return 0;
      case 'preliminary_sent': return 1;
      case 'detailed_sent': return 2;
      case 'final_sent': return 3;
      case 'closed': return 4;
      default: return 0;
    }
  };

  const slaItems = computeSLAItems(incidents);

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
        <Typography variant="h4">Incident Reporting</Typography>
        <Chip
          label={connected ? 'Live' : 'Offline'}
          color={connected ? 'success' : 'default'}
          size="small"
          variant="outlined"
        />
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        NIS2 Art. 23: Notificación CSIRT con plazos 24h / 72h / 1 mes
      </Typography>

      {/* SLA Timer Chart */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>SLA Countdown</Typography>
          <SLATimerChart items={slaItems} />
        </CardContent>
      </Card>

      <Button variant="contained" color="error" sx={{ mb: 3 }}>Crear Reporte de Incidente</Button>

      {incidents.map((inc) => (
        <Card key={inc.id} sx={{ mb: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Typography variant="h6">{inc.id}</Typography>
              <Chip label={inc.type} variant="outlined" />
              <Chip label={inc.severity} color="error" />
            </Box>

            <Stepper activeStep={getActiveStep(inc.status)} sx={{ mb: 2 }}>
              {statusSteps.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>

            <Alert severity="warning">
              Próximo plazo: {new Date(inc.detailed_deadline).toLocaleString('es-ES')} (Reporte detallado 72h)
            </Alert>

            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={4}>
                <Typography variant="caption" color="text.secondary">Preliminar (24h)</Typography>
                <Typography>{new Date(inc.preliminary_deadline).toLocaleString('es-ES')}</Typography>
              </Grid>
              <Grid item xs={4}>
                <Typography variant="caption" color="text.secondary">Detallado (72h)</Typography>
                <Typography>{new Date(inc.detailed_deadline).toLocaleString('es-ES')}</Typography>
              </Grid>
              <Grid item xs={4}>
                <Typography variant="caption" color="text.secondary">Final (1 mes)</Typography>
                <Typography>{new Date(inc.final_deadline).toLocaleString('es-ES')}</Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      ))}
    </Box>
  );
}
