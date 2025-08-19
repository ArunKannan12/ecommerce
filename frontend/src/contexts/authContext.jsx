import { createContext, useContext, useState, useEffect } from "react";
import axiosInstance from "../api/axiosinstance";
import { useMergeGuestCartMutation } from "./cartSlice";
import { syncGuestcart } from "../utils/syncGuestCart";

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

  // ✅ Fetch logged-in user
  const fetchProfile = async () => {
    setLoading(true);
    try {
      const res = await axiosInstance.get("auth/users/me/", {
        withCredentials: true, // 👈 important for cookies
      });
      console.log(res.data)
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

  // ✅ Login (email/password or OAuth)
const login = async (credentials = null, tokenData = null, redirectFrom = "/") => {
  setLoading(true);
  try {
    // 1️⃣ Create JWT if credentials provided
    if (credentials) {
      await axiosInstance.post("auth/jwt/create/", credentials, {
        withCredentials: true,
      });
    }

    // 2️⃣ Fetch user profile
    await fetchProfile();

    // 3️⃣ Merge guest Buy Now item (if any)
    const buyNowMinimal = JSON.parse(sessionStorage.getItem("buyNowMinimal") || "null");
    if (buyNowMinimal) {
      // Ensure payload is an array
      const itemsToMerge = Array.isArray(buyNowMinimal) ? buyNowMinimal : [buyNowMinimal];
      console.log("[CartMerge] Merging guest Buy Now item:", itemsToMerge);
      await syncGuestcart(mergeGuestCart, itemsToMerge);
      
    }

    // 4️⃣ Merge guest cart items (if any)
    const guestCart = JSON.parse(localStorage.getItem("cart") || "[]");
    if (guestCart.length > 0) {
      console.log("[CartMerge] Merging guest cart items:", guestCart);
      await syncGuestcart(mergeGuestCart, guestCart);
     
    }

    // 5️⃣ Mark as authenticated
    setIsAuthenticated(true);

    // 6️⃣ Return success + redirect info
    return { success: true, from: redirectFrom };
  } catch (err) {
    console.error("Login failed", err);
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
      await axiosInstance.post("auth/jwt/logout/", {}, { withCredentials: true });
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
