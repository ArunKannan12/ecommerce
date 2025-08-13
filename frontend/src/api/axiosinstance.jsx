import axios from "axios";

const axiosInstance = axios.create({
  baseURL: "http://localhost:8000/api/",
  withCredentials: true,
});

axiosInstance.interceptors.response.use((response)=>
  response,(error)=>{
    if(error.response && error.response.status === 401){
      window.location.href="/login";
    }

    return Promise.reject(error)
  }
)
export default axiosInstance;
