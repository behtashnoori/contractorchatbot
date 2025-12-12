import { createTheme } from '@mui/material/styles';

const theme = createTheme({
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
        },
      },
    },
  },
});

export default theme;

