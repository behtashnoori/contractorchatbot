import { apiClient } from './client.js';

const devError = (...args) => {
  if (import.meta.env.DEV) {
    console.error(...args);
  }
};

const uploadFile = async (url, file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const { data } = await apiClient.post(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 900000, // 15 minutes for large file uploads
    });
    return data;
  } catch (error) {
    devError('Upload failed', {
      status: error?.response?.status,
      code: error?.code,
      message: error?.message,
    });
    
    if (error.code === 'ECONNABORTED') {
      throw new Error('زمان آپلود به پایان رسید. فایل شما در حال پردازش است، لطفاً چند دقیقه صبر کنید و دوباره تلاش کنید.');
    }
    throw error;
  }
};

export const uploadCodTafsiltamin = (file) => uploadFile('/admin/uploads/codtafsiltamin', file);

export const uploadContractorsOne = (file) => uploadFile('/admin/uploads/contractors-1', file);

export const uploadContractorsTwo = (file) => uploadFile('/admin/uploads/contractors-2', file);

const downloadTemplate = async (url, filename) => {
  const response = await apiClient.get(url, {
    responseType: 'blob',
  });
  const blob = new Blob([response.data], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(downloadUrl);
};

export const downloadCodTafsiltaminTemplate = () =>
  downloadTemplate('/admin/templates/codtafsiltamin', 'codtafsiltamin_template.xlsx');

export const downloadContractorsOneTemplate = () =>
  downloadTemplate('/admin/templates/contractors-1', 'contractors-1_template.xlsx');

export const downloadContractorsTwoTemplate = () =>
  downloadTemplate('/admin/templates/contractors-2', 'contractors-2_template.xlsx');

export const getBatchErrors = async (batchId) => {
  const { data } = await apiClient.get(`/admin/uploads/${batchId}`);
  return data;
};

export const getContractors = async (params = {}) => {
  const { data } = await apiClient.get('/admin/contractors', { params });
  return data;
};

export const getUploadProgress = async (batchId) => {
  const { data } = await apiClient.get(`/admin/uploads/${batchId}/progress`);
  return data;
};

export const getInvoiceSummaries = async (params = {}) => {
  const { data } = await apiClient.get('/admin/invoice-summaries', { params });
  return data;
};

export const getInvoiceDetails = async (params = {}) => {
  const { data } = await apiClient.get('/admin/invoice-details', { params });
  return data;
};
