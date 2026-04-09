import { useState } from 'react';
import {
  Box, Typography, Card, CardContent, Button, Grid, Chip,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
} from '@mui/material';
import RiskMatrix from '../components/charts/RiskMatrix';

export default function DPIAManager() {
  const [dpias] = useState([
    { id: '1', version: '1.0', status: 'approved', risks_count: 12, created_at: '2026-03-15', next_review: '2026-06-15' },
    { id: '2', version: '1.1', status: 'draft', risks_count: 8, created_at: '2026-03-30', next_review: '2026-06-30' },
  ]);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>DPIA Manager</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Data Protection Impact Assessment automatizada (GDPR Art. 35). Actualización continua.
      </Typography>

      <Button variant="contained" sx={{ mb: 3 }}>Generar Nueva DPIA</Button>

      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <TableContainer component={Paper} sx={{ bgcolor: 'background.paper' }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Versión</TableCell>
                  <TableCell>Estado</TableCell>
                  <TableCell>Riesgos</TableCell>
                  <TableCell>Creada</TableCell>
                  <TableCell>Próxima Revisión</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {dpias.map((d) => (
                  <TableRow key={d.id} hover>
                    <TableCell>v{d.version}</TableCell>
                    <TableCell>
                      <Chip label={d.status} color={d.status === 'approved' ? 'success' : 'warning'} size="small" />
                    </TableCell>
                    <TableCell>{d.risks_count}</TableCell>
                    <TableCell>{d.created_at}</TableCell>
                    <TableCell>{d.next_review}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>

        <Grid item xs={12} md={5}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Matriz de Riesgos</Typography>
              <RiskMatrix />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
