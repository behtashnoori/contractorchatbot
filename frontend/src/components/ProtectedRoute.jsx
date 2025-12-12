import PropTypes from 'prop-types';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth.js';

export function ProtectedRoute({ redirectTo = '/login' }) {
  const location = useLocation();
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="page-loader">در حال بارگذاری...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to={redirectTo} replace state={{ from: location }} />;
  }

  return <Outlet />;
}

ProtectedRoute.propTypes = {
  redirectTo: PropTypes.string,
};

