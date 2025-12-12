import axios from 'axios';
import { authStorage } from './authStorage.js';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3855';

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

