import { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import {
  Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText,
  AppBar, Toolbar, Typography, IconButton,
} from '@mui/material';
import {
  Dashboard as DashboardIcon, Warning, Gavel, Psychology, Assessment,
  BugReport, Description, Shield, Settings as SettingsIcon, Menu,
  Timeline, BalanceOutlined,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

import DashboardPage from './pages/Dashboard';
import AlertTriagePage from './pages/AlertTriage';
import HITLQueuePage from './pages/HITLQueue';
import ComplianceScoresPage from './pages/ComplianceScores';
import BiasReportsPage from './pages/BiasReports';
import AuditTrailPage from './pages/AuditTrail';
import DPIAManagerPage from './pages/DPIAManager';
import IncidentReportingPage from './pages/IncidentReporting';
import ExplainabilityPage from './pages/Explainability';
import SettingsPage from './pages/Settings';

const drawerWidth = 260;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Alert Triage', icon: <Warning />, path: '/alerts' },
  { text: 'HITL Queue', icon: <Psychology />, path: '/hitl' },
  { text: 'Compliance Scores', icon: <Gavel />, path: '/compliance' },
  { text: 'Bias Reports', icon: <BalanceOutlined />, path: '/bias' },
  { text: 'Audit Trail', icon: <Timeline />, path: '/audit' },
  { text: 'DPIA Manager', icon: <Description />, path: '/dpia' },
  { text: 'Incident Reporting', icon: <BugReport />, path: '/incidents' },
  { text: 'Explainability', icon: <Assessment />, path: '/explainability' },
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
];

export default function App() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const drawer = (
    <Box>
      <Toolbar>
        <Shield sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6" noWrap sx={{ fontWeight: 700 }}>
          SOC-LLM
        </Typography>
      </Toolbar>
      <List>
        {menuItems.map((item) => (
          <ListItemButton
            key={item.text}
            selected={location.pathname === item.path}
            onClick={() => navigate(item.path)}
            sx={{
              mx: 1, borderRadius: 2, mb: 0.5,
              '&.Mui-selected': { bgcolor: 'rgba(0,176,255,0.12)' },
            }}
          >
            <ListItemIcon sx={{ minWidth: 40, color: location.pathname === item.path ? 'primary.main' : 'inherit' }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1, bgcolor: 'background.paper', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <Toolbar>
          <IconButton color="inherit" edge="start" onClick={() => setMobileOpen(!mobileOpen)} sx={{ mr: 2, display: { sm: 'none' } }}>
            <Menu />
          </IconButton>
          <Typography variant="h6" noWrap sx={{ flexGrow: 1 }}>
            Módulo de Auditoría Ético-Normativa
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            GDPR · NIS2 · EU AI Act
          </Typography>
        </Toolbar>
      </AppBar>

      <Box component="nav" sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}>
        <Drawer variant="temporary" open={mobileOpen} onClose={() => setMobileOpen(false)}
          sx={{ display: { xs: 'block', sm: 'none' }, '& .MuiDrawer-paper': { width: drawerWidth } }}>
          {drawer}
        </Drawer>
        <Drawer variant="permanent"
          sx={{ display: { xs: 'none', sm: 'block' }, '& .MuiDrawer-paper': { width: drawerWidth, boxSizing: 'border-box', bgcolor: 'background.paper', borderRight: '1px solid rgba(255,255,255,0.08)' } }}
          open>
          {drawer}
        </Drawer>
      </Box>

      <Box component="main" sx={{ flexGrow: 1, p: 3, width: { sm: `calc(100% - ${drawerWidth}px)` } }}>
        <Toolbar />
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/alerts" element={<AlertTriagePage />} />
          <Route path="/hitl" element={<HITLQueuePage />} />
          <Route path="/compliance" element={<ComplianceScoresPage />} />
          <Route path="/bias" element={<BiasReportsPage />} />
          <Route path="/audit" element={<AuditTrailPage />} />
          <Route path="/dpia" element={<DPIAManagerPage />} />
          <Route path="/incidents" element={<IncidentReportingPage />} />
          <Route path="/explainability" element={<ExplainabilityPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Box>
    </Box>
  );
}
