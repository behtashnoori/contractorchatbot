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
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import Grid from '@mui/material/Grid';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
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

dayjs.extend(jalaliday);

const formatDate = (date) => (date ? dayjs(date).calendar('jalali').format('YYYY/MM/DD') : '-');

export function InvoiceDetailPage() {
  const { coverNumber } = useParams();
  const navigate = useNavigate();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['invoice-detail', coverNumber],
    queryFn: () => fetchInvoiceDetail(coverNumber),
  });

  const summary = data?.summary;
  const detailRows = data?.details ?? [];
  const supplierInvoiceNumbers = summary?.supplier_invoice_numbers || [];
  const supplierInvoiceCount = summary?.supplier_invoice_count || 0;
  
  console.log('[InvoiceDetailPage] Summary:', summary);
  console.log('[InvoiceDetailPage] Detail rows count:', detailRows.length);
  console.log('[InvoiceDetailPage] Detail rows:', detailRows);

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
      <Paper sx={{ p: 3, borderRadius: 2, bgcolor: 'white' }} elevation={0}>
        <Typography variant="h6" sx={{ mb: 3, fontWeight: 'bold' }}>
          اطلاعات روکش
        </Typography>

        {/* چهار تاریخ در بالا */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card elevation={0} sx={{ bgcolor: '#f5f5f5', borderRadius: 2 }}>
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
            <Card elevation={0} sx={{ bgcolor: '#f5f5f5', borderRadius: 2 }}>
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
            <Card elevation={0} sx={{ bgcolor: '#f5f5f5', borderRadius: 2 }}>
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
            <Card elevation={0} sx={{ bgcolor: '#f5f5f5', borderRadius: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <CalendarTodayIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                  <Typography variant="caption" color="text.secondary">
                    تاریخ ایجاد سند حسابداری
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                  {formatDate(summary?.dates?.accounting_document_created_at)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Card elevation={0} sx={{ bgcolor: '#f5f5f5', borderRadius: 2 }}>
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
            <Card elevation={0} sx={{ bgcolor: '#f5f5f5', borderRadius: 2 }}>
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
            <Card elevation={0} sx={{ bgcolor: '#f5f5f5', borderRadius: 2 }}>
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
            <Card elevation={0} sx={{ bgcolor: '#f5f5f5', borderRadius: 2 }}>
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
            <Card elevation={0} sx={{ bgcolor: '#f5f5f5', borderRadius: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  {summary?.invoice_status === 'تاييد شده' || summary?.invoice_status === 'تایید شده' ? (
                    <CheckCircleIcon sx={{ color: '#4CAF50', fontSize: 20 }} />
                  ) : summary?.invoice_status === 'در انتظار' ? (
                    <AccessTimeIcon sx={{ color: '#FF9800', fontSize: 20 }} />
                  ) : (
                    <HashIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                  )}
                  <Typography variant="caption" color="text.secondary">
                    وضعیت
                  </Typography>
                </Box>
                {summary?.invoice_status ? (
                  <Chip
                    label={summary.invoice_status}
                    size="small"
                    color={
                      summary.invoice_status === 'تاييد شده' || summary.invoice_status === 'تایید شده'
                        ? 'success'
                        : summary.invoice_status === 'در انتظار'
                          ? 'warning'
                          : 'error'
                    }
                    sx={{ fontWeight: 'bold' }}
                  />
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
                p: 3, 
                borderRadius: 2, 
                bgcolor: 'white',
                border: '1px solid #e0e0e0',
                '&:hover': {
                  boxShadow: 2,
                },
              }} 
              elevation={0}
            >
              <Table>
                <TableHead>
                  <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                      شماره
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                      تاریخ
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                      واحد / رمز تامین
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                      تامین کننده
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                      وضعیت
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                      عنوان قلم خریدنی
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                      مبلغ ناخالص
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                      مبنا
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                      توضیحات
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow hover>
                    <TableCell align="right">
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        {row.invoice_no || summary?.cover_number || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">{formatDate(row.invoice_date)}</TableCell>
                    <TableCell align="right">{row.unit_code || '-'}</TableCell>
                    <TableCell align="right">{row.supplier_name || '-'}</TableCell>
                    <TableCell align="right">
                      {row.status ? (
                        <Chip
                          label={row.status}
                          size="small"
                          color={
                            row.status === 'تاييد شده' || row.status === 'تایید شده'
                              ? 'success'
                              : row.status === 'در انتظار'
                                ? 'warning'
                                : 'error'
                          }
                          sx={{ fontWeight: 'bold' }}
                        />
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell align="right">{row.item_title || '-'}</TableCell>
                    <TableCell align="right">
                      {typeof row.gross_amount === 'number'
                        ? `${row.gross_amount.toLocaleString('fa-IR')} ریال`
                        : row.gross_amount || '-'}
                    </TableCell>
                    <TableCell align="right">{row.reference || '-'}</TableCell>
                    <TableCell align="right">
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
                  </TableRow>
                </TableBody>
              </Table>
            </Paper>
          ))}
        </Box>
      ) : (
        <Paper sx={{ mt: 4, p: 3, borderRadius: 2, bgcolor: 'white' }} elevation={0}>
          <Typography variant="body1" color="text.secondary" align="center">
            ردیفی ثبت نشده است.
          </Typography>
        </Paper>
      )}
    </AppLayout>
  );
}

