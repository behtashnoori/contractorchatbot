import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TableContainer from '@mui/material/TableContainer';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import Grid from '@mui/material/Grid';
import Divider from '@mui/material/Divider';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import HashIcon from '@mui/icons-material/Tag';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import dayjs from 'dayjs';
import jalaliday from 'jalaliday';
import { useQuery } from '@tanstack/react-query';
import { fetchInvoiceDetail } from '../api/invoices.js';
import { AppLayout } from '../components/AppLayout.jsx';
import { StatusChip } from '../components/StatusChip.jsx';
import { getStatusVisuals } from '../utils/status.js';

dayjs.extend(jalaliday);

const formatDate = (date) => (date ? dayjs(date).calendar('jalali').format('YYYY/MM/DD') : '-');

export function InvoiceDetailPage() {
  const { coverNumber } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['invoice-detail', coverNumber],
    queryFn: () => fetchInvoiceDetail(coverNumber),
  });

  const summary = data?.summary;
  const detailRows = data?.details ?? [];
  const summaryStatusVisuals = getStatusVisuals(summary?.invoice_status);

  if (isLoading) {
    return (
      <AppLayout title={`جزئیات روکش ${coverNumber}`}>
        <Box sx={{ py: 10, display: 'flex', justifyContent: 'center' }}>
          <CircularProgress />
        </Box>
      </AppLayout>
    );
  }

  if (isError) {
    return (
      <AppLayout title={`جزئیات روکش ${coverNumber}`}>
        <Alert
          severity="error"
          sx={{ my: 4, direction: 'rtl' }}
          action={
            <Button color="inherit" size="small" onClick={() => refetch()}>
              تلاش مجدد
            </Button>
          }
        >
          {error?.response?.data?.error || 'خطا در دریافت اطلاعات'}
        </Alert>
      </AppLayout>
    );
  }

  return (
    <AppLayout
      title={`جزئیات روکش ${coverNumber}`}
      actions={
        <Button variant="outlined" onClick={() => navigate(-1)}>
          بازگشت
        </Button>
      }
    >
      <Paper
        sx={{
          p: 3,
          borderRadius: 2,
          bgcolor: 'background.paper',
          transition: 'all 0.3s ease',
          animation: 'fadeIn 0.3s ease-in',
          '@keyframes fadeIn': {
            from: { opacity: 0, transform: 'translateY(10px)' },
            to: { opacity: 1, transform: 'translateY(0)' },
          },
        }}
        elevation={1}
      >
        <Typography variant="h6" sx={{ mb: 3, fontWeight: 'bold' }}>
          اطلاعات روکش
        </Typography>

        {/* باکس‌های سال مالی و وضعیت */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {data?.summary?.fiscal_year && (
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card elevation={0} sx={{ bgcolor: 'background.default', borderRadius: 2 }}>
                <CardContent>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                    سال مالی
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                    {data.summary.fiscal_year}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}
          {data?.summary?.invoice_status && (
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card elevation={0} sx={{ bgcolor: 'background.default', borderRadius: 2 }}>
                <CardContent>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                    وضعیت
                  </Typography>
                  <StatusChip status={data.summary.invoice_status} />
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>

        {/* چهار تاریخ در بالا */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card elevation={0} sx={{ bgcolor: 'background.default', borderRadius: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <CalendarTodayIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                  <Typography variant="caption" color="text.secondary">
                    تاریخ ایجاد فاکتور
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                  {formatDate(summary?.dates?.invoice_created_at)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card elevation={0} sx={{ bgcolor: 'background.default', borderRadius: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <CalendarTodayIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                  <Typography variant="caption" color="text.secondary">
                    تاریخ تحویل به ناظر
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                  {formatDate(summary?.dates?.delivered_to_supervisor_at)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card elevation={0} sx={{ bgcolor: 'background.default', borderRadius: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <CalendarTodayIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                  <Typography variant="caption" color="text.secondary">
                    تاریخ تحویل به حسابداری
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                  {formatDate(summary?.dates?.delivered_to_accounting_at)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card elevation={0} sx={{ bgcolor: 'background.default', borderRadius: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <CalendarTodayIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                  <Typography variant="caption" color="text.secondary">
                    تاریخ ثبت سند حسابداری
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                  {formatDate(summary?.dates?.accounting_document_created_at)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* موضوع هزینه */}
        {summary?.cost_subject && (
          <Box sx={{ mt: 3, mb: 2 }}>
            <Card elevation={0} sx={{ bgcolor: 'background.default', borderRadius: 2 }}>
              <CardContent>
                <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                  موضوع هزینه فاکتور خرید
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                  {summary.cost_subject}
                </Typography>
              </CardContent>
            </Card>
          </Box>
        )}

        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Card elevation={0} sx={{ bgcolor: 'background.default', borderRadius: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <HashIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                  <Typography variant="caption" color="text.secondary">
                    شماره روکش
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                  {summary?.cover_number || '-'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Card elevation={0} sx={{ bgcolor: 'background.default', borderRadius: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <HashIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                  <Typography variant="caption" color="text.secondary">
                    شماره اتوماسیون
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                  {summary?.automation_number || '-'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Card elevation={0} sx={{ bgcolor: 'background.default', borderRadius: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <AttachMoneyIcon sx={{ color: '#FF9800', fontSize: 20 }} />
                  <Typography variant="caption" color="text.secondary">
                    مبلغ کل
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ fontWeight: 'bold', color: '#FF9800' }}>
                  {summary ? summary.gross_amount.toLocaleString('fa-IR') : '-'} ریال
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Card elevation={0} sx={{ bgcolor: 'background.default', borderRadius: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <CheckCircleIcon sx={{ color: '#4CAF50', fontSize: 20 }} />
                  <Typography variant="caption" color="text.secondary">
                    مبلغ بدون مالیات
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ fontWeight: 'bold', color: '#4CAF50' }}>
                  {summary ? summary.net_amount.toLocaleString('fa-IR') : '-'} ریال
                </Typography>
              </CardContent>
            </Card>
          </Grid>


          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Card elevation={0} sx={{ bgcolor: 'background.default', borderRadius: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  {summaryStatusVisuals.kind === 'approved' || summaryStatusVisuals.kind === 'registered' ? (
                    <CheckCircleIcon sx={{ color: '#4CAF50', fontSize: 20 }} />
                  ) : summaryStatusVisuals.kind === 'pending' ? (
                    <AccessTimeIcon sx={{ color: '#FF9800', fontSize: 20 }} />
                  ) : (
                    <HashIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                  )}
                  <Typography variant="caption" color="text.secondary">
                    وضعیت
                  </Typography>
                </Box>
                {summary?.invoice_status ? (
                  <StatusChip status={summary.invoice_status} />
                ) : (
                  <Typography variant="body1">-</Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* نمایش جزئیات: هر ردیف در یک باکس جداگانه */}
      {detailRows.length > 0 ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 4 }}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>
              جزئیات روکش
            </Typography>
            <Typography variant="body2" color="text.secondary">
              تعداد ردیف‌ها: {detailRows.length}
            </Typography>
          </Box>
          
          {detailRows.map((row, idx) => (
            <Paper
              key={`${row.invoice_no}-${row.reference}-${idx}`}
              sx={{
                p: { xs: 2, sm: 3 },
                borderRadius: 2,
                bgcolor: 'background.paper',
                border: '1px solid',
                borderColor: 'divider',
                transition: 'all 0.3s ease',
                '&:hover': {
                  boxShadow: 3,
                  transform: 'translateY(-2px)',
                },
              }}
              elevation={0}
            >
              {isMobile ? (
                // Mobile Card View
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '1rem' }}>
                      {row.invoice_no || '-'}
                    </Typography>
                    {row.status && <StatusChip status={row.status} />}
                  </Box>
                  <Divider sx={{ my: 2 }} />
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 6 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                        تاریخ
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {formatDate(row.invoice_date)}
                      </Typography>
                    </Grid>
                    <Grid size={{ xs: 6 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                        ناظر
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {row.unit_code || '-'}
                      </Typography>
                    </Grid>
                    <Grid size={{ xs: 12 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                        تامین کننده
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {row.supplier_name || '-'}
                      </Typography>
                    </Grid>
                    <Grid size={{ xs: 12 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                        عنوان قلم خریدنی
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {row.item_title || '-'}
                      </Typography>
                    </Grid>
                    <Grid size={{ xs: 6 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                        مبلغ ناخالص
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {typeof row.gross_amount === 'number'
                          ? `${row.gross_amount.toLocaleString('fa-IR')} ریال`
                          : row.gross_amount || '-'}
                      </Typography>
                    </Grid>
                    {row.description && (
                      <Grid size={{ xs: 12 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                          توضیحات
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 400 }}>
                          {row.description}
                        </Typography>
                      </Grid>
                    )}
                  </Grid>
                </Box>
              ) : (
                // Desktop Table View
                <TableContainer sx={{ overflowX: 'auto' }}>
                  <Table>
                    <TableHead>
                      <TableRow sx={{ bgcolor: 'background.default' }}>
                        <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                          شماره
                        </TableCell>
                        <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                          تاریخ
                        </TableCell>
                        <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                          ناظر
                        </TableCell>
                        <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                          تامین کننده
                        </TableCell>
                        <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                          عنوان قلم خریدنی
                        </TableCell>
                        <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                          مبلغ ناخالص
                        </TableCell>
                        <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                          توضیحات
                        </TableCell>
                        <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                          وضعیت
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow hover>
                        <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                            {row.invoice_no || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>{formatDate(row.invoice_date)}</TableCell>
                        <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>{row.unit_code || '-'}</TableCell>
                        <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>{row.supplier_name || '-'}</TableCell>
                        <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>{row.item_title || '-'}</TableCell>
                        <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                          {typeof row.gross_amount === 'number'
                            ? `${row.gross_amount.toLocaleString('fa-IR')} ریال`
                            : row.gross_amount || '-'}
                        </TableCell>
                        <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                          <Typography
                            variant="body2"
                            sx={{
                              maxWidth: 300,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                            title={row.description || ''}
                          >
                            {row.description || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                          {row.status ? <StatusChip status={row.status} /> : '-'}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Paper>
          ))}
        </Box>
      ) : (
        <Paper sx={{ mt: 4, p: 3, borderRadius: 2, bgcolor: 'background.paper' }} elevation={0}>
          <Typography variant="body1" color="text.secondary" align="center">
            ردیفی ثبت نشده است.
          </Typography>
        </Paper>
      )}
    </AppLayout>
  );
}

