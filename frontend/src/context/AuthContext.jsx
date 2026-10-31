import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const DEFAULT_USERS = {
  admin: {
    id: 'user-admin-01',
    email: 'admin@brightloop.com',
    full_name: 'Alexander Wright',
    role: 'admin',
    status: 'active',
  },
  staff: {
    id: 'user-staff-01',
    email: 'staff@brightloop.com',
    full_name: 'Chloe Bennett',
    role: 'staff',
    status: 'active',
  },
  customer: {
    id: 'user-cust-01',
    email: 'customer@acmecloud.com',
    full_name: 'Sarah Jenkins (Acme Cloud)',
    role: 'customer',
    status: 'active',
    customer_id: 'cust-001',
  },
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user_info');
    return saved ? JSON.parse(saved) : DEFAULT_USERS.admin;
  });
  const [token, setToken] = useState(() => localStorage.getItem('access_token') || 'mock-demo-jwt-token');

  useEffect(() => {
    if (user) {
      localStorage.setItem('user_info', JSON.stringify(user));
    } else {
      localStorage.removeItem('user_info');
    }
  }, [user]);

  const login = async (email, password) => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const res = await api.post('/auth/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      const accessToken = res.data.access_token;
      setToken(accessToken);
      localStorage.setItem('access_token', accessToken);

      // Fetch profile
      try {
        const meRes = await api.get('/auth/me');
        setUser(meRes.data);
        return meRes.data;
      } catch {
        const mockMatch = Object.values(DEFAULT_USERS).find((u) => u.email === email) || {
          id: 'user-custom',
          email,
          full_name: email.split('@')[0],
          role: 'staff',
          status: 'active',
        };
        setUser(mockMatch);
        return mockMatch;
      }
    } catch {
      // Fallback demo login
      const mockMatch = Object.values(DEFAULT_USERS).find((u) => u.email === email) || {
        id: 'user-custom',
        email,
        full_name: email.split('@')[0],
        role: 'staff',
        status: 'active',
      };
      setToken('mock-demo-jwt-token');
      localStorage.setItem('access_token', 'mock-demo-jwt-token');
      setUser(mockMatch);
      return mockMatch;
    }
  };

  const loginAs = (roleKey) => {
    const targetUser = DEFAULT_USERS[roleKey] || DEFAULT_USERS.admin;
    setUser(targetUser);
    setToken('mock-demo-jwt-token');
    localStorage.setItem('access_token', 'mock-demo-jwt-token');
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
        isAuthenticated: !!user,
        isAdmin: user?.role === 'admin',
        isStaff: user?.role === 'staff' || user?.role === 'admin',
        isCustomer: user?.role === 'customer',
        login,
        loginAs,
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
