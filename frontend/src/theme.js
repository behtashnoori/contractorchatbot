import { createTheme } from '@mui/material/styles';

const commonTheme = {
  direction: 'rtl',
  typography: {
    fontFamily: "'Vazirmatn', 'Segoe UI', 'Tahoma', 'Arial', sans-serif",
    h1: {
      fontWeight: 700,
      fontSize: '2.5rem',
      lineHeight: 1.2,
    },
    h2: {
      fontWeight: 700,
      fontSize: '2rem',
      lineHeight: 1.3,
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.75rem',
      lineHeight: 1.3,
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.5rem',
      lineHeight: 1.4,
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.25rem',
      lineHeight: 1.4,
    },
    h6: {
      fontWeight: 600,
      fontSize: '1.125rem',
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
      fontWeight: 400,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.6,
      fontWeight: 400,
    },
    button: {
      fontWeight: 500,
      textTransform: 'none',
    },
    subtitle1: {
      fontSize: '1rem',
      lineHeight: 1.6,
      fontWeight: 500,
    },
    subtitle2: {
      fontSize: '0.875rem',
      lineHeight: 1.6,
      fontWeight: 500,
    },
    caption: {
      fontSize: '0.75rem',
      lineHeight: 1.5,
      fontWeight: 400,
    },
  },
  components: {
    MuiTypography: {
      styleOverrides: {
        root: {
          fontFamily: "'Vazirmatn', 'Segoe UI', 'Tahoma', 'Arial', sans-serif",
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          fontFamily: "'Vazirmatn', 'Segoe UI', 'Tahoma', 'Arial', sans-serif",
          borderRadius: 8,
          fontWeight: 500,
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-1px)',
            boxShadow: 2,
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          fontFamily: "'Vazirmatn', 'Segoe UI', 'Tahoma', 'Arial', sans-serif",
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          fontFamily: "'Vazirmatn', 'Segoe UI', 'Tahoma', 'Arial', sans-serif",
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontFamily: "'Vazirmatn', 'Segoe UI', 'Tahoma', 'Arial', sans-serif",
          transition: 'all 0.2s ease-in-out',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          transition: 'all 0.3s ease-in-out',
          '&:hover': {
            transform: 'translateY(-2px)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          transition: 'all 0.3s ease-in-out',
        },
      },
    },
  },
};

// Theme
const theme = createTheme({
  ...commonTheme,
  palette: {
    mode: 'light',
    primary: {
      main: '#1976D2',
      light: '#42A5F5',
      dark: '#1565C0',
    },
    secondary: {
      main: '#9C27B0',
      light: '#BA68C8',
      dark: '#7B1FA2',
    },
    success: {
      main: '#4CAF50',
      light: '#81C784',
      dark: '#2E7D32',
    },
    warning: {
      main: '#FF9800',
      light: '#FFB74D',
      dark: '#F57C00',
    },
    error: {
      main: '#F44336',
      light: '#E57373',
      dark: '#C62828',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
    text: {
      primary: 'rgba(0, 0, 0, 0.87)',
      secondary: 'rgba(0, 0, 0, 0.6)',
    },
  },
});

export default theme;

