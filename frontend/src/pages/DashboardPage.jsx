import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import { useQuery } from '@tanstack/react-query';
import Button from '@mui/material/Button';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CancelIcon from '@mui/icons-material/Cancel';
import PendingIcon from '@mui/icons-material/Pending';
import { fetchInvoices, fetchFilterOptions } from '../api/invoices.js';
import { useAuth } from '../hooks/useAuth.js';
import { hasStaffAccess } from '../utils/roles.js';
import { AppLayout } from '../components/AppLayout.jsx';
import { SummaryCard } from '../components/SummaryCard.jsx';
import { FiltersBar } from '../components/FiltersBar.jsx';
import { InvoicesTable } from '../components/InvoicesTable.jsx';

const DEFAULT_FILTERS = {
  status: '',
  fiscal_year: '',
  search: '',
  from_date: '',
  to_date: '',
};

const toSearchParams = (filters) => {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, value);
    }
  });
  return params;
};

const filtersFromSearchParams = (searchParams) => {
  const entries = Object.fromEntries(searchParams.entries());
  return { ...DEFAULT_FILTERS, ...entries };
};

export function DashboardPage() {
  const { contractor, user } = useAuth();
  const navigate = useNavigate();
  const staffDashboard = hasStaffAccess(user);
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState(() => filtersFromSearchParams(searchParams));
  const [page, setPage] = useState(Number(searchParams.get('page') || 1));
  const [pageSize, setPageSize] = useState(Number(searchParams.get('page_size') || 20));

  const queryParams = useMemo(
    () => {
      const params = {
        page,
        page_size: pageSize,
      };
      
      // فقط فیلترهای موجود را اضافه می‌کنیم (نه همه filters)
      if (filters.status) {
        params.status = filters.status;
      }
      
      if (filters.fiscal_year) {
        params.fiscal_year = String(filters.fiscal_year);
      }
      
      if (filters.search) {
        params.search = filters.search;
      }
      
      if (filters.cover_number) {
        params.cover_number = filters.cover_number;
      }
      
      console.log('[DashboardPage] Query params:', params);
      return params;
    },
    [filters, page, pageSize],
  );

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['invoices', queryParams],
    queryFn: () => fetchInvoices(queryParams),
    keepPreviousData: true,
  });

  // دریافت لیست سال‌های مالی و وضعیت‌ها (مرتبط با فیلترهای فعلی)
  const { data: filterOptions } = useQuery({
    queryKey: [
      'invoice-filter-options', 
      filters.fiscal_year || 'no-fiscal-year', 
      filters.status || 'no-status'
    ],
    queryFn: () => {
      const params = {};
      // فقط فیلترهای موجود را ارسال می‌کنیم
      if (filters.fiscal_year) {
        params.fiscal_year = filters.fiscal_year;
      }
      if (filters.status) {
        params.status = filters.status;
      }
      console.log('[DashboardPage] Fetching filter options with params:', params);
      return fetchFilterOptions(params);
    },
    enabled: true, // همیشه فعال
    staleTime: 0,  // همیشه fresh data بگیر
    cacheTime: 0,  // cache نکن
  });

  useEffect(() => {
    const params = toSearchParams({ ...filters, page, page_size: pageSize });
    setSearchParams(params, { replace: true });
  }, [filters, page, pageSize, setSearchParams]);

  const handleFiltersChange = (nextFilters) => {
    setFilters(nextFilters);
    setPage(1);
  };

  const handleReset = () => {
    setFilters(DEFAULT_FILTERS);
    setPage(1);
    setPageSize(20);
  };

  const handleView = (coverNumber) => {
    navigate(`/invoice/${coverNumber}`);
  };

  const totals = {
    pending: data?.totals?.pending_amount ?? 0,
    approved: data?.totals?.approved_amount ?? 0,
    totalInvoices: data?.totals?.total_invoices ?? 0,
  };

  return (
    <AppLayout
      title={staffDashboard ? "داشبورد مدیریت فاکتورها" : "داشبورد فاکتورها"}
      actions={
        <Box>
          <CircularProgress size={24} sx={{ visibility: isLoading ? 'visible' : 'hidden' }} />
        </Box>
      }
    >
      {/* باکس‌های فیلتر سال مالی */}
      {filterOptions?.fiscal_years?.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 2 }}>
            سال مالی:
          </Typography>
          <Grid container spacing={2}>
            {filterOptions.fiscal_years.map((year) => {
              const isSelected = filters.fiscal_year === String(year);
              return (
                <Grid key={year} size={{ xs: 12, sm: 6, md: 3 }}>
                  <Paper
                    elevation={0}
                    onClick={() => {
                      const newYear = isSelected ? '' : String(year);
                      const newFilters = { ...filters, fiscal_year: newYear };
                      // فقط اگر سال مالی deselect شد، status را پاک می‌کنیم
                      if (isSelected) {
                        newFilters.status = '';
                      }
                      console.log('[DashboardPage] Fiscal year clicked:', year, 'New filters:', newFilters);
                      handleFiltersChange(newFilters);
                    }}
                    sx={{
                      p: { xs: 2, sm: 2.5 },
                      display: 'flex',
                      flexDirection: 'row-reverse',
                      alignItems: 'center',
                      gap: { xs: 1.5, sm: 2 },
                      borderRadius: 2,
                      bgcolor: isSelected ? '#E3F2FD' : 'white',
                      border: `2px solid ${isSelected ? '#2196F3' : '#e0e0e0'}`,
                      cursor: 'pointer',
                      transition: 'all 0.3s ease',
                      boxShadow: isSelected ? 4 : 0,
                      transform: isSelected ? 'scale(1.02)' : 'scale(1)',
                      '&:hover': {
                        boxShadow: isSelected ? 6 : 2,
                        transform: isSelected ? 'scale(1.03)' : 'translateY(-2px) scale(1.01)',
                        borderColor: '#2196F3',
                      },
                    }}
                  >
                    <Box
                      sx={{
                        width: { xs: 40, sm: 48 },
                        height: { xs: 40, sm: 48 },
                        borderRadius: '50%',
                        bgcolor: isSelected ? '#E3F2FD' : '#f5f5f5',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                      }}
                    >
                      <CalendarTodayIcon sx={{ color: isSelected ? '#2196F3' : '#757575', fontSize: { xs: 20, sm: 24 } }} />
                    </Box>
                    <Box sx={{ flex: 1 }}>
                      <Typography 
                        variant="h6" 
                        sx={{ 
                          fontWeight: isSelected ? 800 : 'bold', 
                          color: isSelected ? '#2196F3' : 'text.primary',
                          fontSize: { xs: isSelected ? '1.1rem' : '1rem', sm: isSelected ? '1.25rem' : '1.125rem' },
                        }}
                      >
                        {year}
                      </Typography>
                      <Typography 
                        variant="caption" 
                        sx={{ 
                          color: isSelected ? '#1976D2' : 'text.secondary',
                          fontWeight: isSelected ? 600 : 400,
                          fontSize: { xs: '0.7rem', sm: '0.75rem' },
                        }}
                      >
                        سال مالی
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>
              );
            })}
          </Grid>
        </Box>
      )}

      {/* باکس‌های فیلتر وضعیت */}
      {filterOptions?.statuses?.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 2 }}>
            وضعیت:
          </Typography>
          <Grid container spacing={2}>
            {filterOptions.statuses.map((status) => {
              const isSelected = filters.status === status;
              const statusStat = filterOptions.status_stats?.[status] || { count: 0, percentage: 0 };
              
              // تعیین آیکون و رنگ بر اساس نوع وضعیت (Gamification)
              // رنگ‌ها باید حتی وقتی انتخاب نشده هم اعمال شوند
              let icon, iconBg, iconColor, borderColor;
              if (status === 'تاييد شده' || status === 'تایید شده' || status === 'approved') {
                // تایید شده: سبز پررنگ
                icon = <CheckCircleIcon sx={{ fontSize: 24 }} />;
                iconBg = isSelected ? '#C8E6C9' : '#E8F5E9';
                iconColor = '#2E7D32';  // همیشه سبز پررنگ
                borderColor = isSelected ? '#2E7D32' : '#2E7D3240';
              } else if (status === 'ثبت شده' || status === 'registered') {
                // ثبت شده: سبز کم رنگ
                icon = <CheckCircleIcon sx={{ fontSize: 24 }} />;
                iconBg = isSelected ? '#E8F5E9' : '#F1F8E9';
                iconColor = '#66BB6A';  // همیشه سبز کم رنگ
                borderColor = isSelected ? '#66BB6A' : '#66BB6A40';
              } else if (status === 'معلق' || status === 'pending' || status === 'در انتظار' || status === 'جاری') {
                // معلق: نارنجی
                icon = <AccessTimeIcon sx={{ fontSize: 24 }} />;
                iconBg = isSelected ? '#FFF3E0' : '#FFF8E1';
                iconColor = '#FF9800';  // همیشه نارنجی
                borderColor = isSelected ? '#FF9800' : '#FF980040';
              } else if (status === 'عودت شده' || status === 'rejected' || status === 'رد شده') {
                // عودت شده: قرمز
                icon = <CancelIcon sx={{ fontSize: 24 }} />;
                iconBg = isSelected ? '#FFEBEE' : '#FCE4EC';
                iconColor = '#F44336';  // همیشه قرمز
                borderColor = isSelected ? '#F44336' : '#F4433640';
              } else {
                icon = <PendingIcon sx={{ fontSize: 24 }} />;
                iconBg = isSelected ? '#E3F2FD' : '#f5f5f5';
                iconColor = '#2196F3';
                borderColor = isSelected ? '#2196F3' : '#2196F340';
              }

              return (
                <Grid key={status} size={{ xs: 12, sm: 6, md: 3 }}>
                  <Paper
                    elevation={0}
                    onClick={() => {
                      const newStatus = isSelected ? '' : status;
                      const newFilters = { ...filters, status: newStatus };
                      // فقط اگر وضعیت deselect شد، fiscal_year را پاک می‌کنیم
                      if (isSelected) {
                        newFilters.fiscal_year = '';
                      }
                      console.log('[DashboardPage] Status clicked:', status, 'New filters:', newFilters);
                      handleFiltersChange(newFilters);
                    }}
                    sx={{
                      p: { xs: 2, sm: 2.5 },
                      display: 'flex',
                      flexDirection: 'row-reverse',
                      alignItems: 'center',
                      gap: { xs: 1.5, sm: 2 },
                      borderRadius: 2,
                      bgcolor: isSelected ? iconBg : 'white',
                      border: `2px solid ${borderColor}`,
                      cursor: 'pointer',
                      transition: 'all 0.3s ease',
                      boxShadow: isSelected ? 4 : 0,
                      transform: isSelected ? 'scale(1.02)' : 'scale(1)',
                      '&:hover': {
                        boxShadow: isSelected ? 6 : 2,
                        transform: isSelected ? 'scale(1.03)' : 'translateY(-2px) scale(1.01)',
                        borderColor: borderColor,
                      },
                    }}
                  >
                    <Box
                      sx={{
                        width: { xs: 40, sm: 48 },
                        height: { xs: 40, sm: 48 },
                        borderRadius: '50%',
                        bgcolor: iconBg,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                      }}
                    >
                      <Box sx={{ color: iconColor, '& svg': { fontSize: { xs: 20, sm: 24 } } }}>{icon}</Box>
                    </Box>
                    <Box sx={{ flex: 1 }}>
                      <Typography 
                        variant="h6" 
                        sx={{ 
                          fontWeight: isSelected ? 800 : 'bold', 
                          color: iconColor,
                          fontSize: { xs: isSelected ? '1.1rem' : '1rem', sm: isSelected ? '1.25rem' : '1.125rem' },
                        }}
                      >
                        {status}
                      </Typography>
                      <Typography 
                        variant="caption" 
                        sx={{ 
                          color: isSelected ? iconColor : 'text.secondary',
                          fontWeight: isSelected ? 600 : 400,
                          fontSize: { xs: '0.7rem', sm: '0.75rem' },
                        }}
                      >
                        {statusStat.percentage}% ({statusStat.count} فاکتور)
                      </Typography>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          fontWeight: isSelected ? 700 : 'bold', 
                          color: iconColor, 
                          mt: 0.5,
                          fontSize: { xs: isSelected ? '0.85rem' : '0.8rem', sm: isSelected ? '0.95rem' : '0.875rem' },
                        }}
                      >
                        {statusStat.amount ? `${statusStat.amount.toLocaleString('fa-IR')} ریال` : '0 ریال'}
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>
              );
            })}
          </Grid>
        </Box>
      )}

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 4 }}>
          <SummaryCard label="تعداد کل فاکتورها" value={totals.totalInvoices.toLocaleString('fa-IR')} color="info" />
        </Grid>
      </Grid>

      <FiltersBar filters={filters} onChange={handleFiltersChange} onReset={handleReset} />

      {isError ? (
        <Alert severity="error" sx={{ direction: 'rtl' }} action={<Button onClick={() => refetch()}>تلاش مجدد</Button>}>
          {error?.response?.data?.error || 'خطا در دریافت اطلاعات'}
        </Alert>
      ) : null}

      {isLoading && !data ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Box sx={{ mt: 3 }}>
          <InvoicesTable
            data={data?.items ?? []}
            pagination={{
              page: data?.page ?? page,
              page_size: data?.page_size ?? pageSize,
              total: data?.total ?? 0,
            }}
            onPageChange={setPage}
            onPageSizeChange={setPageSize}
            onView={handleView}
          />
        </Box>
      )}
    </AppLayout>
  );
}

