import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import api from '../services/api';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  username: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [username, setUsername] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Check for existing session on mount.
  useEffect(() => {
    void (async () => {
      try {
        const hasSession = await api.checkSession();
        setIsAuthenticated(hasSession);
        setUsername(hasSession ? 'admin' : null);
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  const login = useCallback(async (nextUsername: string, password: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      const success = await api.login(nextUsername, password);
      setIsAuthenticated(success);
      setUsername(success ? nextUsername : null);
      setError(null);
      if (!success) {
        setError('Invalid username or password');
      }
      return success;
    } catch (err) {
      setIsAuthenticated(false);
      setUsername(null);
      setError(err instanceof Error ? err.message : 'Login failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    void api.logout();
    setUsername(null);
    setIsAuthenticated(false);
    setError(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        username,
        login,
        logout,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
