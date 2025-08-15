import { createContext, useContext, useState, useEffect } from "react";
import axiosInstance from "../api/axiosinstance";
import { useMergeGuestCartMutation } from "./cartSlice";

export const AuthContext = createContext({
  user: null,
  isAuthenticated: false,
  loading: true,
  login: () => {},
  logout: () => {},
  setUser: () => {},
  hasRole: () => false,
  isAdmin: () => false,
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  const [mergeGuestCart] = useMergeGuestCartMutation();

  // Fetch logged-in user on mount
  const fetchProfile = async () => {
    setLoading(true);
    try {
      const res = await axiosInstance.get("auth/users/me/");
      setUser(res.data);
      setIsAuthenticated(true);
    } catch (error) {
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchProfile();
  }, []);

  // Login function
  const login = async (credentials, navigate, location) => {
    setLoading(true);
    try {
      // Authenticate user
      await axiosInstance.post("auth/jwt/create/", credentials);
      await fetchProfile()

      // Merge guest cart if any
      const guestCart = JSON.parse(localStorage.getItem("cart")) || [];
      if (guestCart.length) {
        await mergeGuestCart({ items: guestCart }).unwrap();
        localStorage.removeItem("cart");
      }

      // Redirect
      const redirectTo = location?.state?.from || "/cart";
      navigate(redirectTo);

      return true;
    } catch (error) {
      console.error("Login failed:", error);
      setUser(null);
      setIsAuthenticated(false);
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Logout function
  const logout = async () => {
    setLoading(true);
    try {
      await axiosInstance.post("auth/jwt/logout/");
    } catch (error) {
      console.warn("Logout error", error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      setLoading(false);
    }
  };

  const hasRole = (role) => {
    if (!user) return false;
    if (Array.isArray(user.roles)) return user.roles.includes(role);
    return user.role === role;
  };

  const isAdmin = () => hasRole("admin") || user?.is_staff || user?.is_superuser;

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        loading,
        login,
        logout,
        setUser,
        hasRole,
        isAdmin,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
