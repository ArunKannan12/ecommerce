import { createContext, useContext, useState, useEffect } from "react";
import axiosInstance from "../api/axiosinstance";
import { useMergeGuestCartMutation } from "./cartSlice";
import { syncGuestcart } from "../utils/syncGuestCart";
import { toast } from "react-toastify";

// Create context
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

// CSRF setup
const ensureCsrfCookie = async () => {
  try {
    await axiosInstance.get("auth/csrf/");
  } catch (err) {
    console.error("CSRF cookie setup failed:", err);
  }
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [mergeGuestCart] = useMergeGuestCartMutation();

  // ✅ Fetch logged-in user
  const fetchProfile = async () => {
    setLoading(true);
    try {
      const res = await axiosInstance.get("auth/users/me/");
      setUser(res.data);
      console.log('data from context',res.data);
      
      setIsAuthenticated(true);
      return res.data;
    } catch (error) {
      setUser(null);
      setIsAuthenticated(false);
      return null;
    } finally {
      setLoading(false);
    }
  };

  // ✅ Initial load: setup CSRF + fetch user
  useEffect(() => {
    ensureCsrfCookie().then(fetchProfile);
  }, []);

  // ✅ Login (email/password or OAuth)
  const login = async (credentials = null, tokenData = null, redirectFrom = "/") => {
    setLoading(true);
    try {
      await ensureCsrfCookie();

      if (credentials) {
        await axiosInstance.post("auth/jwt/create/", credentials);
      }

      const user = await fetchProfile();

      if (!user?.is_active || !user?.is_verified) {
        toast.info("Your account isn't verified yet. Please check your email.");
        setUser(null);
        setIsAuthenticated(false);
        return {
          success: false,
          reason: "unverified",
          email: credentials?.email,
        };
      }

      // ✅ Merge guest cart (Buy Now + regular)
      const buyNowMinimal = JSON.parse(sessionStorage.getItem("buyNowMinimal") || "null");
      if (buyNowMinimal) {
        const itemsToMerge = Array.isArray(buyNowMinimal) ? buyNowMinimal : [buyNowMinimal];
        await syncGuestcart(mergeGuestCart, itemsToMerge);
      }

      const guestCart = JSON.parse(localStorage.getItem("cart") || "[]");
      if (guestCart.length > 0) {
        await syncGuestcart(mergeGuestCart, guestCart);
      }

      setIsAuthenticated(true);
      return { success: true, from: redirectFrom };
    } catch (err) {
      console.error("Login failed", err);

      const backendMessage =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "❌ Login failed. Please check your credentials.";

      toast.error(backendMessage);
      setUser(null);
      setIsAuthenticated(false);
      return { success: false, error: err };
    } finally {
      setLoading(false);
    }
  };

  // ✅ Logout
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

  // ✅ Role-based access
  const hasRole = (role) => {
    if (!user) return false;
    if (Array.isArray(user.roles)) return user.roles.includes(role);
    return user.role === role;
  };

  const isAdmin = () =>
    hasRole("admin") || user?.is_staff || user?.is_superuser;

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