import { lazy, Suspense } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
import { ProtectedRoute } from './components/ProtectedRoute.jsx';

const LoginPage = lazy(() => import('./pages/LoginPage.jsx').then((module) => ({ default: module.LoginPage })));
const LandingPage = lazy(() => import('./pages/LandingPage.jsx').then((module) => ({ default: module.LandingPage })));
const DashboardPage = lazy(() =>
  import('./pages/DashboardPage.jsx').then((module) => ({ default: module.DashboardPage })),
);
const InvoiceDetailPage = lazy(() =>
  import('./pages/InvoiceDetailPage.jsx').then((module) => ({ default: module.InvoiceDetailPage })),
);
const AdminUploadPage = lazy(() =>
  import('./pages/AdminUploadPage.jsx').then((module) => ({ default: module.AdminUploadPage })),
);

function LoadingScreen() {
  return (
    <Box sx={{ width: '100%', py: 10, display: 'flex', justifyContent: 'center' }}>
      <CircularProgress />
    </Box>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingScreen />}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/invoices" element={<DashboardPage />} />
            <Route path="/invoice/:coverNumber" element={<InvoiceDetailPage />} />
            <Route path="/admin/uploads" element={<AdminUploadPage />} />
          </Route>
          <Route path="*" element={<LandingPage />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
