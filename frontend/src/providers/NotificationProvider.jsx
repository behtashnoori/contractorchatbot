import { createContext, useContext, useState, useCallback, useMemo } from 'react';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import Slide from '@mui/material/Slide';

const NotificationContext = createContext({
  showNotification: () => {},
});

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider');
  }
  return context;
};

function SlideTransition(props) {
  return <Slide {...props} direction="up" />;
}

export function NotificationProvider({ children }) {
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info', // 'success', 'error', 'warning', 'info'
    duration: 4000,
  });

  const showNotification = useCallback((message, severity = 'info', duration = 4000) => {
    setNotification({
      open: true,
      message,
      severity,
      duration,
    });
  }, []);

  const handleClose = useCallback((event, reason) => {
    if (reason === 'clickaway') {
      return;
    }
    setNotification((prev) => ({ ...prev, open: false }));
  }, []);

  // Convenience methods
  const showSuccess = useCallback(
    (message, duration) => showNotification(message, 'success', duration),
    [showNotification],
  );

  const showError = useCallback(
    (message, duration) => showNotification(message, 'error', duration),
    [showNotification],
  );

  const showWarning = useCallback(
    (message, duration) => showNotification(message, 'warning', duration),
    [showNotification],
  );

  const showInfo = useCallback(
    (message, duration) => showNotification(message, 'info', duration),
    [showNotification],
  );

  const value = useMemo(
    () => ({
      showNotification,
      showSuccess,
      showError,
      showWarning,
      showInfo,
    }),
    [showNotification, showSuccess, showError, showWarning, showInfo],
  );

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <Snackbar
        open={notification.open}
        autoHideDuration={notification.duration}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        TransitionComponent={SlideTransition}
        sx={{ direction: 'rtl' }}
      >
        <Alert
          onClose={handleClose}
          severity={notification.severity}
          variant="filled"
          sx={{ width: '100%', direction: 'rtl' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </NotificationContext.Provider>
  );
}

