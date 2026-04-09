import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#00b0ff' },
    secondary: { main: '#651fff' },
    error: { main: '#ff1744' },
    warning: { main: '#ff9100' },
    success: { main: '#00e676' },
    background: {
      default: '#0a1929',
      paper: '#0d2137',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: { fontWeight: 700 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          border: '1px solid rgba(255,255,255,0.08)',
        },
      },
    },
  },
});
