import PropTypes from 'prop-types';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import DescriptionIcon from '@mui/icons-material/Description';

const getIcon = (color) => {
  switch (color) {
    case 'success':
      return <CheckCircleIcon sx={{ fontSize: 28 }} />;
    case 'warning':
      return <AccessTimeIcon sx={{ fontSize: 28 }} />;
    case 'info':
      return <DescriptionIcon sx={{ fontSize: 28 }} />;
    default:
      return <DescriptionIcon sx={{ fontSize: 28 }} />;
  }
};

const getStatusText = (color) => {
  switch (color) {
    case 'success':
      return 'آماده پرداخت';
    case 'warning':
      return 'در حال بررسی';
    case 'info':
      return 'فاکتور ثبت شده';
    default:
      return '';
  }
};

const getColorConfig = (color) => {
  switch (color) {
    case 'success':
      return {
        iconBg: '#E8F5E9',
        iconColor: '#4CAF50',
        borderColor: '#4CAF50',
      };
    case 'warning':
      return {
        iconBg: '#FFF3E0',
        iconColor: '#FF9800',
        borderColor: '#FF9800',
      };
    case 'info':
      return {
        iconBg: '#E3F2FD',
        iconColor: '#2196F3',
        borderColor: '#2196F3',
      };
    default:
      return {
        iconBg: '#E3F2FD',
        iconColor: '#2196F3',
        borderColor: '#2196F3',
      };
  }
};

export function SummaryCard({ label, value, color = 'primary' }) {
  const colorConfig = getColorConfig(color);
  const isNumber = typeof value === 'number' || (typeof value === 'string' && !value.includes('ریال'));

  return (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        flex: 1,
        display: 'flex',
        flexDirection: 'row-reverse',
        alignItems: 'center',
        gap: 2,
        borderRadius: 2,
        bgcolor: 'white',
        border: `1px solid ${colorConfig.borderColor}20`,
        transition: 'all 0.3s ease',
        '&:hover': {
          boxShadow: 2,
          transform: 'translateY(-2px)',
        },
      }}
    >
      <Box
        sx={{
          width: 56,
          height: 56,
          borderRadius: '50%',
          bgcolor: colorConfig.iconBg,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        <Box sx={{ color: colorConfig.iconColor }}>{getIcon(color)}</Box>
      </Box>
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
          {label}
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'row-reverse', alignItems: 'baseline', gap: 0.5, flexWrap: 'wrap' }}>
          <Typography variant="h5" sx={{ fontWeight: 'bold', color: colorConfig.borderColor }}>
            {value}
          </Typography>
          {isNumber && (
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
              ریال
            </Typography>
          )}
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem', mt: 0.5 }}>
          {getStatusText(color)}
        </Typography>
      </Box>
    </Paper>
  );
}

SummaryCard.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  color: PropTypes.string,
};

