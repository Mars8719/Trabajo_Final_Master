// Polyfill: React scheduler expects performance.clearMarks/measure
if (typeof window !== 'undefined' && window.performance) {
  if (typeof window.performance.clearMarks !== 'function') {
    window.performance.clearMarks = () => {};
  }
  if (typeof window.performance.clearMeasures !== 'function') {
    window.performance.clearMeasures = () => {};
  }
  if (typeof window.performance.mark !== 'function') {
    window.performance.mark = (() => {}) as any;
  }
  if (typeof window.performance.measure !== 'function') {
    window.performance.measure = (() => {}) as any;
  }
}

import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { store } from './store/store';
import { theme } from './theme';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ThemeProvider>
    </Provider>
  </React.StrictMode>
);
