import { Box, Typography, LinearProgress, Chip } from '@mui/material';

interface SLAItem {
  incident_id: string;
  sla_24h_pct: number;
  sla_72h_pct: number;
  elapsed_hours: number;
}

interface Props {
  items: SLAItem[];
}

function getColor(pct: number): string {
  if (pct >= 90) return '#ef5350';
  if (pct >= 70) return '#ffa726';
  if (pct >= 50) return '#ffee58';
  return '#66bb6a';
}

export default function SLATimerChart({ items }: Props) {
  if (!items || items.length === 0) {
    return (
      <Box sx={{ py: 2, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Sin incidentes activos con SLA
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ py: 1 }}>
      {items.map((item) => (
        <Box key={item.incident_id} sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="caption" sx={{ fontWeight: 600 }}>
              {item.incident_id}
            </Typography>
            <Chip
              label={`${item.elapsed_hours}h transcurridas`}
              size="small"
              sx={{ fontSize: 10, height: 20 }}
              color={item.sla_24h_pct >= 100 ? 'error' : 'default'}
            />
          </Box>

          {/* NIS2 24h SLA */}
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
            <Typography variant="caption" sx={{ width: 70, fontSize: 10 }}>
              NIS2 24h
            </Typography>
            <Box sx={{ flexGrow: 1, mr: 1 }}>
              <LinearProgress
                variant="determinate"
                value={Math.min(item.sla_24h_pct, 100)}
                sx={{
                  height: 12,
                  borderRadius: 1,
                  bgcolor: '#333',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: getColor(item.sla_24h_pct),
                    borderRadius: 1,
                  },
                }}
              />
            </Box>
            <Typography variant="caption" sx={{ fontSize: 10, width: 40, textAlign: 'right' }}>
              {item.sla_24h_pct.toFixed(0)}%
            </Typography>
          </Box>

          {/* GDPR/NIS2 72h SLA */}
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ width: 70, fontSize: 10 }}>
              72h
            </Typography>
            <Box sx={{ flexGrow: 1, mr: 1 }}>
              <LinearProgress
                variant="determinate"
                value={Math.min(item.sla_72h_pct, 100)}
                sx={{
                  height: 12,
                  borderRadius: 1,
                  bgcolor: '#333',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: getColor(item.sla_72h_pct),
                    borderRadius: 1,
                  },
                }}
              />
            </Box>
            <Typography variant="caption" sx={{ fontSize: 10, width: 40, textAlign: 'right' }}>
              {item.sla_72h_pct.toFixed(0)}%
            </Typography>
          </Box>
        </Box>
      ))}
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
        NIS2 Art.23 / GDPR Art.33 — Countdown por incidente activo
      </Typography>
    </Box>
  );
}
