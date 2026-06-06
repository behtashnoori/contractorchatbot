import PropTypes from 'prop-types';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TablePagination from '@mui/material/TablePagination';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Grid from '@mui/material/Grid';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import VisibilityIcon from '@mui/icons-material/Visibility';
import dayjs from 'dayjs';
import jalaliday from 'jalaliday';
import { StatusChip } from './StatusChip.jsx';

dayjs.extend(jalaliday);

export function InvoicesTable({ data, pagination, onPageChange, onPageSizeChange, onView }) {
  const formatDate = (date) => (date ? dayjs(date).calendar('jalali').format('YYYY/MM/DD') : '-');
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Card View for Mobile
  if (isMobile && data.length > 0) {
    return (
      <Box>
        {data.map((row) => (
          <Card
            key={row.cover_number}
            elevation={0}
            sx={{
              mb: 2,
              borderRadius: 2,
              bgcolor: 'white',
              border: '1px solid #e0e0e0',
            }}
          >
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  {row.cover_number}
                </Typography>
                {row.status && <StatusChip status={row.status} />}
              </Box>
              <Divider sx={{ my: 2 }} />
              <Grid container spacing={2}>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                    تاریخ ایجاد فاکتور
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {formatDate(row.invoice_created_at)}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                    تحویل به ناظر
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {formatDate(row.delivered_to_supervisor_at)}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                    تحویل به حسابداری
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {formatDate(row.delivered_to_accounting_at)}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                    مبلغ ناخالص
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {row.gross_amount.toLocaleString('fa-IR')} ریال
                  </Typography>
                </Grid>
                <Grid size={{ xs: 6 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                    مبلغ خالص
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {row.net_amount.toLocaleString('fa-IR')} ریال
                  </Typography>
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <Button
                    variant="contained"
                    fullWidth
                    onClick={() => onView(row.cover_number)}
                    startIcon={<VisibilityIcon />}
                    sx={{
                      mt: 1,
                      borderRadius: 2,
                      textTransform: 'none',
                      fontWeight: 'bold',
                    }}
                  >
                    مشاهده جزئیات
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        ))}
        <TablePagination
          component="div"
          count={pagination.total}
          page={pagination.page - 1}
          rowsPerPage={pagination.page_size}
          onPageChange={(_, newPage) => onPageChange(newPage + 1)}
          onRowsPerPageChange={(event) => onPageSizeChange(parseInt(event.target.value, 10))}
          rowsPerPageOptions={[10, 20, 50]}
          labelRowsPerPage="تعداد در صفحه"
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} از ${count}`}
          sx={{
            direction: 'ltr',
            '& .MuiTablePagination-actions': { direction: 'ltr' },
            flexWrap: 'wrap',
          }}
        />
      </Box>
    );
  }

  // Table View for Desktop
  return (
    <Paper elevation={0} sx={{ overflow: 'hidden', borderRadius: 2, bgcolor: 'white' }}>
      <TableContainer sx={{ maxHeight: 'calc(100vh - 400px)', overflowX: 'auto' }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow sx={{ bgcolor: '#f5f5f5' }}>
              <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                شماره روکش
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: { xs: '0.75rem', sm: '0.875rem' }, display: { xs: 'none', md: 'table-cell' } }}>
                تاریخ ایجاد فاکتور
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: { xs: '0.75rem', sm: '0.875rem' }, display: { xs: 'none', lg: 'table-cell' } }}>
                تحویل به ناظر
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: { xs: '0.75rem', sm: '0.875rem' }, display: { xs: 'none', lg: 'table-cell' } }}>
                تحویل به حسابداری
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                مبلغ ناخالص
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: { xs: '0.75rem', sm: '0.875rem' }, display: { xs: 'none', sm: 'table-cell' } }}>
                مبلغ خالص
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                جزئیات
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                وضعیت
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  داده‌ای یافت نشد.
                </TableCell>
              </TableRow>
            ) : (
              data.map((row) => (
                <TableRow key={row.cover_number} hover>
                  <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>{row.cover_number}</TableCell>
                  <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' }, display: { xs: 'none', md: 'table-cell' } }}>{formatDate(row.invoice_created_at)}</TableCell>
                  <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' }, display: { xs: 'none', lg: 'table-cell' } }}>{formatDate(row.delivered_to_supervisor_at)}</TableCell>
                  <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' }, display: { xs: 'none', lg: 'table-cell' } }}>{formatDate(row.delivered_to_accounting_at)}</TableCell>
                  <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>{row.gross_amount.toLocaleString('fa-IR')}</TableCell>
                  <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' }, display: { xs: 'none', sm: 'table-cell' } }}>{row.net_amount.toLocaleString('fa-IR')}</TableCell>
                  <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => onView(row.cover_number)}
                      startIcon={<VisibilityIcon />}
                      sx={{
                        borderRadius: 2,
                        textTransform: 'none',
                        fontSize: { xs: '0.7rem', sm: '0.875rem' },
                        px: { xs: 1, sm: 2 },
                        '&:hover': {
                          bgcolor: 'primary.light',
                          borderColor: 'primary.main',
                        },
                      }}
                    >
                      جزئیات
                    </Button>
                  </TableCell>
                  <TableCell align="right" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                    {row.status ? <StatusChip status={row.status} /> : '-'}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        component="div"
        count={pagination.total}
        page={pagination.page - 1}
        rowsPerPage={pagination.page_size}
        onPageChange={(_, newPage) => onPageChange(newPage + 1)}
        onRowsPerPageChange={(event) => onPageSizeChange(parseInt(event.target.value, 10))}
        rowsPerPageOptions={[10, 20, 50]}
        labelRowsPerPage="تعداد در صفحه"
        labelDisplayedRows={({ from, to, count }) => `${from}-${to} از ${count}`}
        sx={{
          direction: 'ltr',
          '& .MuiTablePagination-actions': { direction: 'ltr' },
        }}
      />
    </Paper>
  );
}

InvoicesTable.propTypes = {
  data: PropTypes.arrayOf(
    PropTypes.shape({
      cover_number: PropTypes.string.isRequired,
      automation_number: PropTypes.string,
      invoice_date: PropTypes.string,
      invoice_created_at: PropTypes.string,
      delivered_to_supervisor_at: PropTypes.string,
      delivered_to_accounting_at: PropTypes.string,
      status: PropTypes.string,
      gross_amount: PropTypes.number,
      net_amount: PropTypes.number,
      detail_count: PropTypes.number,
    }),
  ).isRequired,
  pagination: PropTypes.shape({
    page: PropTypes.number.isRequired,
    page_size: PropTypes.number.isRequired,
    total: PropTypes.number.isRequired,
  }).isRequired,
  onPageChange: PropTypes.func.isRequired,
  onPageSizeChange: PropTypes.func.isRequired,
  onView: PropTypes.func.isRequired,
};


