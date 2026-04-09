import { useEffect, useState, useCallback } from 'react';
import {
  Grid, Card, CardContent, Typography, Box, Chip, LinearProgress,
} from '@mui/material';
import {
  Warning, Gavel, Psychology, BugReport, Timer, Security, Fingerprint,
  AccountBalance, VerifiedUser, AttachMoney, SmartToy, Shield,
} from '@mui/icons-material';
import { dashboardApi } from '../services/api';
import useWebSocket from '../hooks/useWebSocket';

// G1: CENS Score Gauge
import ComplianceGauge from '../components/charts/ComplianceGauge';
// G2: Score Normativo Time Series (3 líneas)
import TrendLine from '../components/charts/TrendLine';
// G3: Heatmap Riesgos Normativos
import RiskMatrix from '../components/charts/RiskMatrix';
// G4: SLA Timer NIS2/GDPR
import SLATimerChart from '../components/charts/SLATimerChart';
// G5: Agent Execution Trace
import AgentExecutionTrace from '../components/charts/AgentExecutionTrace';
// G6: RAG Pipeline Health
import RAGPipelineHealth from '../components/charts/RAGPipelineHealth';
// G7: PII Exposure Heatmap
import PIIExposureHeatmap from '../components/charts/PIIExposureHeatmap';
// G8: Hallucination & Drift Monitor
import HallucinationDriftMonitor from '../components/charts/HallucinationDriftMonitor';
// G9: Denial-of-Wallet Monitor
import DoWMonitor from '../components/charts/DoWMonitor';
// G10: Immutable Audit Chain Table
import AuditChainTable from '../components/charts/AuditChainTable';
// G11: Bias & Fairness Monitor
import BiasFairnessRadar from '../components/charts/BiasFairnessRadar';
// G12: Notification Center Treemap
import NotificationTreemap from '../components/charts/NotificationTreemap';

interface KPIs {
  alerts: { total: number; last_24h: number };
  compliance: { average_score: number; non_compliant_count: number };
  hitl: { pending_reviews: number; total_decisions: number };
  incidents: { active: number };
  bias: { tests_passed: number; tests_total: number };
  system_status: string;
}

interface EnterpriseKPIs {
  k1_cens_score: { score: number; delta_1h: number; status: string };
  k2_nis2_sla: { active_incidents: number; items: Array<{ incident_id: string; sla_24h_pct: number; sla_72h_pct: number; elapsed_hours: number }> };
  k3_pii_events: { today: number; yesterday: number; delta: number };
  k4_active_violations: { critical: number; warning: number; total: number };
  k5_audit_integrity: { valid: boolean; total_blocks: number };
  k6_human_review: { pending: number };
  k7_dow_budget: { current_hour_usd: number; limit_hour_usd: number; usage_pct: number };
  k8_ai_act_risk: { level: string; failed_bias_tests: number; deadline: string };
}

function KPICard({ title, value, subtitle, icon, color }: {
  title: string; value: string | number; subtitle: string; icon: React.ReactNode; color: string;
}) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ pb: '12px !important' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Box sx={{ bgcolor: `${color}22`, p: 0.8, borderRadius: 2, mr: 1.5 }}>{icon}</Box>
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: 11 }}>{title}</Typography>
        </Box>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>{value}</Typography>
        <Typography variant="caption" color="text.secondary">{subtitle}</Typography>
      </CardContent>
    </Card>
  );
}

const defaultEnterpriseKPIs: EnterpriseKPIs = {
  k1_cens_score: { score: 87.3, delta_1h: 1.2, status: 'GREEN' },
  k2_nis2_sla: { active_incidents: 2, items: [
    { incident_id: 'INC-2026-001', sla_24h_pct: 65, sla_72h_pct: 22, elapsed_hours: 15.6 },
    { incident_id: 'INC-2026-002', sla_24h_pct: 30, sla_72h_pct: 10, elapsed_hours: 7.2 },
  ]},
  k3_pii_events: { today: 12, yesterday: 8, delta: 4 },
  k4_active_violations: { critical: 2, warning: 5, total: 7 },
  k5_audit_integrity: { valid: true, total_blocks: 1847 },
  k6_human_review: { pending: 7 },
  k7_dow_budget: { current_hour_usd: 8.40, limit_hour_usd: 12.50, usage_pct: 67.2 },
  k8_ai_act_risk: { level: 'LIMITED', failed_bias_tests: 1, deadline: '2026-08-02T00:00:00Z' },
};

export default function Dashboard() {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [enterprise, setEnterprise] = useState<EnterpriseKPIs>(defaultEnterpriseKPIs);
  const [loading, setLoading] = useState(true);
  const [wsAlerts, setWsAlerts] = useState<number>(0);

  // WebSocket connections for real-time updates
  const onAlertMessage = useCallback(() => {
    setWsAlerts((prev) => prev + 1);
  }, []);

  const { connected: alertsWsConnected } = useWebSocket('/ws/alerts/stream', {
    onMessage: onAlertMessage,
  });

  const onComplianceMessage = useCallback((data: Record<string, unknown>) => {
    if (data.average_score && typeof data.average_score === 'number') {
      setKpis((prev) => prev ? { ...prev, compliance: { ...prev.compliance, average_score: data.average_score as number } } : prev);
    }
  }, []);

  useWebSocket('/ws/compliance/live', { onMessage: onComplianceMessage });
  useWebSocket('/ws/hitl/queue', {
    onMessage: useCallback((data: Record<string, unknown>) => {
      if (data.pending_reviews && typeof data.pending_reviews === 'number') {
        setKpis((prev) => prev ? { ...prev, hitl: { ...prev.hitl, pending_reviews: data.pending_reviews as number } } : prev);
      }
    }, []),
  });

  useEffect(() => {
    Promise.all([
      dashboardApi.getKPIs().catch(() => ({ data: null })),
      dashboardApi.getEnterpriseKPIs().catch(() => ({ data: null })),
    ]).then(([kpiRes, entRes]) => {
      if (kpiRes.data) {
        setKpis(kpiRes.data);
      } else {
        setKpis({
          alerts: { total: 1247, last_24h: 83 },
          compliance: { average_score: 87.3, non_compliant_count: 4 },
          hitl: { pending_reviews: 7, total_decisions: 342 },
          incidents: { active: 2 },
          bias: { tests_passed: 14, tests_total: 15 },
          system_status: 'operational',
        });
      }
      if (entRes.data) setEnterprise(entRes.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <LinearProgress />;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="h4">Dashboard Enterprise</Typography>
        <Chip label={kpis?.system_status === 'operational' ? 'Operativo' : 'Degradado'}
          color={kpis?.system_status === 'operational' ? 'success' : 'warning'}
          size="small" />
        <Chip label={alertsWsConnected ? 'WS Conectado' : 'WS Desconectado'}
          color={alertsWsConnected ? 'info' : 'default'}
          size="small" variant="outlined" />
        {wsAlerts > 0 && (
          <Chip label={`+${wsAlerts} alertas real-time`} color="warning" size="small" variant="outlined" />
        )}
      </Box>

      {/* ═══ 8 KPI CARDS (K1-K8) ═══ */}
      <Typography variant="h6" sx={{ mb: 1.5, color: 'text.secondary' }}>KPIs Ejecutivos</Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {/* K1: CENS Score */}
        <Grid item xs={6} sm={4} md={3} lg={1.5}>
          <KPICard
            title="K1 · CENS Score"
            value={`${enterprise.k1_cens_score.score}%`}
            subtitle={`${enterprise.k1_cens_score.delta_1h >= 0 ? '↑' : '↓'}${Math.abs(enterprise.k1_cens_score.delta_1h)} vs 1h`}
            icon={<Gavel sx={{ color: '#00b0ff', fontSize: 20 }} />} color="#00b0ff"
          />
        </Grid>
        {/* K2: NIS2 SLA Countdown */}
        <Grid item xs={6} sm={4} md={3} lg={1.5}>
          <KPICard
            title="K2 · NIS2 SLA"
            value={`${enterprise.k2_nis2_sla.active_incidents}`}
            subtitle={enterprise.k2_nis2_sla.items[0] ? `${enterprise.k2_nis2_sla.items[0].sla_24h_pct}% (24h)` : 'Sin incidentes'}
            icon={<Timer sx={{ color: '#ff9100', fontSize: 20 }} />} color="#ff9100"
          />
        </Grid>
        {/* K3: PII Events */}
        <Grid item xs={6} sm={4} md={3} lg={1.5}>
          <KPICard
            title="K3 · PII Events"
            value={enterprise.k3_pii_events.today}
            subtitle={`${enterprise.k3_pii_events.delta >= 0 ? '+' : ''}${enterprise.k3_pii_events.delta} vs ayer`}
            icon={<Fingerprint sx={{ color: '#ff1744', fontSize: 20 }} />} color="#ff1744"
          />
        </Grid>
        {/* K4: Active Violations */}
        <Grid item xs={6} sm={4} md={3} lg={1.5}>
          <KPICard
            title="K4 · Violations"
            value={enterprise.k4_active_violations.total}
            subtitle={`${enterprise.k4_active_violations.critical} críticas · ${enterprise.k4_active_violations.warning} warning`}
            icon={<Warning sx={{ color: '#ef5350', fontSize: 20 }} />} color="#ef5350"
          />
        </Grid>
        {/* K5: Audit Chain Integrity */}
        <Grid item xs={6} sm={4} md={3} lg={1.5}>
          <KPICard
            title="K5 · Audit Chain"
            value={enterprise.k5_audit_integrity.valid ? '✓ OK' : '✗ FAIL'}
            subtitle={`${enterprise.k5_audit_integrity.total_blocks} bloques SHA-256`}
            icon={<VerifiedUser sx={{ color: enterprise.k5_audit_integrity.valid ? '#66bb6a' : '#ef5350', fontSize: 20 }} />}
            color={enterprise.k5_audit_integrity.valid ? '#66bb6a' : '#ef5350'}
          />
        </Grid>
        {/* K6: Human Review Queue */}
        <Grid item xs={6} sm={4} md={3} lg={1.5}>
          <KPICard
            title="K6 · HITL Queue"
            value={kpis?.hitl.pending_reviews ?? enterprise.k6_human_review.pending}
            subtitle={`${kpis?.hitl.total_decisions ?? 0} decisiones totales`}
            icon={<Psychology sx={{ color: '#651fff', fontSize: 20 }} />} color="#651fff"
          />
        </Grid>
        {/* K7: DoW Budget */}
        <Grid item xs={6} sm={4} md={3} lg={1.5}>
          <KPICard
            title="K7 · DoW Budget"
            value={`${enterprise.k7_dow_budget.usage_pct}%`}
            subtitle={`$${enterprise.k7_dow_budget.current_hour_usd}/$${enterprise.k7_dow_budget.limit_hour_usd}/h`}
            icon={<AttachMoney sx={{ color: enterprise.k7_dow_budget.usage_pct > 80 ? '#ef5350' : '#66bb6a', fontSize: 20 }} />}
            color={enterprise.k7_dow_budget.usage_pct > 80 ? '#ef5350' : '#66bb6a'}
          />
        </Grid>
        {/* K8: AI Act Risk Level */}
        <Grid item xs={6} sm={4} md={3} lg={1.5}>
          <KPICard
            title="K8 · AI Act Risk"
            value={enterprise.k8_ai_act_risk.level}
            subtitle={`Deadline Aug'26 · ${enterprise.k8_ai_act_risk.failed_bias_tests} bias fails`}
            icon={<SmartToy sx={{ color: '#ce93d8', fontSize: 20 }} />} color="#ce93d8"
          />
        </Grid>
      </Grid>

      {/* ═══ 12 GRÁFICAS (G1-G12) ═══ */}
      <Typography variant="h6" sx={{ mb: 1.5, color: 'text.secondary' }}>Monitoreo en Tiempo Real</Typography>
      <Grid container spacing={2}>

        {/* G1: CENS Score Gauge */}
        <Grid item xs={12} md={4}>
          <Card sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>G1 · CENS Score Gauge</Typography>
            <ComplianceGauge score={kpis?.compliance.average_score ?? enterprise.k1_cens_score.score} />
          </Card>
        </Grid>

        {/* G2: Score Normativo Time Series (3 líneas) */}
        <Grid item xs={12} md={8}>
          <Card sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>G2 · Score Normativo (GDPR / NIS2 / Bias) — 24h</Typography>
            <TrendLine />
          </Card>
        </Grid>

        {/* G3: Heatmap Riesgos Normativos */}
        <Grid item xs={12} md={6}>
          <Card sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>G3 · Heatmap Riesgos Normativos</Typography>
            <RiskMatrix />
          </Card>
        </Grid>

        {/* G4: SLA Timer NIS2/GDPR */}
        <Grid item xs={12} md={6}>
          <Card sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>G4 · SLA Timer NIS2/GDPR</Typography>
            <SLATimerChart items={enterprise.k2_nis2_sla.items} />
          </Card>
        </Grid>

        {/* G5: Agent Execution Trace */}
        <Grid item xs={12} md={6}>
          <Card sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>G5 · Agent Execution Trace</Typography>
            <AgentExecutionTrace />
          </Card>
        </Grid>

        {/* G6: RAG Pipeline Health */}
        <Grid item xs={12} md={6}>
          <Card sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>G6 · RAG Pipeline Health</Typography>
            <RAGPipelineHealth />
          </Card>
        </Grid>

        {/* G7: PII Exposure Heatmap */}
        <Grid item xs={12} md={6}>
          <Card sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>G7 · PII Exposure Heatmap</Typography>
            <PIIExposureHeatmap />
          </Card>
        </Grid>

        {/* G8: Hallucination & Drift Monitor */}
        <Grid item xs={12} md={6}>
          <Card sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>G8 · Hallucination & Drift Monitor</Typography>
            <HallucinationDriftMonitor />
          </Card>
        </Grid>

        {/* G9: Denial-of-Wallet Monitor */}
        <Grid item xs={12} md={6}>
          <Card sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>G9 · Denial-of-Wallet Monitor</Typography>
            <DoWMonitor />
          </Card>
        </Grid>

        {/* G10: Immutable Audit Chain Table */}
        <Grid item xs={12} md={6}>
          <Card sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>G10 · Immutable Audit Chain</Typography>
            <AuditChainTable />
          </Card>
        </Grid>

        {/* G11: Bias & Fairness Monitor */}
        <Grid item xs={12} md={8}>
          <Card sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>G11 · Bias & Fairness Monitor</Typography>
            <BiasFairnessRadar />
          </Card>
        </Grid>

        {/* G12: Notification Center Treemap */}
        <Grid item xs={12} md={4}>
          <Card sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>G12 · Notification Center</Typography>
            <NotificationTreemap />
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
