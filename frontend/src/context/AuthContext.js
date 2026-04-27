import React, { createContext, useState, useContext, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

// Global axios interceptor for 401 handling
let isRefreshing = false;
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Don't retry for refresh endpoint or if already retried
    if (error.response?.status === 401 && 
        !originalRequest._retry && 
        !originalRequest.url?.includes('/auth/refresh') &&
        !originalRequest.url?.includes('/auth/me')) {
      
      if (!isRefreshing) {
        isRefreshing = true;
        originalRequest._retry = true;
        
        try {
          await axios.post(`${API_URL}/auth/refresh`, {}, { withCredentials: true });
          isRefreshing = false;
          // Retry the original request
          return axios(originalRequest);
        } catch {
          isRefreshing = false;
          // Refresh failed - session is truly expired
          window.dispatchEvent(new Event('auth:session-expired'));
        }
      }
    }
    return Promise.reject(error);
  }
);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const inactivityTimerRef = useRef(null);

  const SESSION_TIMEOUT_MS = 24 * 60 * 60 * 1000; // 24 hours
  const INACTIVITY_WARNING_MS = 23 * 60 * 60 * 1000; // 23 hours

  const handleSessionExpired = useCallback(() => {
    setUser(false);
  }, []);

  useEffect(() => {
    window.addEventListener('auth:session-expired', handleSessionExpired);
    return () => window.removeEventListener('auth:session-expired', handleSessionExpired);
  }, [handleSessionExpired]);

  // Reset inactivity timer on user activity
  useEffect(() => {
    if (!user) return;

    const resetTimer = () => {
      if (inactivityTimerRef.current) clearTimeout(inactivityTimerRef.current);
      inactivityTimerRef.current = setTimeout(() => {
        handleSessionExpired();
      }, SESSION_TIMEOUT_MS);
    };

    const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];
    events.forEach((e) => window.addEventListener(e, resetTimer));
    resetTimer();

    return () => {
      events.forEach((e) => window.removeEventListener(e, resetTimer));
      if (inactivityTimerRef.current) clearTimeout(inactivityTimerRef.current);
    };
  }, [user, handleSessionExpired]);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const { data } = await axios.get(`${API_URL}/auth/me`, {
        withCredentials: true,
      });
      setUser(data);
    } catch {
      setUser(false);
    } finally {
      setLoading(false);
    }
  };

  // Direct login (no OTP)
  const login = async (email, password, captchaToken) => {
    const { data } = await axios.post(
      `${API_URL}/auth/login`,
      { email, password, captcha_token: captchaToken || '' },
      { withCredentials: true }
    );
    setUser(data);
    return data;
  };

  // Step 1: Email + Password → returns login_session_id
  const loginStep1 = async (email, password, captchaToken) => {
    const { data } = await axios.post(
      `${API_URL}/auth/login-step1`,
      { email, password, captcha_token: captchaToken || '' },
      { withCredentials: true }
    );
    return data; // { message, login_session_id }
  };

  // Step 2: OTP Verification → sets user
  const verifyOtp = async (loginSessionId, otpCode) => {
    const { data } = await axios.post(
      `${API_URL}/auth/verify-otp`,
      { login_session_id: loginSessionId, otp_code: otpCode },
      { withCredentials: true }
    );
    setUser(data);
    return data;
  };

  const logout = async () => {
    try {
      await axios.post(`${API_URL}/auth/logout`, {}, { withCredentials: true });
    } catch {
      // ignore
    }
    setUser(false);
  };

  // Session polling - check every 30 seconds if session is still valid
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(async () => {
      try {
        await axios.get(`${API_URL}/auth/session-check`, { withCredentials: true });
      } catch (err) {
        if (err.response?.status === 401) {
          setUser(false);
          window.alert('Un altro admin ha effettuato l\'accesso. La tua sessione è stata chiusa.');
        }
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [user]);

  const changePassword = async (currentPassword, newPassword) => {
    const { data } = await axios.post(
      `${API_URL}/auth/change-password`,
      { current_password: currentPassword, new_password: newPassword },
      { withCredentials: true }
    );
    return data;
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, loginStep1, verifyOtp, logout, changePassword }}>
      {children}
    </AuthContext.Provider>
  );
};
