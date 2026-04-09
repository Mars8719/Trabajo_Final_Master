import { useState } from 'react';
import {
  Box, Typography, Card, CardContent, Grid, Switch, FormControlLabel,
  TextField, Button, Divider, Alert,
} from '@mui/material';

export default function Settings() {
  const [hitlEnabled, setHitlEnabled] = useState(true);
  const [killSwitchActive, setKillSwitchActive] = useState(false);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Settings</Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>HITL Configuration</Typography>
              <FormControlLabel
                control={<Switch checked={hitlEnabled} onChange={(e) => setHitlEnabled(e.target.checked)} />}
                label="HITL Active"
              />
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" gutterBottom>Umbrales de Escalación</Typography>
              <TextField fullWidth label="L0 CS Min" defaultValue="90" size="small" sx={{ mb: 1 }} />
              <TextField fullWidth label="L1 CS Min" defaultValue="70" size="small" sx={{ mb: 1 }} />
              <TextField fullWidth label="L2 CS Min" defaultValue="50" size="small" sx={{ mb: 1 }} />
              <TextField fullWidth label="L3 Confidence Min" defaultValue="0.50" size="small" />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Kill Switch (L4)</Typography>
              {killSwitchActive ? (
                <Alert severity="error" sx={{ mb: 2 }}>KILL SWITCH ACTIVO — LLM desactivado</Alert>
              ) : (
                <Alert severity="success" sx={{ mb: 2 }}>Sistema operativo — LLM activo</Alert>
              )}
              <Button
                variant="contained"
                color={killSwitchActive ? 'success' : 'error'}
                fullWidth
                onClick={() => setKillSwitchActive(!killSwitchActive)}
              >
                {killSwitchActive ? 'Desactivar Kill Switch' : 'Activar Kill Switch'}
              </Button>
            </CardContent>
          </Card>

          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Compliance Weights</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                CS = Σ(wi × si) donde Σ(wi) = 1.0
              </Typography>
              <TextField fullWidth label="Data Minimization" defaultValue="0.15" size="small" sx={{ mb: 1 }} />
              <TextField fullWidth label="Legal Basis" defaultValue="0.15" size="small" sx={{ mb: 1 }} />
              <TextField fullWidth label="Transparency" defaultValue="0.15" size="small" sx={{ mb: 1 }} />
              <TextField fullWidth label="Pipeline Security" defaultValue="0.15" size="small" sx={{ mb: 1 }} />
              <TextField fullWidth label="Bias Fairness" defaultValue="0.10" size="small" sx={{ mb: 1 }} />
              <TextField fullWidth label="Retention" defaultValue="0.10" size="small" sx={{ mb: 1 }} />
              <TextField fullWidth label="Incident Reporting" defaultValue="0.10" size="small" sx={{ mb: 1 }} />
              <TextField fullWidth label="HITL" defaultValue="0.10" size="small" />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
