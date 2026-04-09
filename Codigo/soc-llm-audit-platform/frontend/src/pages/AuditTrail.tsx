import { useEffect, useState } from 'react';
import {
  Box, Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, Chip, Button, LinearProgress,
} from '@mui/material';
import { Verified, Warning } from '@mui/icons-material';
import { auditApi } from '../services/api';

interface AuditEntry {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  gdpr_articles: string[];
  nis2_articles: string[];
  hash_chain: string;
}

const MOCK_ENTRIES: AuditEntry[] = [
  { id: '1', timestamp: '2026-03-31T10:30:00Z', actor: 'system', action: 'alert.ingested', gdpr_articles: ['Art. 5', 'Art. 25'], nis2_articles: [], hash_chain: 'a1b2c3d4e5f6...' },
  { id: '2', timestamp: '2026-03-31T10:25:00Z', actor: 'analyst_001', action: 'hitl.decision.approved', gdpr_articles: ['Art. 22'], nis2_articles: ['Art. 21'], hash_chain: 'f6e5d4c3b2a1...' },
];

export default function AuditTrail() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [integrityValid, setIntegrityValid] = useState<boolean | null>(null);

  useEffect(() => {
    auditApi.getTrail()
      .then((res) => {
        const data = res.data as Array<Record<string, unknown>>;
        const loaded = data.map((e) => ({
          id: String(e.id),
          timestamp: String(e.timestamp),
          actor: String(e.actor),
          action: String(e.action),
          gdpr_articles: (e.gdpr_articles as string[]) ?? [],
          nis2_articles: (e.nis2_articles as string[]) ?? [],
          hash_chain: String(e.hash_chain ?? ''),
        }));
        setEntries(loaded.length > 0 ? loaded : MOCK_ENTRIES);
      })
      .catch(() => setEntries(MOCK_ENTRIES))
      .finally(() => setLoading(false));
  }, []);

  const handleVerify = () => {
    auditApi.verifyIntegrity()
      .then((res) => setIntegrityValid((res.data as { integrity_valid: boolean }).integrity_valid))
      .catch(() => setIntegrityValid(false));
  };

  const handleExport = () => {
    auditApi.exportTrail()
      .then((res) => {
        const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit-trail-export-${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
        URL.revokeObjectURL(url);
      });
  };

  if (loading) return <LinearProgress />;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Audit Trail</Typography>
        {integrityValid !== null && (
          <Chip
            icon={integrityValid ? <Verified /> : <Warning />}
            label={integrityValid ? 'Integridad OK' : 'Integridad Comprometida'}
            color={integrityValid ? 'success' : 'error'}
            sx={{ ml: 2 }}
          />
        )}
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Registro inmutable (append-only) con hash chain SHA-256. Retención: 7 años.
      </Typography>

      <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
        <Button variant="outlined" onClick={handleExport}>Exportar JSON</Button>
        <Button variant="outlined" onClick={handleVerify}>Verificar Integridad</Button>
      </Box>

      <TableContainer component={Paper} sx={{ bgcolor: 'background.paper' }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Timestamp</TableCell>
              <TableCell>Actor</TableCell>
              <TableCell>Acción</TableCell>
              <TableCell>GDPR</TableCell>
              <TableCell>NIS2</TableCell>
              <TableCell>Hash Chain</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {entries.map((e) => (
              <TableRow key={e.id} hover>
                <TableCell>{e.id}</TableCell>
                <TableCell>{new Date(e.timestamp).toLocaleString('es-ES')}</TableCell>
                <TableCell>{e.actor}</TableCell>
                <TableCell><Chip label={e.action} size="small" variant="outlined" /></TableCell>
                <TableCell>{e.gdpr_articles.join(', ') || '—'}</TableCell>
                <TableCell>{e.nis2_articles.join(', ') || '—'}</TableCell>
                <TableCell sx={{ fontFamily: 'monospace', fontSize: 12 }}>{e.hash_chain}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
