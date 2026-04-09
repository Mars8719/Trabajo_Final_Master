import { Box, Typography, Chip } from '@mui/material';

interface Notification {
  id: string;
  type: string;
  framework: string;
  deadline: string;
  status: 'pending' | 'sent' | 'overdue';
  priority: number; // 1-5, determines visual size
}

const defaultNotifications: Notification[] = [
  { id: 'N-001', type: 'CSIRT Early Warning', framework: 'NIS2', deadline: '4h remaining', status: 'pending', priority: 5 },
  { id: 'N-002', type: 'DPA Breach Notification', framework: 'GDPR', deadline: '48h remaining', status: 'pending', priority: 4 },
  { id: 'N-003', type: 'Detailed Report', framework: 'NIS2', deadline: '2d remaining', status: 'pending', priority: 3 },
  { id: 'N-004', type: 'Final Report', framework: 'NIS2', deadline: '28d remaining', status: 'pending', priority: 2 },
  { id: 'N-005', type: 'AI Act Transparency', framework: 'AI Act', deadline: 'Aug 2026', status: 'pending', priority: 2 },
  { id: 'N-006', type: 'DPO Quarterly Review', framework: 'GDPR', deadline: 'Overdue', status: 'overdue', priority: 4 },
  { id: 'N-007', type: 'DPIA Update', framework: 'GDPR', deadline: '15d remaining', status: 'pending', priority: 2 },
  { id: 'N-008', type: 'Bias Audit Report', framework: 'AI Act', deadline: '30d remaining', status: 'pending', priority: 1 },
];

function getFrameworkColor(fw: string): string {
  switch (fw) {
    case 'NIS2': return '#29b6f6';
    case 'GDPR': return '#66bb6a';
    case 'AI Act': return '#ce93d8';
    default: return '#999';
  }
}

function getStatusColor(status: string): 'warning' | 'success' | 'error' {
  switch (status) {
    case 'pending': return 'warning';
    case 'sent': return 'success';
    case 'overdue': return 'error';
    default: return 'warning';
  }
}

interface Props {
  notifications?: Notification[];
}

export default function NotificationTreemap({ notifications = defaultNotifications }: Props) {
  // Sort by priority descending
  const sorted = [...notifications].sort((a, b) => b.priority - a.priority);

  return (
    <Box sx={{ py: 1 }}>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
        {sorted.map((n) => {
          const size = 40 + n.priority * 16;
          return (
            <Box
              key={n.id}
              sx={{
                width: size,
                height: size,
                bgcolor: getFrameworkColor(n.framework) + '22',
                border: `1px solid ${getFrameworkColor(n.framework)}`,
                borderRadius: 1,
                p: 0.5,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                cursor: 'pointer',
                transition: 'all 0.2s',
                '&:hover': { bgcolor: getFrameworkColor(n.framework) + '44' },
              }}
            >
              <Typography variant="caption" sx={{
                fontSize: Math.max(7, 6 + n.priority),
                fontWeight: 700,
                textAlign: 'center',
                lineHeight: 1.1,
                color: getFrameworkColor(n.framework),
              }}>
                {n.type}
              </Typography>
              <Chip
                label={n.status}
                color={getStatusColor(n.status)}
                size="small"
                sx={{ fontSize: 6, height: 14, mt: 0.3, '& .MuiChip-label': { px: 0.5 } }}
              />
              <Typography variant="caption" sx={{ fontSize: 7, mt: 0.3, color: '#999' }}>
                {n.deadline}
              </Typography>
            </Box>
          );
        })}
      </Box>
      <Box sx={{ display: 'flex', gap: 1, mt: 1.5, flexWrap: 'wrap' }}>
        {['NIS2', 'GDPR', 'AI Act'].map((fw) => (
          <Chip
            key={fw}
            label={`${fw}: ${notifications.filter((n) => n.framework === fw).length}`}
            size="small"
            sx={{ fontSize: 9, height: 20, bgcolor: getFrameworkColor(fw) + '33', color: getFrameworkColor(fw) }}
          />
        ))}
        <Chip
          label={`Overdue: ${notifications.filter((n) => n.status === 'overdue').length}`}
          size="small" color="error" variant="outlined"
          sx={{ fontSize: 9, height: 20 }}
        />
      </Box>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
        GDPR Art.33 / NIS2 Art.23 — Notificaciones regulatorias pendientes (tamaño = prioridad)
      </Typography>
    </Box>
  );
}
