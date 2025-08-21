import axios from "axios";
import { getCsrfToken } from "../utils/csrf";

const axiosInstance = axios.create({
  // baseURL: "http://localhost:8000/api/",
  baseURL:"https://ecommerce-ml5v.onrender.com/api",

  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": getCsrfToken(),
  },
});

// Response interceptor
axiosInstance.interceptors.request.use(config => {
  const csrfToken = getCsrfToken(); // reads from document.cookie
  if (csrfToken) {
    config.headers["X-CSRFToken"] = csrfToken;
  } else {
    console.warn("⚠️ CSRF token not found in cookies");
  }
  return config;
});

// 🔄 Auto-refresh access token on 401
axiosInstance.interceptors.response.use(
  response => response,
  async error => {
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
