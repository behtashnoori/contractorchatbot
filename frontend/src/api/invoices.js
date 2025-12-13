import { apiClient } from './client.js';

export const fetchInvoices = async (params) => {
  const { data } = await apiClient.get('/invoices/', { params });
  return data;
};

export const fetchInvoiceDetail = async (coverNumber) => {
  const { data } = await apiClient.get(`/invoices/${coverNumber}`);
  return data;
};

export const fetchFilterOptions = async (filters = {}) => {
  const params = {};
  if (filters.fiscal_year) {
    params.fiscal_year = filters.fiscal_year;
  }
  if (filters.status) {
    params.status = filters.status;
  }
  const { data } = await apiClient.get('/invoices/filters/options', { params });
  return data;
};

