import { useMemo, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Container from '@mui/material/Container';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import InfoIcon from '@mui/icons-material/Info';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PersonIcon from '@mui/icons-material/Person';
import LockIcon from '@mui/icons-material/Lock';
import DescriptionIcon from '@mui/icons-material/Description';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import { useAuth } from '../hooks/useAuth.js';
import { useNotification } from '../hooks/useNotification.js';

export function LoginPage() {
  const { login } = useAuth();
  const { showSuccess, showError } = useNotification();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [welcomeMessage, setWelcomeMessage] = useState(null);

  const role = useMemo(() => {
    const params = new URLSearchParams(location.search);
    const r = params.get('role');
    return r === 'expert' ? 'expert' : 'contractor';
  }, [location.search]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setWelcomeMessage(null);
    try {
      const loginData = await login({ username: form.username.trim().toLowerCase(), password: form.password });
      
      // نمایش پیام خوش‌آمدگویی اگر contractor وجود داشته باشد
      if (loginData.contractor?.name) {
        setLoading(false);
        const welcomeMsg = `سلام ${loginData.contractor.name}! خوش آمدید.`;
        setWelcomeMessage(welcomeMsg);
        showSuccess(welcomeMsg);
        // بعد از 2 ثانیه redirect می‌کنیم
        setTimeout(() => {
          const redirect = location.state?.from?.pathname || (role === 'expert' ? '/admin/uploads' : '/invoices');
          navigate(redirect, { replace: true });
        }, 2000);
      } else {
        // اگر contractor نبود، فوراً redirect می‌کنیم
        setLoading(false);
        showSuccess('ورود موفقیت‌آمیز بود');
        const redirect = location.state?.from?.pathname || (role === 'expert' ? '/admin/uploads' : '/invoices');
        navigate(redirect, { replace: true });
      }
    } catch (err) {
      // استفاده از message از backend اگر موجود باشد، در غیر این صورت error code
      const errorData = err.response?.data;
      let message = errorData?.message || errorData?.error || 'خطا در ورود. لطفاً دوباره تلاش کنید.';
      
      // اگر error code مربوط به not_found یا invalid_credentials است
      if (errorData?.error === 'not_found' || errorData?.error === 'invalid_credentials') {
        message = 'اطلاعات شما در سیستم یافت نشد. لطفاً با کارشناس بازرگانی تماس بگیرید.';
      } else if (errorData?.error === 'inactive_contractor') {
        message = errorData?.message || 'حساب کاربری شما غیرفعال است. لطفاً با کارشناس بازرگانی تماس بگیرید.';
      }
      
      setError(message);
      showError(message);
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: 'background.default',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        direction: 'rtl',
        py: 4,
      }}
    >
      <Container maxWidth="sm">
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            mb: 4,
            animation: 'fadeInDown 0.5s ease-out',
            '@keyframes fadeInDown': {
              from: { opacity: 0, transform: 'translateY(-20px)' },
              to: { opacity: 1, transform: 'translateY(0)' },
            },
          }}
        >
          <Box
            sx={{
              width: 64,
              height: 64,
              bgcolor: 'success.main',
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mb: 2,
              boxShadow: 2,
              transition: 'transform 0.3s ease',
              '&:hover': {
                transform: 'scale(1.05)',
              },
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
          elevation={2}
          sx={{
            p: 4,
            borderRadius: 3,
            bgcolor: 'background.paper',
            display: 'flex',
            flexDirection: 'column',
            gap: 3,
            animation: 'fadeInUp 0.5s ease-out',
            '@keyframes fadeInUp': {
              from: { opacity: 0, transform: 'translateY(20px)' },
              to: { opacity: 1, transform: 'translateY(0)' },
            },
          }}
        >
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 0.5 }}>
              {role === 'expert' ? 'ورود کارشناس بازرگانی' : 'ورود به سیستم'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {role === 'expert' ? 'برای دسترسی به پنل مدیریت وارد شوید' : 'برای دسترسی به فاکتورها وارد شوید'}
            </Typography>
          </Box>

          {error ? (
            <Alert severity="error" sx={{ textAlign: 'right' }}>
              {error}
            </Alert>
          ) : null}

          {welcomeMessage ? (
            <Alert 
              severity="success" 
              sx={{ 
                textAlign: 'right',
                bgcolor: '#E8F5E9',
                color: '#2E7D32',
                '& .MuiAlert-icon': {
                  color: '#4CAF50',
                },
              }}
            >
              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                {welcomeMessage}
              </Typography>
              <Typography variant="caption" sx={{ display: 'block', mt: 0.5, opacity: 0.8 }}>
                در حال انتقال...
              </Typography>
            </Alert>
          ) : null}

          <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
            <TextField
              label="نام کاربری"
              name="username"
              value={form.username}
              onChange={handleChange}
              required
              placeholder={role === 'expert' ? 'نام کاربری' : 'کد تفصیلی_کد تامین کننده'}
              InputLabelProps={{ shrink: true }}
              InputProps={{
                startAdornment: (
                  <Box sx={{ ml: 1, display: 'flex', alignItems: 'center' }}>
                    <PersonIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                  </Box>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  bgcolor: 'background.default',
                  transition: 'all 0.2s ease',
                  '& fieldset': {
                    borderColor: 'divider',
                  },
                  '&:hover fieldset': {
                    borderColor: 'primary.main',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: 'primary.main',
                    borderWidth: 2,
                  },
                },
              }}
              autoComplete="username"
              dir="rtl"
            />
            <TextField
              label="رمز عبور"
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              required
              InputLabelProps={{ shrink: true }}
              InputProps={{
                startAdornment: (
                  <Box sx={{ ml: 1, display: 'flex', alignItems: 'center' }}>
                    <LockIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                  </Box>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  bgcolor: 'background.default',
                  transition: 'all 0.2s ease',
                  '& fieldset': {
                    borderColor: 'divider',
                  },
                  '&:hover fieldset': {
                    borderColor: 'primary.main',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: 'primary.main',
                    borderWidth: 2,
                  },
                },
              }}
              autoComplete="current-password"
              dir="rtl"
            />
            <Button
              type="submit"
              variant="contained"
              disabled={loading}
              fullWidth
              sx={{
                py: 1.5,
                borderRadius: 2,
                fontWeight: 'bold',
                transition: 'all 0.2s ease',
              }}
            >
              {loading ? <CircularProgress size={20} color="inherit" /> : 'ورود به سیستم'}
            </Button>
          </Box>

          {role === 'contractor' && (
            <Accordion sx={{ boxShadow: 'none', '&:before': { display: 'none' } }}>
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                sx={{
                  px: 0,
                  '& .MuiAccordionSummary-content': {
                    my: 0,
                  },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <HelpOutlineIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                  <Typography variant="body2" color="text.secondary">
                    راهنمای ورود پیمانکاران
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails sx={{ px: 0, pt: 0 }}>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  <Typography variant="body2" color="text.secondary">
                    <strong>نام کاربری:</strong> کد تفصیلی_کد تامین‌کننده
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    <strong>رمز عبور:</strong> کد تفصیلی@کد تامین‌کننده
                  </Typography>
                  <Box sx={{ mt: 1, p: 1.5, bgcolor: 'info.light', borderRadius: 1 }}>
                    <Typography variant="caption" component="div" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                      مثال:
                    </Typography>
                    <Typography variant="caption" component="div">
                      اگر کد تفصیلی شما <strong>26968</strong> و کد تامین‌کننده <strong>732</strong> است:
                    </Typography>
                    <Typography variant="caption" component="div" sx={{ mt: 0.5 }}>
                      نام کاربری: <strong>26968_732</strong>
                    </Typography>
                    <Typography variant="caption" component="div">
                      رمز عبور: <strong>26968@732</strong>
                    </Typography>
                    <Alert severity="warning" sx={{ mt: 1, fontSize: '0.75rem' }}>
                      <Typography variant="caption" component="div">
                        <strong>توجه:</strong> ترتیب مهم است! ابتدا کد تفصیلی، سپس کد تامین‌کننده
                      </Typography>
                    </Alert>
                  </Box>
                  <Alert severity="info" sx={{ mt: 1 }}>
                    <Typography variant="caption">
                      در صورت بروز مشکل در ورود، لطفاً با کارشناس بازرگانی تماس بگیرید.
                    </Typography>
                  </Alert>
                </Box>
              </AccordionDetails>
            </Accordion>
          )}
        </Paper>
      </Container>
    </Box>
  );
}
