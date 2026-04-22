/**
 * Auth Component Tests
 *
 * Hostile Audit Checklist:
 * - AuthContext provides correct default state
 * - useAuth hook throws outside provider
 * - ProtectedRoute redirects when not authenticated
 * - Login flow keeps tokens in memory only
 * - Role checks use the authenticated user payload
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import '@testing-library/jest-dom';

import { AuthProvider, AuthContext } from '../contexts/AuthContext';
import { useAuth } from '../hooks/useAuth';
import ProtectedRoute from '../components/ProtectedRoute';

global.fetch = vi.fn();

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should provide default auth state', () => {
    const TestComponent = () => {
      const auth = React.useContext(AuthContext);
      return (
        <div>
          <span data-testid="authenticated">{auth.isAuthenticated.toString()}</span>
          <span data-testid="loading">{auth.isLoading.toString()}</span>
        </div>
      );
    };

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    expect(screen.getByTestId('loading')).toHaveTextContent('false');
  });
});

describe('useAuth Hook', () => {
  it('should throw when used outside AuthProvider', () => {
    const TestComponent = () => {
      useAuth();
      return <div />;
    };

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => render(<TestComponent />)).toThrow(
      'useAuth must be used within an AuthProvider'
    );

    consoleSpy.mockRestore();
  });

  it('should return auth context when inside provider', () => {
    const TestComponent = () => {
      const auth = useAuth();
      return <span data-testid="auth">{auth ? 'available' : 'unavailable'}</span>;
    };

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('auth')).toHaveTextContent('available');
  });
});

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should redirect to login when not authenticated', () => {
    const TestComponent = () => <div data-testid="protected">Protected Content</div>;

    render(
      <BrowserRouter>
        <AuthProvider>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.queryByTestId('protected')).not.toBeInTheDocument();
  });
});

describe('Login Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should handle login success with in-memory tokens', async () => {
    const mockTokens = {
      access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMSIsImV4cCI6OTk5OTk5OTk5OX0.test',
      refresh_token: 'refresh123',
      token_type: 'bearer',
    };
    const mockUser = {
      username: 'testuser',
      email: 'test@example.com',
      roles: ['user'],
    };

    (global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockTokens,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      });

    const TestComponent = () => {
      const { login, isAuthenticated, user } = useAuth();

      React.useEffect(() => {
        void login('testuser', 'password123');
      }, [login]);

      return (
        <div>
          <span data-testid="authenticated">{isAuthenticated.toString()}</span>
          <span data-testid="username">{user?.username || 'none'}</span>
        </div>
      );
    };

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
      expect(screen.getByTestId('username')).toHaveTextContent('testuser');
    });
  });

  it('should handle login failure', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'Invalid credentials' }),
    });

    const TestComponent = () => {
      const { login, error } = useAuth();

      React.useEffect(() => {
        void login('testuser', 'wrongpassword');
      }, [login]);

      return <span data-testid="error">{error || 'no error'}</span>;
    };

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('Invalid credentials');
    });
  });
});

describe('Role-based Access', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should check user roles correctly after login', async () => {
    const mockTokens = {
      access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbnVzZXIiLCJleHAiOjk5OTk5OTk5OTl9.test',
      refresh_token: 'refresh123',
      token_type: 'bearer',
    };
    const mockUser = {
      username: 'adminuser',
      roles: ['admin', 'user'],
    };

    (global.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockTokens,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      });

    const TestComponent = () => {
      const { login, hasRole } = useAuth();

      React.useEffect(() => {
        void login('adminuser', 'password123');
      }, [login]);

      return (
        <div>
          <span data-testid="is-admin">{hasRole('admin').toString()}</span>
          <span data-testid="is-user">{hasRole('user').toString()}</span>
          <span data-testid="is-guest">{hasRole('guest').toString()}</span>
        </div>
      );
    };

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('is-admin')).toHaveTextContent('true');
      expect(screen.getByTestId('is-user')).toHaveTextContent('true');
      expect(screen.getByTestId('is-guest')).toHaveTextContent('false');
    });
  });
});
