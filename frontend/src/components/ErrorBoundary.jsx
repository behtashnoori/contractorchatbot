import React from 'react';
import PropTypes from 'prop-types';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';

const isDev = import.meta.env.DEV;

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    if (isDev) {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
      console.error('Error details:', {
        message: error?.message,
        stack: error?.stack,
        componentStack: errorInfo?.componentStack,
      });
    }
    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            p: 3,
            bgcolor: 'background.default',
            direction: 'rtl',
          }}
        >
          <Box sx={{ maxWidth: 600, width: '100%' }}>
            <Alert severity="error" icon={<ErrorOutlineIcon />} sx={{ mb: 2 }}>
              <Typography variant="h6" sx={{ mb: 1 }}>
                خطایی رخ داد
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                {isDev && this.state.error?.message
                  ? this.state.error.message
                  : 'یک خطای غیرمنتظره رخ داد. لطفاً صفحه را بارگذاری مجدد کنید.'}
              </Typography>
              {isDev && (
                <Box
                  component="pre"
                  sx={{
                    mt: 2,
                    p: 2,
                    bgcolor: 'background.paper',
                    borderRadius: 1,
                    fontSize: '0.75rem',
                    overflow: 'auto',
                    maxHeight: 200,
                    direction: 'ltr',
                    textAlign: 'left',
                  }}
                >
                  {this.state.error?.stack || 'No stack trace available'}
                </Box>
              )}
            </Alert>
            <Button variant="contained" onClick={this.handleReset} fullWidth sx={{ mt: 2 }}>
              بارگذاری مجدد صفحه
            </Button>
          </Box>
        </Box>
      );
    }

    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
};
