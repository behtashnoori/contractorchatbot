import { apiClient } from './client.js';

export const fetchInvoices = async (params) => {
  const { data } = await apiClient.get('/invoices/', { params });
  return data;
};

export const fetchInvoiceDetail = async (coverNumber) => {
  const { data } = await apiClient.get(`/invoices/${coverNumber}`);
  return data;
};

