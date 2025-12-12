import { useMemo, useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { Navigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Table from '@mui/material/Table';
import TableHead from '@mui/material/TableHead';
import TableBody from '@mui/material/TableBody';
import TableRow from '@mui/material/TableRow';
import TableCell from '@mui/material/TableCell';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import TablePagination from '@mui/material/TablePagination';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DownloadIcon from '@mui/icons-material/Download';
import SearchIcon from '@mui/icons-material/Search';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ErrorIcon from '@mui/icons-material/Error';
import ChecklistIcon from '@mui/icons-material/Checklist';
import LinearProgress from '@mui/material/LinearProgress';
import CircularProgress from '@mui/material/CircularProgress';

import { AppLayout } from '../components/AppLayout.jsx';
import { useAuth } from '../hooks/useAuth.js';
import {
  uploadCodTafsiltamin,
  uploadContractorsOne,
  uploadContractorsTwo,
  downloadCodTafsiltaminTemplate,
  downloadContractorsOneTemplate,
  downloadContractorsTwoTemplate,
  getBatchErrors,
  getContractors,
  getUploadProgress,
  getInvoiceSummaries,
  getInvoiceDetails,
} from '../api/admin.js';

const COD_REQUIRED_COLUMNS = ['کد تامین کننده', 'نام تامین کننده', 'وضعیت', 'نوع', 'کد تفصیلی'];

const COD_SAMPLE_ROWS = [
  {
    supplier_code: '732',
    supplier_name: 'سیاوش ایوبی (تعمیر)',
    status: 'فعال',
    type: 'داخلی',
    detail_code: '0026968',
  },
  {
    supplier_code: '731',
    supplier_name: 'احمد رحیمیان | نماکار',
    status: 'فعال',
    type: 'داخلی',
    detail_code: '0026956',
  },
  {
    supplier_code: '730',
    supplier_name: 'پزمان رودخانه ئی شلمه',
    status: 'فعال',
    type: 'داخلی',
    detail_code: '0026966',
  },
  {
    supplier_code: '729',
    supplier_name: 'شرکت آذین توسعه مهرآ',
    status: 'فعال',
    type: 'داخلی',
    detail_code: '0071639',
  },
  {
    supplier_code: '728',
    supplier_name: 'شاهسواری عزیزی تخت',
    status: 'فعال',
    type: 'داخلی',
    detail_code: '0026921',
  },
];

const CONTRACTORS_COLUMNS = [
  'شماره اتوماسیون',
  'تاريخ ایجاد سند حسابداری فاکتور',
  'در اختیار ناظر',
  'تاریخ تحویل به حسابداری',
  'تاریخ تحویل به ناظر',
  'تاريخ ایجاد فاکتور',
  'شماره روکش',
  'بهره بردار',
  'موضوع هزینه فاکتور خرید',
  'مبلغ کل',
  'مبلغ بدون مالیات',
  'محدوده زمانی انجام کار',
  'وضعیت فاکتور',
  'توضیحات فاکتور خرید',
  'شماره صورت حساب پیمانکار فاکتور خرید',
  'شماره مجوز فاکتور خرید',
  'نوع مجوز فاکتور خرید',
  'نام تامین کننده',
  'شماره قرارداد کارفرما فاکتور خرید',
  'نام کارفرما',
];

const CONTRACTORS_SAMPLE_ROWS = [
  {
    automation_number: '',
    invoice_date: '1401/09/12',
    supervisor_available: '',
    delivered_accounting: '',
    delivered_supervisor: '',
    invoice_created_at: '',
    cover_number: '14010010',
    business_owner: 'حوزه مدیرعامل',
    cost_subject: '',
    gross_amount: '1084877000',
    net_amount: '995300000',
    time_span: '',
    status: 'تایید شده',
    notes: '',
    contractor_invoice_no: '',
    permit_number: '',
    permit_type: '',
    supplier_name: 'پیشرو فناوران فرتاک',
    client_contract_number: '',
    client_name: '',
  },
  {
    automation_number: '',
    invoice_date: '1401/08/29',
    supervisor_available: '',
    delivered_accounting: '',
    delivered_supervisor: '',
    invoice_created_at: '',
    cover_number: '14010011',
    business_owner: 'حوزه مدیرعامل',
    cost_subject: '',
    gross_amount: '16490479200',
    net_amount: '15128880000',
    time_span: '',
    status: 'تایید شده',
    notes: '',
    contractor_invoice_no: '',
    permit_number: '',
    permit_type: '',
    supplier_name: 'واگن سازان تبریز',
    client_contract_number: '',
    client_name: '',
  },
];

const CONTRACTORS2_COLUMNS = ['توضیحات', 'مبنا', 'مبلغ ناخالص', 'وضعیت', 'عنوان قلم خرید', 'تامین کننده', 'احد/رمز', 'تاریخ', 'شماره'];

const CONTRACTORS2_SAMPLE_ROWS = [
  {
    description: '14040331',
    reference: '14046576',
    gross_amount: '2/22E+08',
    status: 'ثبت شده',
    item_title: 'لجستیک ریل ثبت شده',
    supplier: 'محمدجواد ده ریب (محصول)',
    unit: 'محصول',
    date: '1404/03/03',
    invoice_no: '14040450',
  },
  {
    description: '0452',
    reference: '14046575',
    gross_amount: '1E+08',
    status: 'ثبت شده',
    item_title: 'ساخت سیوله ثبت شده',
    supplier: 'سیدجلال مرادیه و ناسیاسی',
    unit: 'س',
    date: '1404/04/02',
    invoice_no: '14040453',
  },
  {
    description: '10060781',
    reference: '14046573',
    gross_amount: '3/9E+09',
    status: 'معلق',
    item_title: 'اجاره ماشین',
    supplier: 'حمل و نقل رنت و تاکون',
    unit: 'حمل و نقل رنت و تاکون',
    date: '1404/04/02',
    invoice_no: '14040452',
  },
];

function TabPanel({ children, value, index }) {
  return (
    <div role="tabpanel" hidden={value !== index} id={`upload-tabpanel-${index}`} aria-labelledby={`upload-tab-${index}`}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

TabPanel.propTypes = {
  children: PropTypes.node,
  value: PropTypes.number.isRequired,
  index: PropTypes.number.isRequired,
};

export function AdminUploadPage() {
  const { user } = useAuth();
  const isAdmin = user?.username?.toLowerCase().startsWith('admin') || user?.username?.toLowerCase() === 'expert';

  const [activeTab, setActiveTab] = useState(0);
  const [codFile, setCodFile] = useState(null);
  const [codResult, setCodResult] = useState(null);
  const [codErrors, setCodErrors] = useState(null);
  const [contractorsFile, setContractorsFile] = useState(null);
  const [contractorsResult, setContractorsResult] = useState(null);
  const [contractorsErrors, setContractorsErrors] = useState(null);
  const [contractorsProgress, setContractorsProgress] = useState(null);
  const [contractorsProgressInterval, setContractorsProgressInterval] = useState(null);
  const contractorsProgressIntervalRef = useRef(null);
  
  const [contractorsTwoFile, setContractorsTwoFile] = useState(null);
  const [contractorsTwoResult, setContractorsTwoResult] = useState(null);
  const [contractorsTwoErrors, setContractorsTwoErrors] = useState(null);
  const [contractorsTwoProgress, setContractorsTwoProgress] = useState(null);
  const contractorsTwoProgressIntervalRef = useRef(null);
  
  // Pagination and search for contractors list
  const [contractorsPage, setContractorsPage] = useState(0);
  const [contractorsPerPage, setContractorsPerPage] = useState(20);
  const [contractorsSearch, setContractorsSearch] = useState('');
  
  // Pagination and search for invoice summaries list
  const [summariesPage, setSummariesPage] = useState(0);
  const [summariesPerPage, setSummariesPerPage] = useState(20);
  const [summariesSearch, setSummariesSearch] = useState('');
  
  // Pagination and search for invoice details list
  const [detailsPage, setDetailsPage] = useState(0);
  const [detailsPerPage, setDetailsPerPage] = useState(20);
  const [detailsSearch, setDetailsSearch] = useState('');

  const codMutation = useMutation({
    mutationFn: uploadCodTafsiltamin,
    onSuccess: async (data) => {
      setCodResult(data);
      setCodErrors(null);
      if (data.metrics?.errors > 0 && data.batch_id) {
        try {
          const errorData = await getBatchErrors(data.batch_id);
          setCodErrors(errorData.errors || []);
        } catch (err) {
          console.error('Failed to fetch errors:', err);
        }
      }
    },
  });

  const contractorsMutation = useMutation({
    mutationFn: uploadContractorsOne,
    onSuccess: async (data) => {
      console.log('[contractorsMutation] onSuccess called', data);
      // If status is "queued", start polling for progress
      if (data.status === 'queued' && data.batch_id) {
        console.log('[contractorsMutation] Starting polling for batch_id:', data.batch_id);
        setContractorsProgress({
          status: 'queued',
          percentage: 0,
          processed: 0,
          total: 0,
        });
        
        // Start polling with exponential backoff
        let consecutiveErrors = 0;
        let pollDelay = 2000; // Start with 2 seconds
        const maxConsecutiveErrors = 5; // Increased to allow more retries
        const maxPollDelay = 10000; // Maximum 10 seconds between polls
        const basePollDelay = 2000; // Base delay of 2 seconds
        let timeoutId = null;
        let isPolling = true;
        
        const pollProgress = async () => {
          if (!isPolling) {
            console.log('[pollProgress] Polling stopped, exiting');
            return;
          }
          
          console.log('[pollProgress] Polling progress for batch_id:', data.batch_id);
          try {
            const progressData = await getUploadProgress(data.batch_id);
            console.log('[pollProgress] Progress data received:', progressData);
            console.log('[pollProgress] Status:', progressData.status);
            console.log('[pollProgress] Progress:', progressData.progress);
            console.log('[pollProgress] Metrics:', progressData.metrics);
            consecutiveErrors = 0; // Reset error counter on success
            pollDelay = basePollDelay; // Reset to base delay on success
            
            setContractorsProgress({
              ...progressData.progress,
              status: progressData.status,
              metrics: progressData.metrics,
            });
            
            // If completed, stop polling and fetch final results
            if (progressData.status === 'completed' || progressData.status === 'completed_with_errors' || progressData.status === 'failed') {
              console.log('[pollProgress] Processing completed! Status:', progressData.status);
              isPolling = false;
              if (timeoutId) {
                clearTimeout(timeoutId);
                timeoutId = null;
              }
              contractorsProgressIntervalRef.current = null;
              
              setContractorsResult({
                batch_id: data.batch_id,
                status: progressData.status,
                metrics: progressData.metrics || {
                  inserted: 0,
                  updated: 0,
                  errors: progressData.metrics?.errors || 0,
                },
              });
              
              // Keep progress for metrics display, but mark as completed
              setContractorsProgress(prev => ({
                ...prev,
                status: progressData.status,
                metrics: progressData.metrics,
              }));
              
              // Fetch errors if any
              if (progressData.metrics?.errors > 0) {
                try {
                  const errorData = await getBatchErrors(data.batch_id);
                  setContractorsErrors(errorData.errors || []);
                } catch (err) {
                  console.error('Failed to fetch errors:', err);
                }
              }
              return;
            }
            
            // Log if still processing
            if (progressData.status === 'processing') {
              console.log('[pollProgress] Still processing...', {
                processed: progressData.progress?.processed,
                total: progressData.progress?.total,
                percentage: progressData.progress?.percentage,
              });
            }
          } catch (err) {
            console.error('[pollProgress] Error fetching progress:', err);
            console.error('[pollProgress] Error response:', err?.response?.data);
            console.error('[pollProgress] Error status:', err?.response?.status);
            consecutiveErrors++;
            const isUnauthorized = err?.response?.status === 401;
            
            if (isUnauthorized) {
              // Check if this is a refresh failure (request was retried but still failed)
              // If _retry is true, it means interceptor tried to refresh but request still failed
              const isRefreshFailed = err?.config?._retry === true;
              
              if (isRefreshFailed) {
                console.error('[Progress Polling] Token refresh attempted but request still failed with 401');
                console.error('[Progress Polling] This may indicate the new token is invalid or backend issue');
                // This means interceptor tried to refresh but request still failed
                // Wait a bit longer before retrying to allow backend to sync
                pollDelay = Math.min(pollDelay * 2, maxPollDelay);
                
                if (consecutiveErrors >= maxConsecutiveErrors) {
                  console.error('[Progress Polling] Too many authentication failures after refresh, stopping polling');
                  isPolling = false;
                  if (timeoutId) {
                    clearTimeout(timeoutId);
                    timeoutId = null;
                  }
                  contractorsProgressIntervalRef.current = null;
                  
                  // Show user-friendly error message
                  setContractorsProgress(prev => ({
                    ...prev,
                    status: 'failed',
                    error: 'خطای احراز هویت. لطفاً دوباره وارد شوید.',
                  }));
                  return;
                }
              } else {
                // Interceptor is handling the refresh, just wait
                console.log('[Progress Polling] 401 detected, waiting for token refresh...');
                // Don't count this as an error yet - interceptor will handle it
                consecutiveErrors = Math.max(0, consecutiveErrors - 1); // Reduce error count
                // Apply exponential backoff
                pollDelay = Math.min(pollDelay * 1.5, maxPollDelay);
              }
            } else {
              console.error('[Progress Polling] Failed to fetch progress:', err);
              // Apply exponential backoff for other errors
              pollDelay = Math.min(pollDelay * 1.5, maxPollDelay);
              
              // For non-401 errors, stop after max errors
              if (consecutiveErrors >= maxConsecutiveErrors) {
                console.error('[Progress Polling] Too many consecutive errors, stopping polling');
                isPolling = false;
                if (timeoutId) {
                  clearTimeout(timeoutId);
                  timeoutId = null;
                }
                contractorsProgressIntervalRef.current = null;
                
                setContractorsProgress(prev => ({
                  ...prev,
                  status: 'failed',
                  error: 'خطا در دریافت وضعیت پردازش. لطفاً صفحه را رفرش کنید.',
                }));
                return;
              }
            }
          }
          
          // Schedule next poll with current delay
          if (isPolling) {
            timeoutId = setTimeout(pollProgress, pollDelay);
            contractorsProgressIntervalRef.current = timeoutId;
          }
        };
        
        // Initial poll
        pollProgress();
      } else {
        // Immediate result (old behavior)
        setContractorsResult(data);
        setContractorsErrors(null);
        if (data.metrics?.errors > 0 && data.batch_id) {
          try {
            const errorData = await getBatchErrors(data.batch_id);
            setContractorsErrors(errorData.errors || []);
          } catch (err) {
            console.error('Failed to fetch errors:', err);
          }
        }
      }
    },
    onError: (error) => {
      console.error('[contractorsMutation] onError called');
      console.error('Upload error:', error);
      console.error('Error response:', error?.response?.data);
      console.error('Error status:', error?.response?.status);
      console.error('Error message:', error?.message);
      setContractorsResult(null);
      setContractorsErrors(null);
      setContractorsProgress(null);
      if (contractorsProgressIntervalRef.current) {
        clearTimeout(contractorsProgressIntervalRef.current);
        contractorsProgressIntervalRef.current = null;
      }
    },
  });
  
  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (contractorsProgressIntervalRef.current) {
        clearTimeout(contractorsProgressIntervalRef.current);
      }
      if (contractorsTwoProgressIntervalRef.current) {
        clearTimeout(contractorsTwoProgressIntervalRef.current);
      }
    };
  }, []);

  const contractorsTwoMutation = useMutation({
    mutationFn: uploadContractorsTwo,
    onSuccess: async (data) => {
      // If status is "queued", start polling for progress
      if (data.status === 'queued' && data.batch_id) {
        setContractorsTwoProgress({
          status: 'queued',
          percentage: 0,
          processed: 0,
          total: 0,
        });
        
        // Start polling with exponential backoff
        let consecutiveErrors = 0;
        let pollDelay = 2000; // Start with 2 seconds
        const maxConsecutiveErrors = 5; // Increased to allow more retries
        const maxPollDelay = 10000; // Maximum 10 seconds between polls
        const basePollDelay = 2000; // Base delay of 2 seconds
        let timeoutId = null;
        let isPolling = true;
        
        const pollProgress = async () => {
          if (!isPolling) return;
          
          try {
            const progressData = await getUploadProgress(data.batch_id);
            consecutiveErrors = 0; // Reset error counter on success
            pollDelay = basePollDelay; // Reset to base delay on success
            
            setContractorsTwoProgress({
              ...progressData.progress,
              status: progressData.status,
              metrics: progressData.metrics,
            });
            
            // If completed, stop polling and fetch final results
            if (progressData.status === 'completed' || progressData.status === 'completed_with_errors' || progressData.status === 'failed') {
              isPolling = false;
              if (timeoutId) {
                clearTimeout(timeoutId);
                timeoutId = null;
              }
              contractorsTwoProgressIntervalRef.current = null;
              
              setContractorsTwoResult({
                batch_id: data.batch_id,
                status: progressData.status,
                metrics: progressData.metrics || {
                  inserted: 0,
                  updated: 0,
                  errors: progressData.metrics?.errors || 0,
                },
              });
              
              // Keep progress for metrics display, but mark as completed
              setContractorsTwoProgress(prev => ({
                ...prev,
                status: progressData.status,
                metrics: progressData.metrics,
              }));
              
              // Fetch errors if any
              if (progressData.metrics?.errors > 0) {
                try {
                  const errorData = await getBatchErrors(data.batch_id);
                  setContractorsTwoErrors(errorData.errors || []);
                } catch (err) {
                  console.error('Failed to fetch errors:', err);
                }
              }
              return;
            }
          } catch (err) {
            console.error('[pollProgress] Error fetching progress:', err);
            console.error('[pollProgress] Error response:', err?.response?.data);
            console.error('[pollProgress] Error status:', err?.response?.status);
            consecutiveErrors++;
            const isUnauthorized = err?.response?.status === 401;
            
            if (isUnauthorized) {
              // Check if this is a refresh failure (request was retried but still failed)
              // If _retry is true, it means interceptor tried to refresh but request still failed
              const isRefreshFailed = err?.config?._retry === true;
              
              if (isRefreshFailed) {
                console.error('[Progress Polling] Token refresh attempted but request still failed with 401');
                console.error('[Progress Polling] This may indicate the new token is invalid or backend issue');
                // This means interceptor tried to refresh but request still failed
                // Wait a bit longer before retrying to allow backend to sync
                pollDelay = Math.min(pollDelay * 2, maxPollDelay);
                
                if (consecutiveErrors >= maxConsecutiveErrors) {
                  console.error('[Progress Polling] Too many authentication failures after refresh, stopping polling');
                  isPolling = false;
                  if (timeoutId) {
                    clearTimeout(timeoutId);
                    timeoutId = null;
                  }
                  contractorsTwoProgressIntervalRef.current = null;
                  
                  // Show user-friendly error message
                  setContractorsTwoProgress(prev => ({
                    ...prev,
                    status: 'failed',
                    error: 'خطای احراز هویت. لطفاً دوباره وارد شوید.',
                  }));
                  return;
                }
              } else {
                // Interceptor is handling the refresh, just wait
                console.log('[Progress Polling] 401 detected, waiting for token refresh...');
                // Don't count this as an error yet - interceptor will handle it
                consecutiveErrors = Math.max(0, consecutiveErrors - 1); // Reduce error count
                // Apply exponential backoff
                pollDelay = Math.min(pollDelay * 1.5, maxPollDelay);
              }
            } else {
              console.error('[Progress Polling] Failed to fetch progress:', err);
              // Apply exponential backoff for other errors
              pollDelay = Math.min(pollDelay * 1.5, maxPollDelay);
              
              // For non-401 errors, stop after max errors
              if (consecutiveErrors >= maxConsecutiveErrors) {
                console.error('[Progress Polling] Too many consecutive errors, stopping polling');
                isPolling = false;
                if (timeoutId) {
                  clearTimeout(timeoutId);
                  timeoutId = null;
                }
                contractorsTwoProgressIntervalRef.current = null;
                
                setContractorsTwoProgress(prev => ({
                  ...prev,
                  status: 'failed',
                  error: 'خطا در دریافت وضعیت پردازش. لطفاً صفحه را رفرش کنید.',
                }));
                return;
              }
            }
          }
          
          // Schedule next poll with current delay
          if (isPolling) {
            timeoutId = setTimeout(pollProgress, pollDelay);
            contractorsTwoProgressIntervalRef.current = timeoutId;
          }
        };
        
        // Initial poll
        pollProgress();
      } else {
        // Immediate result (old behavior)
        setContractorsTwoResult(data);
        setContractorsTwoErrors(null);
        if (data.metrics?.errors > 0 && data.batch_id) {
          try {
            const errorData = await getBatchErrors(data.batch_id);
            setContractorsTwoErrors(errorData.errors || []);
          } catch (err) {
            console.error('Failed to fetch errors:', err);
          }
        }
      }
    },
    onError: (error) => {
      console.error('Upload error:', error);
      console.error('Error response:', error?.response?.data);
      setContractorsTwoResult(null);
      setContractorsTwoErrors(null);
      setContractorsTwoProgress(null);
      if (contractorsTwoProgressIntervalRef.current) {
        clearTimeout(contractorsTwoProgressIntervalRef.current);
        contractorsTwoProgressIntervalRef.current = null;
      }
    },
  });

  const codDisabled = useMemo(() => !codFile || codMutation.isPending, [codFile, codMutation.isPending]);
  const contractorsDisabled = useMemo(
    () => !contractorsFile || contractorsMutation.isPending,
    [contractorsFile, contractorsMutation.isPending],
  );
  const contractorsTwoDisabled = useMemo(
    () => !contractorsTwoFile || contractorsTwoMutation.isPending,
    [contractorsTwoFile, contractorsTwoMutation.isPending],
  );

  // Query for contractors list
  const contractorsQuery = useQuery({
    queryKey: ['contractors', contractorsPage, contractorsPerPage, contractorsSearch],
    queryFn: () =>
      getContractors({
        page: contractorsPage + 1,
        per_page: contractorsPerPage,
        search: contractorsSearch,
      }),
    enabled: activeTab === 0, // Only fetch when codtafsiltamin tab is active
  });
  
  // Query for invoice summaries list
  const summariesQuery = useQuery({
    queryKey: ['invoice-summaries', summariesPage, summariesPerPage, summariesSearch],
    queryFn: () =>
      getInvoiceSummaries({
        page: summariesPage + 1,
        per_page: summariesPerPage,
        search: summariesSearch,
      }),
    enabled: activeTab === 1, // Only fetch when contractors-1 tab is active
  });
  
  // Query for invoice details list
  const detailsQuery = useQuery({
    queryKey: ['invoice-details', detailsPage, detailsPerPage, detailsSearch],
    queryFn: () =>
      getInvoiceDetails({
        page: detailsPage + 1,
        per_page: detailsPerPage,
        search: detailsSearch,
      }),
    enabled: activeTab === 2, // Only fetch when contractors-2 tab is active
  });

  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleCodChange = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      setCodFile(file);
      setCodResult(null);
      setCodErrors(null);
    }
  };

  const handleContractorsChange = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      setContractorsFile(file);
      setContractorsResult(null);
      setContractorsErrors(null);
    }
  };

  const handleContractorsTwoChange = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      setContractorsTwoFile(file);
      setContractorsTwoResult(null);
      setContractorsTwoErrors(null);
      setContractorsTwoProgress(null);
      if (contractorsTwoProgressIntervalRef.current) {
        clearTimeout(contractorsTwoProgressIntervalRef.current);
        contractorsTwoProgressIntervalRef.current = null;
      }
    }
  };

  const submitCod = (event) => {
    event.preventDefault();
    if (!codFile) return;
    codMutation.mutate(codFile);
  };

  const submitContractors = (event) => {
    event.preventDefault();
    console.log('[submitContractors] Called', { contractorsFile, hasFile: !!contractorsFile });
    if (!contractorsFile) {
      console.warn('[submitContractors] No file selected');
      return;
    }
    console.log('[submitContractors] Starting mutation...');
    contractorsMutation.mutate(contractorsFile);
  };

  const submitContractorsTwo = (event) => {
    event.preventDefault();
    if (!contractorsTwoFile) return;
    contractorsTwoMutation.mutate(contractorsTwoFile);
  };

  return (
    <AppLayout title="بارگذاری فایل‌های مرجع" actions={null}>
      <Paper sx={{ p: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tab label="codtafsiltamin (پیمانکاران)" />
          <Tab label="contractors-1 (خلاصه فاکتورها)" />
          <Tab label="contractors-2 (جزئیات فاکتورها)" />
        </Tabs>

        <TabPanel value={activeTab} index={0}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                فایل codtafsiltamin
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                این فایل فهرست پیمانکاران است. فایل باید پسوند .xlsx داشته باشد و ستون‌های زیر را شامل شود.
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                {COD_REQUIRED_COLUMNS.map((column) => (
                  <Box
                    key={column}
                    sx={{ borderRadius: 1, bgcolor: 'grey.100', px: 1.5, py: 0.5, fontSize: 13, color: 'text.secondary' }}
                  >
                    {column}
                  </Box>
                ))}
              </Box>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={downloadCodTafsiltaminTemplate}
                sx={{ mb: 2 }}
              >
                دانلود قالب Excel
              </Button>
            </Box>
            <Box component="form" onSubmit={submitCod} sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
              <Button variant="outlined" component="label" startIcon={<UploadFileIcon />}>
                انتخاب فایل
                <input type="file" hidden accept=".xlsx" onChange={handleCodChange} />
              </Button>
              <Typography variant="body2" sx={{ minWidth: 200 }}>
                {codFile ? codFile.name : 'هیچ فایلی انتخاب نشده است'}
              </Typography>
              <Button type="submit" variant="contained" disabled={codDisabled}>
                {codMutation.isPending ? 'در حال ارسال...' : 'آپلود فایل'}
              </Button>
            </Box>
            {codMutation.isError ? (
              <Alert severity="error">
                {codMutation.error?.response?.data?.message || 'خطایی رخ داد. لطفاً دوباره تلاش کنید.'}
              </Alert>
            ) : null}
            {codResult ? (
              <Alert severity={codResult?.metrics?.errors ? 'warning' : 'success'}>
                <strong>نتیجه:</strong> {codResult.metrics.inserted} جدید، {codResult.metrics.updated} به‌روزرسانی،{' '}
                {codResult.metrics.errors} خطا
                {codResult.metrics.total_in_database !== undefined && (
                  <><br /><strong>تعداد کل در دیتابیس:</strong> {codResult.metrics.total_in_database} ردیف</>
                )}
              </Alert>
            ) : null}
            {codErrors && codErrors.length > 0 ? (
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ bgcolor: 'error.light', color: 'error.contrastText' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ErrorIcon />
                    <Typography variant="subtitle1">نمایش {codErrors.length} خطا</Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Table size="small" sx={{ direction: 'rtl' }}>
                    <TableHead>
                      <TableRow>
                        <TableCell align="right">ردیف</TableCell>
                        <TableCell align="right">پیام خطا</TableCell>
                        <TableCell align="right">داده‌های مشکل‌دار</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {codErrors.map((error, idx) => (
                        <TableRow key={idx}>
                          <TableCell align="right">{error.row_index}</TableCell>
                          <TableCell align="right" sx={{ color: 'error.main' }}>{error.message}</TableCell>
                          <TableCell align="right">
                            <Typography variant="caption" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                              {error.payload ? JSON.stringify(error.payload, null, 2) : '-'}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </AccordionDetails>
              </Accordion>
            ) : null}
            {contractorsQuery.data && (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">داده‌های import شده ({contractorsQuery.data.total} ردیف)</Typography>
                  <TextField
                    size="small"
                    placeholder="جستجو..."
                    value={contractorsSearch}
                    onChange={(e) => {
                      setContractorsSearch(e.target.value);
                      setContractorsPage(0);
                    }}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <SearchIcon />
                        </InputAdornment>
                      ),
                    }}
                    sx={{ minWidth: 250 }}
                  />
                </Box>
                <Table size="small" sx={{ direction: 'rtl' }}>
                  <TableHead>
                    <TableRow>
                      <TableCell align="right">کد تفصیلی</TableCell>
                      <TableCell align="right">کد تامین کننده</TableCell>
                      <TableCell align="right">نام تامین کننده</TableCell>
                      <TableCell align="right">وضعیت</TableCell>
                      <TableCell align="right">نوع</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {contractorsQuery.isLoading ? (
                      <TableRow>
                        <TableCell colSpan={5} align="center">
                          در حال بارگذاری...
                        </TableCell>
                      </TableRow>
                    ) : contractorsQuery.data.items.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} align="center">
                          داده‌ای یافت نشد
                        </TableCell>
                      </TableRow>
                    ) : (
                      contractorsQuery.data.items.map((contractor) => (
                        <TableRow key={contractor.id}>
                          <TableCell align="right">{contractor.detail_code}</TableCell>
                          <TableCell align="right">{contractor.supplier_code || '-'}</TableCell>
                          <TableCell align="right">{contractor.name}</TableCell>
                          <TableCell align="right">{contractor.status}</TableCell>
                          <TableCell align="right">{contractor.type || '-'}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
                <TablePagination
                  component="div"
                  count={contractorsQuery.data?.total || 0}
                  page={contractorsPage}
                  onPageChange={(e, newPage) => setContractorsPage(newPage)}
                  rowsPerPage={contractorsPerPage}
                  onRowsPerPageChange={(e) => {
                    setContractorsPerPage(parseInt(e.target.value, 10));
                    setContractorsPage(0);
                  }}
                  rowsPerPageOptions={[10, 20, 50, 100]}
                  labelRowsPerPage="تعداد ردیف در صفحه:"
                  labelDisplayedRows={({ from, to, count }) => `${from}-${to} از ${count}`}
                />
              </Box>
            )}
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                فایل contractors-1
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                این فایل خلاصه فاکتورهاست. بعد از بارگذاری، داده‌ها ذخیره می‌شوند.
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                {CONTRACTORS_COLUMNS.map((column) => (
                  <Box
                    key={column}
                    sx={{ borderRadius: 1, bgcolor: 'grey.100', px: 1.5, py: 0.5, fontSize: 13, color: 'text.secondary' }}
                  >
                    {column}
                  </Box>
                ))}
              </Box>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={downloadContractorsOneTemplate}
                sx={{ mb: 2 }}
              >
                دانلود قالب Excel
              </Button>
            </Box>
            <Box
              component="form"
              onSubmit={submitContractors}
              sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}
            >
              <Button variant="outlined" component="label" startIcon={<UploadFileIcon />}>
                انتخاب فایل
                <input type="file" hidden accept=".xlsx" onChange={handleContractorsChange} />
              </Button>
              <Typography variant="body2" sx={{ minWidth: 200 }}>
                {contractorsFile ? contractorsFile.name : 'هیچ فایلی انتخاب نشده است'}
              </Typography>
              <Button type="submit" variant="contained" disabled={contractorsDisabled}>
                {contractorsMutation.isPending ? 'در حال ارسال...' : 'آپلود فایل'}
              </Button>
            </Box>
            {contractorsMutation.isError ? (
              <Alert severity="error">
                {contractorsMutation.error?.response?.data?.message || 'خطایی رخ داد. لطفاً دوباره تلاش کنید.'}
              </Alert>
            ) : null}
            {contractorsProgress && (contractorsProgress.status === 'queued' || contractorsProgress.status === 'processing') ? (
              <Box sx={{ width: '100%' }}>
                <Alert severity="info" sx={{ mb: 1 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    در حال پردازش فایل... لطفاً صبر کنید.
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={contractorsProgress.percentage || 0} 
                    sx={{ height: 8, borderRadius: 1 }}
                  />
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    {contractorsProgress.processed || 0} از {contractorsProgress.total || 0} ردیف پردازش شده ({Math.round(contractorsProgress.percentage || 0)}%)
                  </Typography>
                  
                  {/* نمایش جزئیات در حال پردازش */}
                  {contractorsProgress.metrics && (
                    <Box sx={{ mt: 2, p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
                      <Typography variant="caption" component="div" sx={{ mb: 0.5, fontWeight: 'bold' }}>
                        جزئیات پردازش:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, fontSize: '0.75rem' }}>
                        <Typography variant="caption" color="text.secondary">
                          📖 خوانده شده: {contractorsProgress.processed || 0}
                        </Typography>
                        <Typography variant="caption" color="success.main">
                          ✅ ثبت شده: {contractorsProgress.metrics.inserted || 0}
                        </Typography>
                        <Typography variant="caption" color="info.main">
                          🔄 به‌روزرسانی (تکراری): {contractorsProgress.metrics.updated || 0}
                        </Typography>
                        {contractorsProgress.metrics.errors > 0 && (
                          <Typography variant="caption" color="error.main">
                            ❌ خطا: {contractorsProgress.metrics.errors || 0}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  )}
                </Alert>
              </Box>
            ) : null}
            {contractorsProgress && contractorsProgress.status === 'failed' && contractorsProgress.error ? (
              <Alert severity="error" sx={{ mb: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                  خطا در پردازش:
                </Typography>
                <Typography variant="body2">
                  {contractorsProgress.error}
                </Typography>
              </Alert>
            ) : null}
            {contractorsProgress && contractorsProgress.metrics && (contractorsProgress.status === 'completed' || contractorsProgress.status === 'completed_with_errors') ? (
              <Alert severity={contractorsProgress.metrics.errors > 0 ? 'warning' : 'success'}>
                <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                  نتیجه نهایی:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, fontSize: '0.875rem' }}>
                  <Typography variant="body2" color="text.secondary">
                    📊 کل ردیف‌ها: {contractorsProgress.total || 0}
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    ✅ ثبت شده: {contractorsProgress.metrics.inserted || 0}
                  </Typography>
                  <Typography variant="body2" color="info.main">
                    🔄 به‌روزرسانی (تکراری): {contractorsProgress.metrics.updated || 0}
                  </Typography>
                  {contractorsProgress.metrics.errors > 0 && (
                    <Typography variant="body2" color="error.main">
                      ❌ خطا: {contractorsProgress.metrics.errors || 0}
                    </Typography>
                  )}
                </Box>
              </Alert>
            ) : null}
            {contractorsResult && !contractorsProgress?.metrics ? (
              <Alert severity={contractorsResult?.metrics?.errors ? 'warning' : 'success'}>
                <strong>نتیجه:</strong> {contractorsResult.metrics?.inserted || 0} جدید، {contractorsResult.metrics?.updated || 0} به‌روزرسانی،{' '}
                {contractorsResult.metrics?.errors || 0} خطا
              </Alert>
            ) : null}
            {contractorsErrors && contractorsErrors.length > 0 ? (
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ bgcolor: 'error.light', color: 'error.contrastText' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ErrorIcon />
                    <Typography variant="subtitle1">نمایش {contractorsErrors.length} خطا</Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Table size="small" sx={{ direction: 'rtl' }}>
                    <TableHead>
                      <TableRow>
                        <TableCell align="right">ردیف</TableCell>
                        <TableCell align="right">پیام خطا</TableCell>
                        <TableCell align="right">داده‌های مشکل‌دار</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {contractorsErrors.map((error, idx) => (
                        <TableRow key={idx}>
                          <TableCell align="right">{error.row_index}</TableCell>
                          <TableCell align="right" sx={{ color: 'error.main' }}>{error.message}</TableCell>
                          <TableCell align="right">
                            <Typography variant="caption" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                              {error.payload ? JSON.stringify(error.payload, null, 2) : '-'}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </AccordionDetails>
              </Accordion>
            ) : null}
            {summariesQuery.data && (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">داده‌های import شده ({summariesQuery.data.total} ردیف)</Typography>
                  <TextField
                    size="small"
                    placeholder="جستجو..."
                    value={summariesSearch}
                    onChange={(e) => {
                      setSummariesSearch(e.target.value);
                      setSummariesPage(0);
                    }}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <SearchIcon />
                        </InputAdornment>
                      ),
                    }}
                    sx={{ minWidth: 250 }}
                  />
                </Box>
                <Table size="small" sx={{ direction: 'rtl' }}>
                  <TableHead>
                    <TableRow>
                      <TableCell align="right">شماره روکش</TableCell>
                      <TableCell align="right">شماره اتوماسیون</TableCell>
                      <TableCell align="right">تاریخ فاکتور</TableCell>
                      <TableCell align="right">وضعیت</TableCell>
                      <TableCell align="right">مبلغ ناخالص</TableCell>
                      <TableCell align="right">مبلغ خالص</TableCell>
                      <TableCell align="right">نام تامین‌کننده</TableCell>
                      <TableCell align="right">کد تفصیلی</TableCell>
                      <TableCell align="right">کد تامین‌کننده</TableCell>
                      <TableCell align="right">بهره بردار</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {summariesQuery.isLoading ? (
                      <TableRow>
                        <TableCell colSpan={10} align="center">
                          در حال بارگذاری...
                        </TableCell>
                      </TableRow>
                    ) : summariesQuery.data.items.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={10} align="center">
                          داده‌ای یافت نشد
                        </TableCell>
                      </TableRow>
                    ) : (
                      summariesQuery.data.items.map((summary) => (
                        <TableRow key={summary.id}>
                          <TableCell align="right">{summary.cover_number || '-'}</TableCell>
                          <TableCell align="right">{summary.automation_number || '-'}</TableCell>
                          <TableCell align="right">{summary.invoice_date ? new Date(summary.invoice_date).toLocaleDateString('fa-IR') : '-'}</TableCell>
                          <TableCell align="right">{summary.invoice_status || '-'}</TableCell>
                          <TableCell align="right">{summary.gross_amount?.toLocaleString('fa-IR') || '0'}</TableCell>
                          <TableCell align="right">{summary.net_amount?.toLocaleString('fa-IR') || '0'}</TableCell>
                          <TableCell align="right">{summary.supplier_name || '-'}</TableCell>
                          <TableCell align="right">{summary.detail_code || '-'}</TableCell>
                          <TableCell align="right">{summary.supplier_code || '-'}</TableCell>
                          <TableCell align="right">{summary.business_owner || '-'}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
                <TablePagination
                  component="div"
                  count={summariesQuery.data?.total || 0}
                  page={summariesPage}
                  onPageChange={(e, newPage) => setSummariesPage(newPage)}
                  rowsPerPage={summariesPerPage}
                  onRowsPerPageChange={(e) => {
                    setSummariesPerPage(parseInt(e.target.value, 10));
                    setSummariesPage(0);
                  }}
                  rowsPerPageOptions={[10, 20, 50, 100]}
                  labelRowsPerPage="تعداد ردیف در صفحه:"
                  labelDisplayedRows={({ from, to, count }) => `${from}-${to} از ${count}`}
                />
              </Box>
            )}
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <ChecklistIcon color="primary" />
                <Typography variant="subtitle1">نمونه ردیف‌ها</Typography>
              </Box>
              <Table size="small" sx={{ direction: 'rtl' }}>
                <TableHead>
                  <TableRow>
                    <TableCell align="right">شماره روکش</TableCell>
                    <TableCell align="right">نام تامین‌کننده</TableCell>
                    <TableCell align="right">وضعیت فاکتور</TableCell>
                    <TableCell align="right">مبلغ کل</TableCell>
                    <TableCell align="right">مبلغ بدون مالیات</TableCell>
                    <TableCell align="right">بهره بردار</TableCell>
                    <TableCell align="right">تاريخ ایجاد سند حسابداری</TableCell>
                    <TableCell align="right">نام کارفرما</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {CONTRACTORS_SAMPLE_ROWS.map((row, index) => (
                    <TableRow key={`${row.cover_number}-${index}`}>
                      <TableCell align="right">{row.cover_number}</TableCell>
                      <TableCell align="right">{row.supplier_name}</TableCell>
                      <TableCell align="right">{row.status}</TableCell>
                      <TableCell align="right">{row.gross_amount}</TableCell>
                      <TableCell align="right">{row.net_amount}</TableCell>
                      <TableCell align="right">{row.business_owner}</TableCell>
                      <TableCell align="right">{row.invoice_date}</TableCell>
                      <TableCell align="right">{row.client_name || '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                فایل contractors-2
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                این فایل شامل ردیف‌های جزئیات فاکتور است (شماره سند، تاریخ، تامین‌کننده، قلم خرید و ...).
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                {CONTRACTORS2_COLUMNS.map((column) => (
                  <Box
                    key={column}
                    sx={{ borderRadius: 1, bgcolor: 'grey.100', px: 1.5, py: 0.5, fontSize: 13, color: 'text.secondary' }}
                  >
                    {column}
                  </Box>
                ))}
              </Box>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={downloadContractorsTwoTemplate}
                sx={{ mb: 2 }}
              >
                دانلود قالب Excel
              </Button>
            </Box>
            <Box component="form" onSubmit={submitContractorsTwo} sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
              <Button variant="outlined" component="label" startIcon={<UploadFileIcon />}>
                انتخاب فایل
                <input type="file" hidden accept=".xlsx" onChange={handleContractorsTwoChange} />
              </Button>
              <Typography variant="body2" sx={{ minWidth: 200 }}>
                {contractorsTwoFile ? contractorsTwoFile.name : 'هیچ فایلی انتخاب نشده است'}
              </Typography>
              <Button type="submit" variant="contained" disabled={contractorsTwoDisabled}>
                {contractorsTwoMutation.isPending ? 'در حال ارسال...' : 'آپلود فایل'}
              </Button>
            </Box>
            {contractorsTwoMutation.isError ? (
              <Alert severity="error">
                {contractorsTwoMutation.error?.response?.data?.message || 'خطایی رخ داد. لطفاً دوباره تلاش کنید.'}
              </Alert>
            ) : null}
            {contractorsTwoProgress && (contractorsTwoProgress.status === 'queued' || contractorsTwoProgress.status === 'processing') ? (
              <Box sx={{ width: '100%' }}>
                <Alert severity="info" sx={{ mb: 1 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    در حال پردازش فایل... لطفاً صبر کنید.
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={contractorsTwoProgress.percentage || 0} 
                    sx={{ height: 8, borderRadius: 1 }}
                  />
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    {contractorsTwoProgress.processed || 0} از {contractorsTwoProgress.total || 0} ردیف پردازش شده ({Math.round(contractorsTwoProgress.percentage || 0)}%)
                  </Typography>
                  
                  {/* نمایش جزئیات در حال پردازش */}
                  {contractorsTwoProgress.metrics && (
                    <Box sx={{ mt: 2, p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
                      <Typography variant="caption" component="div" sx={{ mb: 0.5, fontWeight: 'bold' }}>
                        جزئیات پردازش:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, fontSize: '0.75rem' }}>
                        <Typography variant="caption" color="text.secondary">
                          📖 خوانده شده: {contractorsTwoProgress.processed || 0}
                        </Typography>
                        <Typography variant="caption" color="success.main">
                          ✅ ثبت شده: {contractorsTwoProgress.metrics.inserted || 0}
                        </Typography>
                        <Typography variant="caption" color="info.main">
                          🔄 به‌روزرسانی (تکراری): {contractorsTwoProgress.metrics.updated || 0}
                        </Typography>
                        {contractorsTwoProgress.metrics.errors > 0 && (
                          <Typography variant="caption" color="error.main">
                            ❌ خطا: {contractorsTwoProgress.metrics.errors || 0}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  )}
                </Alert>
              </Box>
            ) : null}
            {contractorsTwoProgress && contractorsTwoProgress.status === 'failed' && contractorsTwoProgress.error ? (
              <Alert severity="error" sx={{ mb: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                  خطا در پردازش:
                </Typography>
                <Typography variant="body2">
                  {contractorsTwoProgress.error}
                </Typography>
              </Alert>
            ) : null}
            {contractorsTwoProgress && contractorsTwoProgress.metrics && (contractorsTwoProgress.status === 'completed' || contractorsTwoProgress.status === 'completed_with_errors') ? (
              <Alert severity={contractorsTwoProgress.metrics.errors > 0 ? 'warning' : 'success'}>
                <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                  نتیجه نهایی:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, fontSize: '0.875rem' }}>
                  <Typography variant="body2" color="text.secondary">
                    📊 کل ردیف‌ها: {contractorsTwoProgress.total || 0}
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    ✅ ثبت شده: {contractorsTwoProgress.metrics.inserted || 0}
                  </Typography>
                  <Typography variant="body2" color="info.main">
                    🔄 به‌روزرسانی (تکراری): {contractorsTwoProgress.metrics.updated || 0}
                  </Typography>
                  {contractorsTwoProgress.metrics.errors > 0 && (
                    <Typography variant="body2" color="error.main">
                      ❌ خطا: {contractorsTwoProgress.metrics.errors || 0}
                    </Typography>
                  )}
                </Box>
              </Alert>
            ) : null}
            {contractorsTwoResult && !contractorsTwoProgress?.metrics ? (
              <Alert severity={contractorsTwoResult?.metrics?.errors ? 'warning' : 'success'}>
                <strong>نتیجه:</strong> {contractorsTwoResult.metrics.inserted} جدید، {contractorsTwoResult.metrics.updated} به‌روزرسانی،{' '}
                {contractorsTwoResult.metrics.errors} خطا
              </Alert>
            ) : null}
            {contractorsTwoErrors && contractorsTwoErrors.length > 0 ? (
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ bgcolor: 'error.light', color: 'error.contrastText' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ErrorIcon />
                    <Typography variant="subtitle1">نمایش {contractorsTwoErrors.length} خطا</Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Table size="small" sx={{ direction: 'rtl' }}>
                    <TableHead>
                      <TableRow>
                        <TableCell align="right">ردیف</TableCell>
                        <TableCell align="right">پیام خطا</TableCell>
                        <TableCell align="right">داده‌های مشکل‌دار</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {contractorsTwoErrors.map((error, idx) => (
                        <TableRow key={idx}>
                          <TableCell align="right">{error.row_index}</TableCell>
                          <TableCell align="right" sx={{ color: 'error.main' }}>{error.message}</TableCell>
                          <TableCell align="right">
                            <Typography variant="caption" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                              {error.payload ? JSON.stringify(error.payload, null, 2) : '-'}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </AccordionDetails>
              </Accordion>
            ) : null}
            {detailsQuery.data && (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">داده‌های import شده ({detailsQuery.data.total} ردیف)</Typography>
                  <TextField
                    size="small"
                    placeholder="جستجو..."
                    value={detailsSearch}
                    onChange={(e) => {
                      setDetailsSearch(e.target.value);
                      setDetailsPage(0);
                    }}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <SearchIcon />
                        </InputAdornment>
                      ),
                    }}
                    sx={{ minWidth: 250 }}
                  />
                </Box>
                <Table size="small" sx={{ direction: 'rtl' }}>
                  <TableHead>
                    <TableRow>
                      <TableCell align="right">شماره روکش</TableCell>
                      <TableCell align="right">شماره فاکتور</TableCell>
                      <TableCell align="right">تاریخ</TableCell>
                      <TableCell align="right">احد/رمز</TableCell>
                      <TableCell align="right">تامین کننده</TableCell>
                      <TableCell align="right">وضعیت</TableCell>
                      <TableCell align="right">عنوان قلم خرید</TableCell>
                      <TableCell align="right">مبلغ ناخالص</TableCell>
                      <TableCell align="right">مبنا</TableCell>
                      <TableCell align="right">توضیحات</TableCell>
                      <TableCell align="right">کد تفصیلی</TableCell>
                      <TableCell align="right">کد تامین‌کننده</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {detailsQuery.isLoading ? (
                      <TableRow>
                        <TableCell colSpan={12} align="center">
                          در حال بارگذاری...
                        </TableCell>
                      </TableRow>
                    ) : detailsQuery.data.items.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={12} align="center">
                          داده‌ای یافت نشد
                        </TableCell>
                      </TableRow>
                    ) : (
                      detailsQuery.data.items.map((detail) => (
                        <TableRow key={detail.id}>
                          <TableCell align="right">{detail.cover_number || '-'}</TableCell>
                          <TableCell align="right">{detail.invoice_no || '-'}</TableCell>
                          <TableCell align="right">{detail.invoice_date ? new Date(detail.invoice_date).toLocaleDateString('fa-IR') : '-'}</TableCell>
                          <TableCell align="right">{detail.unit_code || '-'}</TableCell>
                          <TableCell align="right">{detail.supplier_name || '-'}</TableCell>
                          <TableCell align="right">{detail.status || '-'}</TableCell>
                          <TableCell align="right">{detail.item_title || '-'}</TableCell>
                          <TableCell align="right">{detail.gross_amount?.toLocaleString('fa-IR') || '0'}</TableCell>
                          <TableCell align="right">{detail.reference || '-'}</TableCell>
                          <TableCell align="right" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={detail.description || ''}>
                            {detail.description || '-'}
                          </TableCell>
                          <TableCell align="right">{detail.detail_code || '-'}</TableCell>
                          <TableCell align="right">{detail.supplier_code || '-'}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
                <TablePagination
                  component="div"
                  count={detailsQuery.data?.total || 0}
                  page={detailsPage}
                  onPageChange={(e, newPage) => setDetailsPage(newPage)}
                  rowsPerPage={detailsPerPage}
                  onRowsPerPageChange={(e) => {
                    setDetailsPerPage(parseInt(e.target.value, 10));
                    setDetailsPage(0);
                  }}
                  rowsPerPageOptions={[10, 20, 50, 100]}
                  labelRowsPerPage="تعداد ردیف در صفحه:"
                  labelDisplayedRows={({ from, to, count }) => `${from}-${to} از ${count}`}
                />
              </Box>
            )}
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <ChecklistIcon color="primary" />
                <Typography variant="subtitle1">نمونه ردیف‌ها</Typography>
              </Box>
              <Table size="small" sx={{ direction: 'rtl' }}>
                <TableHead>
                  <TableRow>
                    <TableCell align="right">شماره</TableCell>
                    <TableCell align="right">تاریخ</TableCell>
                    <TableCell align="right">احد/رمز تامین</TableCell>
                    <TableCell align="right">تامین کننده</TableCell>
                    <TableCell align="right">وضعیت</TableCell>
                    <TableCell align="right">عنوان قلم خرید</TableCell>
                    <TableCell align="right">مبلغ ناخالص</TableCell>
                    <TableCell align="right">مبنا</TableCell>
                    <TableCell align="right">توضیحات</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {CONTRACTORS2_SAMPLE_ROWS.map((row) => (
                    <TableRow key={row.invoice_no}>
                      <TableCell align="right">{row.invoice_no}</TableCell>
                      <TableCell align="right">{row.date}</TableCell>
                      <TableCell align="right">{row.unit}</TableCell>
                      <TableCell align="right">{row.supplier}</TableCell>
                      <TableCell align="right">{row.status}</TableCell>
                      <TableCell align="right">{row.item_title}</TableCell>
                      <TableCell align="right">{row.gross_amount}</TableCell>
                      <TableCell align="right">{row.reference}</TableCell>
                      <TableCell align="right">{row.description}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          </Box>
        </TabPanel>
      </Paper>
    </AppLayout>
  );
}

export default AdminUploadPage;

