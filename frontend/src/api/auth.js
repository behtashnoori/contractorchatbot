import { apiClient } from './client.js';

export const login = async (credentials) => {
  const { data } = await apiClient.post('/auth/login', credentials);
  return data;
};

export const fetchMe = async () => {
  const { data } = await apiClient.get('/auth/me');
  return data;
};

export const changePassword = async (payload) => {
  const { data } = await apiClient.post('/auth/change-password', payload);
  return data;
};

