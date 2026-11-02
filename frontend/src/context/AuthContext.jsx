import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('user_info');
      const savedToken = localStorage.getItem('access_token');

      // Never restore a user without a real access token.
      return savedUser && savedToken ? JSON.parse(savedUser) : null;
    } catch {
      localStorage.removeItem('user_info');
      localStorage.removeItem('access_token');
      return null;
    }
  });

  const [token, setToken] = useState(
    () => localStorage.getItem('access_token') || null
  );

  useEffect(() => {
    if (user && token) {
      localStorage.setItem('user_info', JSON.stringify(user));
    } else {
      localStorage.removeItem('user_info');
    }
  }, [user, token]);

  const login = async (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    try {
      const res = await api.post('/auth/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const accessToken = res.data.access_token;

      if (!accessToken) {
        throw new Error('Login response did not contain an access token.');
      }

      // Store the real token before requesting the authenticated profile.
      localStorage.setItem('access_token', accessToken);
      setToken(accessToken);

      const meRes = await api.get('/auth/me');

      if (!meRes.data) {
        throw new Error('Could not retrieve authenticated user profile.');
      }

      setUser(meRes.data);
      localStorage.setItem('user_info', JSON.stringify(meRes.data));

      return meRes.data;
    } catch (error) {
      // Never keep a partially authenticated session.
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
      setToken(null);
      setUser(null);

      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_info');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isAdmin: user?.role === 'admin',
        isStaff: user?.role === 'staff' || user?.role === 'admin',
        isCustomer: user?.role === 'customer',
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}
