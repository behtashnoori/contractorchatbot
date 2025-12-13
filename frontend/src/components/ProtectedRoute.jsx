import PropTypes from 'prop-types';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import { useAuth } from '../hooks/useAuth.js';

export function ProtectedRoute({ redirectTo = '/login' }) {
  const location = useLocation();
  const { isAuthenticated, loading } = useAuth();

  console.log('[ProtectedRoute] Loading:', loading, 'Authenticated:', isAuthenticated);

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 2,
          direction: 'rtl',
          bgcolor: 'background.default',
        }}
      >
        <CircularProgress />
        <Typography variant="body1" color="text.secondary">
          در حال بارگذاری...
        </Typography>
      </Box>
    );
  }

  if (!isAuthenticated) {
    console.log('[ProtectedRoute] Not authenticated, redirecting to login');
    return <Navigate to={redirectTo} replace state={{ from: location }} />;
  }

  console.log('[ProtectedRoute] Authenticated, rendering outlet');
  return <Outlet />;
}

ProtectedRoute.propTypes = {
  redirectTo: PropTypes.string,
};

