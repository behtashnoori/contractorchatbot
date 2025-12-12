import PropTypes from 'prop-types';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Divider from '@mui/material/Divider';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import DescriptionIcon from '@mui/icons-material/Description';
import LogoutIcon from '@mui/icons-material/Logout';
import { useAuth } from '../hooks/useAuth.js';

export function AppLayout({ title, actions, children }) {
  const location = useLocation();
  const { contractor, logout, user } = useAuth();
  const isAdmin = user?.username?.toLowerCase().startsWith('admin') || user?.username?.toLowerCase() === 'expert';

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#f5f5f5', color: 'text.primary', direction: 'rtl' }}>
      <AppBar
        position="static"
        sx={{
          bgcolor: '#1976D2',
          boxShadow: 'none',
        }}
      >
        <Toolbar sx={{ display: 'flex', justifyContent: 'space-between', py: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                width: 40,
                height: 40,
                bgcolor: '#4CAF50',
                borderRadius: 1.5,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <DescriptionIcon sx={{ fontSize: 24, color: 'white' }} />
            </Box>
            <Box>
              <Typography variant="h6" component="div" sx={{ fontWeight: 'bold', lineHeight: 1.2 }}>
                سامانه فاکتور
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.9, fontSize: '0.75rem' }}>
                مدیریت فاکتورهای پیمانکاران
              </Typography>
            </Box>
            {isAdmin && (
              <Box sx={{ display: 'flex', gap: 1, mr: 2 }}>
                <Button
                  component={RouterLink}
                  to="/admin/uploads"
                  color={location.pathname.startsWith('/admin') ? 'secondary' : 'inherit'}
                  size="small"
                  sx={{
                    '&:hover': {
                      bgcolor: 'rgba(255, 255, 255, 0.1)',
                    },
                  }}
                >
                  بارگذاری داده‌ها
                </Button>
              </Box>
            )}
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {contractor ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.95rem' }}>
                  {contractor.name || 'پیمانکار'}
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.9, fontSize: '0.75rem' }}>
                  {contractor.supplier_code ? `کد تامین‌کننده: ${contractor.supplier_code}` : ''} {contractor.detail_code ? `(${contractor.detail_code})` : ''}
                </Typography>
              </Box>
            ) : isAdmin ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.95rem' }}>
                  کارشناس بازرگانی
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.9, fontSize: '0.75rem' }}>
                  {user?.username || 'کاربر'}
                </Typography>
              </Box>
            ) : (
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                کاربر
              </Typography>
            )}
            <Button
              color="inherit"
              onClick={logout}
              startIcon={<LogoutIcon />}
              sx={{
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              خروج
            </Button>
          </Box>
        </Toolbar>
      </AppBar>
      <Container maxWidth="xl" sx={{ py: 4, px: { xs: 2, sm: 3, md: 4 } }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <Box sx={{ display: 'flex', flexDirection: 'row-reverse', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                {title}
              </Typography>
            </Box>
            <Box>{actions}</Box>
          </Box>
          <Divider />
          {children}
        </Box>
      </Container>
    </Box>
  );
}

AppLayout.propTypes = {
  title: PropTypes.string.isRequired,
  actions: PropTypes.node,
  children: PropTypes.node.isRequired,
};

