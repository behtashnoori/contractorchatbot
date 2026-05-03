import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import PropTypes from 'prop-types';
import { useQueryClient } from '@tanstack/react-query';
import { login as loginApi, fetchMe } from '../api/auth.js';
import { authStorage } from '../api/authStorage.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const queryClient = useQueryClient();
  const [authState, setAuthState] = useState({
    isAuthenticated: false,
    loading: true,
    user: null,
    contractor: null,
    totals: null,
    mustChangePassword: false,
  });

  useEffect(() => {
    const bootstrap = async () => {
      const token = authStorage.getAccessToken();
      if (!token) {
        setAuthState((prev) => ({ ...prev, loading: false }));
        return;
      }
      try {
        const data = await fetchMe();
        setAuthState({
          isAuthenticated: true,
          loading: false,
          user: data.user,
          contractor: data.contractor,
          totals: data.totals,
          mustChangePassword: data.user?.must_change_password ?? false,
        });
      } catch (error) {
        console.error('[AuthProvider] Bootstrap auth failed');
        authStorage.clear();
        setAuthState({
          isAuthenticated: false,
          loading: false,
          user: null,
          contractor: null,
          totals: null,
          mustChangePassword: false,
        });
      }
    };
    bootstrap();
  }, []);

  const handleLogin = useCallback(async (credentials) => {
    const data = await loginApi(credentials);
    authStorage.setAccessToken(data.access_token);
    authStorage.setRefreshToken(data.refresh_token);
    const profile = await fetchMe();
    setAuthState({
      isAuthenticated: true,
      loading: false,
      user: profile.user,
      contractor: profile.contractor,
      totals: profile.totals,
      mustChangePassword: !!data.must_change_password,
    });
    return data;
  }, []);

  const logout = useCallback(() => {
    authStorage.clear();
    queryClient.clear();
    setAuthState({
      isAuthenticated: false,
      loading: false,
      user: null,
      contractor: null,
      totals: null,
      mustChangePassword: false,
    });
  }, [queryClient]);

  const value = useMemo(
    () => ({
      ...authState,
      login: handleLogin,
      logout,
      setTotals: (totals) => setAuthState((prev) => ({ ...prev, totals })),
      setProfile: (profile) =>
        setAuthState((prev) => ({
          ...prev,
          user: profile.user ?? prev.user,
          contractor: profile.contractor ?? prev.contractor,
        })),
    }),
    [authState, handleLogin, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

AuthProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuthContext = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuthContext must be used within AuthProvider');
  }
  return ctx;
};

