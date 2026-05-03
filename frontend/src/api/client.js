import axios from 'axios';
import { authStorage } from './authStorage.js';

const REFRESH_TIMEOUT_MS = 30_000;

/**
 * تشخیص خودکار API Base URL
 * - اگر VITE_API_BASE_URL تنظیم شده باشد (production)، از آن استفاده می‌کند
 * - اگر hostname localhost یا 127.0.0.1 باشد، از localhost:8000 استفاده می‌کند
 * - در غیر این صورت (دسترسی از شبکه)، از همان hostname استفاده می‌کند
 */
const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }

  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;

    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000';
    }

    return `http://${hostname}:8000`;
  }

  return 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();

const defaultTimeout = Number(import.meta.env.VITE_API_TIMEOUT_MS) || 120_000;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: defaultTimeout,
});

apiClient.interceptors.request.use((config) => {
  if (!config.headers.Authorization) {
    const token = authStorage.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

let isRefreshing = false;
let pendingQueue = [];

const processQueue = (error, token = null) => {
  pendingQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  pendingQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response?.status !== 401 ||
      originalRequest._retry ||
      originalRequest.url?.includes('/auth/login') ||
      originalRequest.url?.includes('/auth/refresh')
    ) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingQueue.push({ resolve, reject });
      })
        .then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        })
        .catch((err) => {
          return Promise.reject(err);
        });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const refreshToken = authStorage.getRefreshToken();

      if (!refreshToken) {
        authStorage.clear();
        throw new Error('No refresh token available');
      }

      const { data } = await axios.post(
        `${API_BASE_URL}/auth/refresh`,
        {},
        {
          headers: { Authorization: `Bearer ${refreshToken}` },
          timeout: REFRESH_TIMEOUT_MS,
        },
      );

      const newAccessToken = data.access_token;
      if (newAccessToken) {
        authStorage.setAccessToken(newAccessToken);
        processQueue(null, newAccessToken);

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        delete originalRequest._retry;

        const retryConfig = {
          ...originalRequest,
          headers: {
            ...originalRequest.headers,
            Authorization: `Bearer ${newAccessToken}`,
          },
        };
        const retryResponse = await apiClient(retryConfig);
        return retryResponse;
      }
      throw new Error('No access token in refresh response');
    } catch (refreshError) {
      processQueue(refreshError, null);
      authStorage.clear();
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);
