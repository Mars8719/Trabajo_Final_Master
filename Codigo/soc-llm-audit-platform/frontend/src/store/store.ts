import { configureStore, createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Alert {
  id: string;
  source: string;
  severity_score: number;
  compliance_score: number;
  hitl_level: number;
  hitl_status: string;
  classification: string;
  created_at: string;
}

interface DashboardKPIs {
  alerts: { total: number; last_24h: number };
  compliance: { average_score: number; non_compliant_count: number };
  hitl: { pending_reviews: number; total_decisions: number };
  incidents: { active: number };
  bias: { tests_passed: number; tests_total: number };
  system_status: string;
}

interface AppState {
  alerts: Alert[];
  kpis: DashboardKPIs | null;
  hitlQueue: Alert[];
  loading: boolean;
  error: string | null;
}

const initialState: AppState = {
  alerts: [],
  kpis: null,
  hitlQueue: [],
  loading: false,
  error: null,
};

const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    setAlerts: (state, action: PayloadAction<Alert[]>) => {
      state.alerts = action.payload;
    },
    addAlert: (state, action: PayloadAction<Alert>) => {
      state.alerts.unshift(action.payload);
    },
    setKPIs: (state, action: PayloadAction<DashboardKPIs>) => {
      state.kpis = action.payload;
    },
    setHITLQueue: (state, action: PayloadAction<Alert[]>) => {
      state.hitlQueue = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const { setAlerts, addAlert, setKPIs, setHITLQueue, setLoading, setError } = appSlice.actions;

export const store = configureStore({
  reducer: { app: appSlice.reducer },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
