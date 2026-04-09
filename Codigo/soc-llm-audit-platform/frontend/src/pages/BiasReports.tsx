import { useState } from 'react';
import {
  Box, Typography, Card, CardContent, Grid, Chip, LinearProgress,
} from '@mui/material';
import { CheckCircle, Cancel } from '@mui/icons-material';

interface BiasResult {
  dimension: string;
  test_name: string;
  adverse_impact_ratio: number;
  passed: boolean;
  threshold: number;
}

export default function BiasReports() {
  const [results] = useState<BiasResult[]>([
    { dimension: 'geographic', test_name: 'Sesgo geográfico: EU vs Africa', adverse_impact_ratio: 0.96, passed: true, threshold: 0.8 },
    { dimension: 'temporal', test_name: 'Sesgo temporal: diurnas vs nocturnas', adverse_impact_ratio: 0.94, passed: true, threshold: 0.8 },
    { dimension: 'linguistic', test_name: 'Sesgo lingüístico: es vs en', adverse_impact_ratio: 0.88, passed: true, threshold: 0.8 },
    { dimension: 'severity', test_name: 'Sesgo de severidad: predicha vs real', adverse_impact_ratio: 0.92, passed: true, threshold: 0.8 },
    { dimension: 'source', test_name: 'Sesgo de fuente SIEM', adverse_impact_ratio: 0.73, passed: false, threshold: 0.8 },
  ]);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Bias Reports</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Ethical Bias & Fairness Checker — 5 dimensiones. Umbral: ratio impacto adverso ≥ 0.8
      </Typography>

      <Grid container spacing={3}>
        {results.map((r) => (
          <Grid item xs={12} md={6} key={r.dimension}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6">{r.dimension.charAt(0).toUpperCase() + r.dimension.slice(1)}</Typography>
                  {r.passed
                    ? <Chip icon={<CheckCircle />} label="PASSED" color="success" size="small" />
                    : <Chip icon={<Cancel />} label="FAILED" color="error" size="small" />}
                </Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>{r.test_name}</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                  <Box sx={{ flexGrow: 1, mr: 2 }}>
                    <LinearProgress
                      variant="determinate"
                      value={r.adverse_impact_ratio * 100}
                      color={r.passed ? 'success' : 'error'}
                      sx={{ height: 10, borderRadius: 5 }}
                    />
                  </Box>
                  <Typography variant="body2" fontWeight={700}>
                    {(r.adverse_impact_ratio * 100).toFixed(1)}%
                  </Typography>
                </Box>
                <Typography variant="caption" color="text.secondary">
                  Umbral: {r.threshold * 100}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
