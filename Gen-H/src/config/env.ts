// Environment configuration for GEN-H Studio

export const ENV = {
  // API Configuration
  API_BASE_URL: (import.meta.env.PROD && !import.meta.env.VITE_API_BASE_URL) 
    ? (() => { throw new Error('VITE_API_BASE_URL must be set in production'); })()
    : (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'),
  
  // Admin Configuration
  ADMIN_USER: import.meta.env.VITE_ADMIN_USER || 'admin',
  
  // Feature Flags
  ENABLE_ADMIN: import.meta.env.VITE_ENABLE_ADMIN !== 'false',
  
  // Environment
  NODE_ENV: import.meta.env.MODE,
  IS_DEV: import.meta.env.DEV,
  IS_PROD: import.meta.env.PROD,
} as const;

// Validate required environment variables in production
if (ENV.IS_PROD) {
  if (!import.meta.env.VITE_API_BASE_URL) {
    console.warn('[ENV] VITE_API_BASE_URL not set. Using default: http://localhost:8000');
  }
}
