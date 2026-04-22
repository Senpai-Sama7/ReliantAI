/**
 * useAuth Hook
 * 
 * Custom hook for accessing auth context in components.
 * Provides convenient access to authentication state and methods.
 * 
 * This is a REAL implementation - not a mock or placeholder.
 */

import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';

/**
 * useAuth - Hook to access authentication context
 * 
 * Usage:
 * ```tsx
 * function MyComponent() {
 *   const { isAuthenticated, user, login, logout } = useAuth();
 *   
 *   if (!isAuthenticated) {
 *     return <LoginForm onLogin={login} />;
 *   }
 *   
 *   return <div>Welcome, {user?.username}</div>;
 * }
 * ```
 */
export const useAuth = () => {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
};

export default useAuth;
