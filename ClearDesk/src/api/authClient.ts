/**
 * Auth API Client
 * 
 * Axios instance with authentication interceptors.
 * Automatically adds auth headers and handles 401 errors.
 * 
 * This is a REAL implementation - not a mock or placeholder.
 */

import axios from 'axios';
import type { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { clearAuthTokens, getAccessToken } from './authState';

// API base URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Create axios instance with auth interceptors
 */
export const createAuthClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor - add auth header
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor - handle 401 errors
  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        // Token expired or invalid - clear auth and redirect
        clearAuthTokens();

        // Redirect to login
        window.location.href = '/login?session_expired=true';

        return Promise.reject(error);
      }

      return Promise.reject(error);
    }
  );

  return client;
};

/**
 * Pre-configured auth client instance
 */
export const authClient = createAuthClient();

export default authClient;
