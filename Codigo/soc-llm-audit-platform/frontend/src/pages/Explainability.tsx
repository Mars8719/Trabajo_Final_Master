import { useState } from 'react';
import {
  Box, Typography, Card, CardContent, Grid, Chip, List, ListItem, ListItemText, Divider,
} from '@mui/material';
import WaterfallChart from '../components/charts/WaterfallChart';

interface Feature {
  feature: string;
  value: number;
  shap_value: number;
  impact: string;
}

export default function Explainability() {
  const [features] = useState<Feature[]>([
    { feature: 'data_minimization', value: 95, shap_value: 3.0, impact: 'positive' },
    { feature: 'legal_basis', value: 100, shap_value: 3.75, impact: 'positive' },
    { feature: 'transparency', value: 80, shap_value: 0.75, impact: 'positive' },
    { feature: 'pipeline_security', value: 85, shap_value: 1.5, impact: 'positive' },
    { feature: 'bias_fairness', value: 90, shap_value: 1.5, impact: 'positive' },
    { feature: 'retention_compliance', value: 60, shap_value: -1.5, impact: 'negative' },
    { feature: 'incident_reporting', value: 90, shap_value: 1.5, impact: 'positive' },
    { feature: 'hitl_compliance', value: 100, shap_value: 2.5, impact: 'positive' },
  ]);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Explainability</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        SHAP + LIME — Explicaciones auditables para cada decisión del LLM (GDPR Art. 13-14, EU AI Act)
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>SHAP Waterfall — Contribución por Feature</Typography>
              <WaterfallChart features={features} />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={5}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Feature Importance</Typography>
              <List>
                {features.sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value)).map((f) => (
                  <div key={f.feature}>
                    <ListItem>
                      <ListItemText
                        primary={f.feature.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                        secondary={`Valor: ${f.value} | SHAP: ${f.shap_value > 0 ? '+' : ''}${f.shap_value.toFixed(2)}`}
                      />
                      <Chip
                        label={f.impact === 'positive' ? '↑' : '↓'}
                        color={f.impact === 'positive' ? 'success' : 'error'}
                        size="small"
                      />
                    </ListItem>
                    <Divider />
                  </div>
                ))}
              </List>
            </CardContent>
          </Card>

          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Base Normativa</Typography>
              <List dense>
                <ListItem><ListItemText primary="GDPR Art. 5 — Minimización de datos" /></ListItem>
                <ListItem><ListItemText primary="GDPR Art. 6 — Base legal de procesamiento" /></ListItem>
                <ListItem><ListItemText primary="GDPR Art. 13-14 — Transparencia" /></ListItem>
                <ListItem><ListItemText primary="NIS2 Art. 21 — Gestión de riesgos" /></ListItem>
                <ListItem><ListItemText primary="NIS2 Art. 23 — Notificación" /></ListItem>
                <ListItem><ListItemText primary="EU AI Act — Explicabilidad obligatoria" /></ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
