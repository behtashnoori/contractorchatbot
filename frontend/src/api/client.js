import axios from 'axios';
import { authStorage } from './authStorage.js';

/**
 * تشخیص خودکار API Base URL
 * - اگر VITE_API_BASE_URL تنظیم شده باشد (production)، از آن استفاده می‌کند
 * - اگر hostname localhost یا 127.0.0.1 باشد، از localhost:8000 استفاده می‌کند
 * - در غیر این صورت (دسترسی از شبکه)، از همان hostname استفاده می‌کند
 */
const getApiBaseUrl = () => {
  // اولویت 1: اگر environment variable تنظیم شده باشد (برای production)
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  
  // در مرورگر (client-side)
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const port = window.location.port;
    
    // اگر localhost یا 127.0.0.1 باشد، از localhost:8000 استفاده کن
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000';
    }
    
    // در غیر این صورت (دسترسی از شبکه)، از همان hostname استفاده کن
    // فرض می‌کنیم backend روی پورت 8000 اجرا می‌شود
    return `http://${hostname}:8000`;
  }
  
  // Fallback برای server-side rendering
  return 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();

// Log برای debugging (همیشه log کن برای troubleshooting موبایل)
console.log('[API Client] Base URL:', API_BASE_URL);
if (typeof window !== 'undefined') {
  console.log('[API Client] Window location:', window.location.href);
  console.log('[API Client] Hostname:', window.location.hostname);
  console.log('[API Client] Port:', window.location.port);
  console.log('[API Client] Origin:', window.location.origin);
  console.log('[API Client] User Agent:', navigator.userAgent);
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 600000, // 10 minutes default timeout
});

apiClient.interceptors.request.use((config) => {
  // Only set token if not already set (to allow manual override after refresh)
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
    
    // Skip refresh for login/refresh endpoints or if already retried
    if (
      error.response?.status !== 401 ||
      originalRequest._retry ||
      originalRequest.url?.includes('/auth/login') ||
      originalRequest.url?.includes('/auth/refresh')
    ) {
      return Promise.reject(error);
    }

    // If already refreshing, queue this request
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
      console.log('[Auth Interceptor] Attempting to refresh access token...');
      const refreshToken = authStorage.getRefreshToken();
      
      if (!refreshToken) {
        console.error('[Auth Interceptor] No refresh token available');
        authStorage.clear();
        throw new Error('No refresh token available');
      }
      
      console.log('[Auth Interceptor] Refresh token found, calling refresh endpoint...');
      const { data } = await axios.post(
        `${API_BASE_URL}/auth/refresh`,
        {},
        {
          headers: { Authorization: `Bearer ${refreshToken}` },
        },
      );
      
      const newAccessToken = data.access_token;
      if (newAccessToken) {
        console.log('[Auth Interceptor] Token refresh successful');
        authStorage.setAccessToken(newAccessToken);
        processQueue(null, newAccessToken);
        
        // Update the original request with new token
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        
        // Remove _retry flag to allow this request to go through normally
        delete originalRequest._retry;
        
        console.log('[Auth Interceptor] Retrying original request with new token');
        console.log('[Auth Interceptor] Request URL:', originalRequest.url);
        // Create a new request config to ensure fresh token is used
        const retryConfig = {
          ...originalRequest,
          headers: {
            ...originalRequest.headers,
            Authorization: `Bearer ${newAccessToken}`,
          },
        };
        const retryResponse = await apiClient(retryConfig);
        console.log('[Auth Interceptor] Retry request successful');
        return retryResponse;
      } else {
        console.error('[Auth Interceptor] No access token in refresh response');
        throw new Error('No access token in refresh response');
      }
    } catch (refreshError) {
      console.error('[Auth Interceptor] Token refresh failed:', {
        message: refreshError.message,
        response: refreshError.response?.data,
        status: refreshError.response?.status,
        url: originalRequest.url,
      });
      processQueue(refreshError, null);
      authStorage.clear();
      // Redirect to login if we're not already there
      if (window.location.pathname !== '/login') {
        console.log('[Auth Interceptor] Redirecting to login page');
        window.location.href = '/login';
      }
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);

