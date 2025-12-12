import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import DescriptionIcon from '@mui/icons-material/Description';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuth } from '../hooks/useAuth.js';

export function LandingPage() {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();

  // اگر کاربر لاگین شده باشد، به صفحه مناسب redirect کن
  useEffect(() => {
    if (isAuthenticated) {
      const isAdmin = user?.username?.toLowerCase().startsWith('admin') || user?.username?.toLowerCase() === 'expert' || user?.role === 'expert';
      if (isAdmin) {
        navigate('/admin/uploads', { replace: true });
      } else {
        navigate('/invoices', { replace: true });
      }
    }
  }, [isAuthenticated, user, navigate]);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: '#f5f5f5',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        direction: 'rtl',
        py: 4,
      }}
    >
      <Container maxWidth="sm">
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 4 }}>
          <Box
            sx={{
              width: 64,
              height: 64,
              bgcolor: '#4CAF50',
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mb: 2,
            }}
          >
            <DescriptionIcon sx={{ fontSize: 40, color: 'white' }} />
          </Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 0.5 }}>
            سامانه فاکتور
          </Typography>
          <Typography variant="body1" color="text.secondary">
            مدیریت فاکتورهای پیمانکاران
          </Typography>
        </Box>

        <Paper
          elevation={0}
          sx={{
            p: 4,
            borderRadius: 3,
            bgcolor: 'white',
            display: 'flex',
            flexDirection: 'column',
            gap: 3,
          }}
        >
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 0.5, textAlign: 'center' }}>
              ورود به سیستم
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
              لطفاً نوع ورود خود را انتخاب کنید
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Button
              variant="contained"
              fullWidth
              size="large"
              onClick={() => navigate('/login?role=contractor')}
              sx={{
                py: 1.5,
                borderRadius: 2,
                bgcolor: '#2196F3',
                '&:hover': {
                  bgcolor: '#1976D2',
                },
                fontWeight: 'bold',
              }}
            >
              ورود پیمانکار
            </Button>

            <Button
              variant="outlined"
              fullWidth
              size="large"
              onClick={() => navigate('/login?role=expert')}
              sx={{
                py: 1.5,
                borderRadius: 2,
                borderColor: '#2196F3',
                color: '#2196F3',
                '&:hover': {
                  borderColor: '#1976D2',
                  bgcolor: '#E3F2FD',
                },
                fontWeight: 'bold',
              }}
            >
              ورود کارشناس بازرگانی
            </Button>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
}

export default LandingPage;


