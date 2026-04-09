import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

export const alertsApi = {
  ingest: (data: Record<string, unknown>) => api.post('/alerts/ingest', data),
  getById: (id: string) => api.get(`/alerts/${id}`),
  getExplanation: (id: string) => api.get(`/alerts/${id}/explanation`),
};

export const complianceApi = {
  getScores: (params?: Record<string, unknown>) => api.get('/compliance/scores', { params }),
  getDashboard: () => api.get('/compliance/dashboard'),
  getTrends: (days = 30) => api.get('/compliance/trends', { params: { days } }),
};

export const hitlApi = {
  getQueue: () => api.get('/hitl/queue'),
  submitDecision: (alertId: string, data: Record<string, unknown>) =>
    api.post(`/hitl/${alertId}/decision`, data),
  activateKillSwitch: (data: { reason: string; activated_by: string }) =>
    api.post('/hitl/kill-switch', data),
  deactivateKillSwitch: () => api.post('/hitl/kill-switch/deactivate'),
};

export const auditApi = {
  getTrail: (params?: Record<string, unknown>) => api.get('/audit/trail', { params }),
  exportTrail: (params?: Record<string, unknown>) => api.get('/audit/export', { params }),
  verifyIntegrity: () => api.get('/audit/verify'),
};

export const dpiaApi = {
  generate: (data: { system_description: string }) => api.post('/dpia/generate', data),
  list: () => api.get('/dpia/list'),
  getRiskMatrix: (id: string) => api.get(`/dpia/${id}/risk-matrix`),
};

export const incidentsApi = {
  create: (data: Record<string, unknown>) => api.post('/incidents/report', data),
  update: (id: string, data: Record<string, unknown>) => api.put(`/incidents/${id}/update`, data),
  list: () => api.get('/incidents/'),
};

export const biasApi = {
  getResults: () => api.get('/bias/results'),
  runTest: (data: Record<string, unknown>) => api.post('/bias/run', data),
};

export const dashboardApi = {
  getKPIs: () => api.get('/dashboard/kpis'),
  getEnterpriseKPIs: () => api.get('/dashboard/kpis/enterprise'),
  getRiskMonitor: () => api.get('/dashboard/risk-monitor'),
  getRiskAlerts: () => api.get('/dashboard/risk-monitor/alerts'),
};

export const driftApi = {
  getStatus: () => api.get('/drift/status'),
};

export const finopsApi = {
  getCosts: () => api.get('/finops/costs'),
  getSummary: () => api.get('/finops/summary'),
};

export default api;
