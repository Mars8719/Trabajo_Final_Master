import { Box, Typography, Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';
import { CheckCircle, Error as ErrorIcon } from '@mui/icons-material';

interface AuditBlock {
  index: number;
  timestamp: string;
  agent_id: string;
  action_type: string;
  composite_score: number;
  level: string;
  hash: string;
  previous_hash: string;
  verified: boolean;
}

const defaultBlocks: AuditBlock[] = [
  { index: 1, timestamp: '2026-03-31T23:45:12Z', agent_id: 'triage_agent', action_type: 'classify_alert', composite_score: 0.92, level: 'COMPLIANT', hash: 'a3f2c8...d41e', previous_hash: '000000...0000', verified: true },
  { index: 2, timestamp: '2026-03-31T23:46:08Z', agent_id: 'detector_agent', action_type: 'analyze_payload', composite_score: 0.87, level: 'COMPLIANT', hash: 'b7e1d4...f28a', previous_hash: 'a3f2c8...d41e', verified: true },
  { index: 3, timestamp: '2026-03-31T23:47:22Z', agent_id: 'responder_agent', action_type: 'execute_playbook', composite_score: 0.73, level: 'WARNING', hash: 'c5a9b2...e17c', previous_hash: 'b7e1d4...f28a', verified: true },
  { index: 4, timestamp: '2026-04-01T00:01:45Z', agent_id: 'triage_agent', action_type: 'classify_alert', composite_score: 0.55, level: 'VIOLATION', hash: 'd8f3e1...a94b', previous_hash: 'c5a9b2...e17c', verified: true },
  { index: 5, timestamp: '2026-04-01T00:05:33Z', agent_id: 'ethical_gate', action_type: 'block_action', composite_score: 0.35, level: 'BLOCKED', hash: 'e2c7a9...b63d', previous_hash: 'd8f3e1...a94b', verified: true },
];

function getLevelColor(level: string): 'success' | 'info' | 'warning' | 'error' {
  switch (level) {
    case 'COMPLIANT': return 'success';
    case 'WARNING': return 'warning';
    case 'VIOLATION': return 'error';
    case 'BLOCKED': return 'error';
    default: return 'info';
  }
}

interface Props {
  blocks?: AuditBlock[];
}

export default function AuditChainTable({ blocks = defaultBlocks }: Props) {
  return (
    <Box sx={{ py: 1 }}>
      <TableContainer sx={{ maxHeight: 260 }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontSize: 10, bgcolor: '#0d2137' }}>#</TableCell>
              <TableCell sx={{ fontSize: 10, bgcolor: '#0d2137' }}>Timestamp</TableCell>
              <TableCell sx={{ fontSize: 10, bgcolor: '#0d2137' }}>Agent</TableCell>
              <TableCell sx={{ fontSize: 10, bgcolor: '#0d2137' }}>Action</TableCell>
              <TableCell sx={{ fontSize: 10, bgcolor: '#0d2137' }}>Score</TableCell>
              <TableCell sx={{ fontSize: 10, bgcolor: '#0d2137' }}>Level</TableCell>
              <TableCell sx={{ fontSize: 10, bgcolor: '#0d2137' }}>Hash</TableCell>
              <TableCell sx={{ fontSize: 10, bgcolor: '#0d2137' }}>✓</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {blocks.map((block) => (
              <TableRow key={block.index} sx={{ '&:hover': { bgcolor: '#1a2a3a' } }}>
                <TableCell sx={{ fontSize: 10 }}>{block.index}</TableCell>
                <TableCell sx={{ fontSize: 9 }}>
                  {new Date(block.timestamp).toLocaleTimeString('es-ES')}
                </TableCell>
                <TableCell sx={{ fontSize: 10 }}>{block.agent_id}</TableCell>
                <TableCell sx={{ fontSize: 10 }}>{block.action_type}</TableCell>
                <TableCell sx={{ fontSize: 10 }}>{block.composite_score.toFixed(2)}</TableCell>
                <TableCell>
                  <Chip label={block.level} size="small" color={getLevelColor(block.level)}
                    sx={{ fontSize: 8, height: 18 }} />
                </TableCell>
                <TableCell sx={{ fontSize: 9, fontFamily: 'monospace' }}>{block.hash}</TableCell>
                <TableCell>
                  {block.verified
                    ? <CheckCircle sx={{ fontSize: 14, color: '#66bb6a' }} />
                    : <ErrorIcon sx={{ fontSize: 14, color: '#ef5350' }} />
                  }
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
        NIS2+GDPR Art.30 — Hash chain SHA-256 inmutable con verificación integridad
      </Typography>
    </Box>
  );
}
