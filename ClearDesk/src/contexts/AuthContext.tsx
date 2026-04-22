import React, { createContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import { clearAuthTokens, getAuthTokens, setAuthTokens, type AuthTokens } from '../api/authState';

const AUTH_SERVICE_URL = import.meta.env.VITE_AUTH_SERVICE_URL || 'http://localhost:8080';
const TOKEN_REFRESH_BUFFER = 5 * 60 * 1000;

interface User {
  username: string;
  email?: string;
  full_name?: string;
  roles: string[];
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  tokens: AuthTokens | null;
  isLoading: boolean;
  error: string | null;
}

interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  getAccessToken: () => string | null;
  hasRole: (role: string) => boolean;
}

const defaultAuthContext: AuthContextType = {
  isAuthenticated: false,
  user: null,
  tokens: null,
  isLoading: true,
  error: null,
  login: async () => false,
  logout: () => {},
  refreshToken: async () => false,
  getAccessToken: () => null,
  hasRole: () => false,
};

export const AuthContext = createContext<AuthContextType>(defaultAuthContext);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    tokens: null,
    isLoading: true,
    error: null,
  });

  const parseJwt = (token: string): any | null => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Failed to parse JWT:', error);
      return null;
    }
  };

  const clearAuthState = useCallback(() => {
    clearAuthTokens();
    setState({
      isAuthenticated: false,
      user: null,
      tokens: null,
      isLoading: false,
      error: null,
    });
  }, []);

  useEffect(() => {
    const tokens = getAuthTokens();
    if (!tokens) {
      setState(prev => ({ ...prev, isLoading: false }));
      return;
    }

    const tokenData = parseJwt(tokens.access_token);
    if (tokenData && tokenData.exp * 1000 > Date.now()) {
      setState(prev => ({
        ...prev,
        isAuthenticated: true,
        tokens,
        isLoading: false,
      }));
      return;
    }

    clearAuthState();
  }, [clearAuthState]);

  useEffect(() => {
    if (!state.tokens?.access_token) {
      return;
    }

    const tokenData = parseJwt(state.tokens.access_token);
    if (!tokenData?.exp) {
      return;
    }

    const expiryTime = tokenData.exp * 1000;
    const refreshTime = expiryTime - Date.now() - TOKEN_REFRESH_BUFFER;

    if (refreshTime <= 0) {
      void refreshToken();
      return;
    }

    const timeoutId = setTimeout(() => {
      void refreshToken();
    }, refreshTime);

    return () => clearTimeout(timeoutId);
  }, [state.tokens]);

  const login = useCallback(async (username: string, password: string): Promise<boolean> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await fetch(`${AUTH_SERVICE_URL}/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username,
          password,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: errorData.detail || 'Login failed',
        }));
        return false;
      }

      const tokens: AuthTokens = await response.json();
      const userResponse = await fetch(`${AUTH_SERVICE_URL}/users/me`, {
        headers: {
          Authorization: `Bearer ${tokens.access_token}`,
        },
      });

      if (!userResponse.ok) {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: 'Failed to fetch user information',
        }));
        return false;
      }

      const user: User = await userResponse.json();
      setAuthTokens(tokens);
      setState({
        isAuthenticated: true,
        user,
        tokens,
        isLoading: false,
        error: null,
      });
      return true;
    } catch (error) {
      console.error('Login error:', error);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Network error. Please try again.',
      }));
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    clearAuthState();
  }, [clearAuthState]);

  const refreshToken = useCallback(async (): Promise<boolean> => {
    const tokens = getAuthTokens();
    if (!tokens) {
      return false;
    }

    try {
      const response = await fetch(`${AUTH_SERVICE_URL}/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: tokens.refresh_token }),
      });

      if (!response.ok) {
        logout();
        return false;
      }

      const newTokens: AuthTokens = await response.json();
      setAuthTokens(newTokens);
      setState(prev => ({
        ...prev,
        tokens: newTokens,
      }));
      return true;
    } catch (error) {
      console.error('Token refresh error:', error);
      return false;
    }
  }, [logout]);

  const getAccessToken = useCallback((): string | null => {
    return state.tokens?.access_token || null;
  }, [state.tokens]);

  const hasRole = useCallback((role: string): boolean => {
    return state.user?.roles.includes(role) || false;
  }, [state.user]);

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        logout,
        refreshToken,
        getAccessToken,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
