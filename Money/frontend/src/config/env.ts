// Environment configuration for GEN-H Studio
// Unified System: Frontend is served by the backend, so API calls use relative paths

export const ENV = {
  // API Configuration - Use relative URL since frontend is served by backend
  // In dev mode, you can set VITE_API_BASE_URL=http://localhost:8000
  // In production (unified mode), this defaults to empty string for relative paths
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || '',
  
  // Admin Configuration
  ADMIN_USER: import.meta.env.VITE_ADMIN_USER || 'admin',
  
  // Feature Flags
  ENABLE_ADMIN: import.meta.env.VITE_ENABLE_ADMIN !== 'false',
  
  // Environment
  NODE_ENV: import.meta.env.MODE,
  IS_DEV: import.meta.env.DEV,
  IS_PROD: import.meta.env.PROD,
} as const;

// Log configuration in dev mode
if (ENV.IS_DEV) {
  console.log('[ENV] API_BASE_URL:', ENV.API_BASE_URL || '(relative - same origin)');
}
