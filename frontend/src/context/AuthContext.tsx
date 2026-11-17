import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, AuthState } from '../types';
import { api } from '../services/api';

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('attendai_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      const savedToken = localStorage.getItem('attendai_token');
      const savedUser = localStorage.getItem('attendai_user');
      if (savedToken && savedUser) {
        try {
          setUser(JSON.parse(savedUser));
          setToken(savedToken);
          // Verify with /auth/me
          const res = await api.get('/auth/me');
          setUser(res.data);
          localStorage.setItem('attendai_user', JSON.stringify(res.data));
        } catch (e) {
          console.warn('Session verification failed, logging out');
          localStorage.removeItem('attendai_token');
          localStorage.removeItem('attendai_refresh_token');
          localStorage.removeItem('attendai_user');
          setUser(null);
          setToken(null);
        }
      }
      setIsLoading(false);
    };
    initAuth();
  }, []);

  const login = async (email: string, password: string): Promise<User> => {
    const res = await api.post('/auth/login', { email, password });
    const { access_token, refresh_token, user: userData } = res.data;
    localStorage.setItem('attendai_token', access_token);
    localStorage.setItem('attendai_refresh_token', refresh_token);
    localStorage.setItem('attendai_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const logout = async () => {
    const rt = localStorage.getItem('attendai_refresh_token');
    if (rt) {
      try {
        await api.post('/auth/logout', { refresh_token: rt });
      } catch (e) {
        // ignore logout errors
      }
    }
    localStorage.removeItem('attendai_token');
    localStorage.removeItem('attendai_refresh_token');
    localStorage.removeItem('attendai_user');
    setUser(null);
    setToken(null);
  };

  const refreshUser = async () => {
    try {
      const res = await api.get('/auth/me');
      setUser(res.data);
      localStorage.setItem('attendai_user', JSON.stringify(res.data));
    } catch (e) {
      console.error('Failed to refresh user:', e);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
