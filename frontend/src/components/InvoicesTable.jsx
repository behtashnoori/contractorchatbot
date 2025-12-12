import PropTypes from 'prop-types';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TablePagination from '@mui/material/TablePagination';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import VisibilityIcon from '@mui/icons-material/Visibility';
import dayjs from 'dayjs';
import jalaliday from 'jalaliday';

dayjs.extend(jalaliday);

export function InvoicesTable({ data, pagination, onPageChange, onPageSizeChange, onView }) {
  const formatDate = (date) => (date ? dayjs(date).calendar('jalali').format('YYYY/MM/DD') : '-');

  return (
    <Paper elevation={0} sx={{ overflow: 'hidden', borderRadius: 2, bgcolor: 'white' }}>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow sx={{ bgcolor: '#f5f5f5' }}>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                شماره روکش
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                تاریخ ایجاد فاکتور
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                تحویل به ناظر
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                تحویل به حسابداری
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                وضعیت
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                مبلغ ناخالص
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                مبلغ خالص
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                جزئیات
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
                  <TableCell align="right">{row.cover_number}</TableCell>
                  <TableCell align="right">{formatDate(row.invoice_created_at)}</TableCell>
                  <TableCell align="right">{formatDate(row.delivered_to_supervisor_at)}</TableCell>
                  <TableCell align="right">{formatDate(row.delivered_to_accounting_at)}</TableCell>
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
                  <TableCell align="right">{row.gross_amount.toLocaleString('fa-IR')}</TableCell>
                  <TableCell align="right">{row.net_amount.toLocaleString('fa-IR')}</TableCell>
                  <TableCell align="right">
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => onView(row.cover_number)}
                      startIcon={<VisibilityIcon />}
                      sx={{
                        borderRadius: 2,
                        textTransform: 'none',
                        '&:hover': {
                          bgcolor: 'primary.light',
                          borderColor: 'primary.main',
                        },
                      }}
                    >
                      جزئیات
                    </Button>
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

