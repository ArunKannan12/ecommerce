import axios from "axios";
import { getCsrfToken } from "../utils/csrf";

const axiosInstance = axios.create({
  // baseURL:"http://localhost:8000/api/"
  baseURL: "https://ecommerce-ml5v.onrender.com/api",
  withCredentials: true, // ✅ send/receive cookies
  headers: {
    "Content-Type": "application/json",
  },
});

// ⏳ Fetch CSRF cookie before first request if missing
axiosInstance.interceptors.request.use(
  async (config) => {
    let csrfToken = getCsrfToken();

    if (!csrfToken) {
      try {
        // hit backend to set csrftoken cookie
        await axiosInstance.get("auth/csrf/", {
          withCredentials: true,
        });
        csrfToken = getCsrfToken();
      } catch (err) {
        console.error("❌ Failed to fetch CSRF token:", err);
      }
    }

    if (csrfToken) {
      config.headers["X-CSRFToken"] = csrfToken;
    } else {
      console.warn("⚠️ CSRF token still missing");
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// 🔄 Auto-refresh access token on 401
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url.includes("auth/jwt/refresh/")
    ) {
      originalRequest._retry = true;

      try {
        await axiosInstance.post("auth/jwt/refresh/");
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        console.error("🔒 Token refresh failed:", refreshError);
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
