import axios from "axios";

const baseURL="https://ecommerce-ml5v.onrender.com/api/"

const csrfClient = axios.create({
  baseURL: baseURL,
  withCredentials: true,
});

export const initCsrf = async () => {
  try {
    await csrfClient.get("auth/csrf/");
    console.log("✅ CSRF cookie initialized");
  } catch (error) {
    console.error("❌ Failed to initialize CSRF:", error);
  }
};
