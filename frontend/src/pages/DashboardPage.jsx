import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import Grid from '@mui/material/Grid';
import { useQuery } from '@tanstack/react-query';
import Button from '@mui/material/Button';
import { fetchInvoices } from '../api/invoices.js';
import { useAuth } from '../hooks/useAuth.js';
import { AppLayout } from '../components/AppLayout.jsx';
import { SummaryCard } from '../components/SummaryCard.jsx';
import { FiltersBar } from '../components/FiltersBar.jsx';
import { InvoicesTable } from '../components/InvoicesTable.jsx';

const DEFAULT_FILTERS = {
  status: '',
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
  const isAdmin = user?.username?.toLowerCase().startsWith('admin') || user?.username?.toLowerCase() === 'expert' || user?.role === 'expert';
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState(() => filtersFromSearchParams(searchParams));
  const [page, setPage] = useState(Number(searchParams.get('page') || 1));
  const [pageSize, setPageSize] = useState(Number(searchParams.get('page_size') || 20));

  const queryParams = useMemo(
    () => ({
      ...filters,
      page,
      page_size: pageSize,
      status: filters.status || undefined,
    }),
    [filters, page, pageSize],
  );

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['invoices', queryParams],
    queryFn: () => fetchInvoices(queryParams),
    keepPreviousData: true,
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
      title={isAdmin ? "داشبورد مدیریت فاکتورها" : "داشبورد فاکتورها"}
      actions={
        <Box>
          <CircularProgress size={24} sx={{ visibility: isLoading ? 'visible' : 'hidden' }} />
        </Box>
      }
    >
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 4 }}>
          <SummaryCard label="مبلغ تایید شده" value={totals.approved.toLocaleString('fa-IR')} color="success" />
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <SummaryCard label="مبلغ در انتظار" value={totals.pending.toLocaleString('fa-IR')} color="warning" />
        </Grid>
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

