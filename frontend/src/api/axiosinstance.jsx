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
axiosInstance.interceptors.response.use(
  response => response,
  async (error) => {
    const originalRequest = error.config;

    // Only retry once
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url.includes("auth/jwt/refresh/")
    ) {
      originalRequest._retry = true;

      // Only try refresh if user has refresh token (cookie)
      try {
        await axiosInstance.post("auth/jwt/refresh/");
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        console.error("Token refresh failed:", refreshError);
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
