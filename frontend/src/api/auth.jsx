import { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  apiRequest,
  clearTokens,
  saveTokens,
  setAuthFailureHandler,
} from "./client.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setAuthFailureHandler(() => setUser(null));
    apiRequest("/auth/me/")
      .then(setUser)
      .catch(() => {
        clearTokens();
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      async login(email, password) {
        const data = await apiRequest(
          "/auth/token/",
          {
            method: "POST",
            body: { email, password },
          },
          false,
        );
        saveTokens(data);
        setUser(data.user);
      },
      async register(payload) {
        const data = await apiRequest(
          "/auth/register/",
          {
            method: "POST",
            body: payload,
          },
          false,
        );
        saveTokens(data);
        setUser(data.user);
      },
      logout() {
        clearTokens();
        setUser(null);
      },
    }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
