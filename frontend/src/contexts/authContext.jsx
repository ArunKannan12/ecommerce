import { createContext, useContext, useEffect, useState } from "react";
import axiosInstance from "../api/axiosinstance";


export const AuthContext = createContext({
    user:null,
    isAuthenticated:false,
    loading:true,
    login:()=>{},
    logout:()=>{},
    setUser:()=>{}
})

export const AuthProvider =({children})=>{
    const [loading,setLoading] = useState(false)
    const [user,setUser] = useState(null)
    const [isAuthenticated,setIsAuthenticated] = useState(false)

    useEffect(()=>{
        const fetchProfile = async ()=>{
            setLoading(true)
            try {
                const res = await axiosInstance.get("auth/users/me/")
                setUser(res.data)
                setIsAuthenticated(true)
            } catch (error) {
                setUser(null);
                setIsAuthenticated(false);
            } finally {
                setLoading(false);
            }
            };

            fetchProfile();
        }, []);

        const login = async (credentials) => {
            try {
            // POST to your cookie-based login endpoint
            await axiosInstance.post("auth/jwt/create/", credentials);
            // If login successful, fetch user info
            const res = await axiosInstance.get("auth/users/me/");
            setUser(res.data);
            setIsAuthenticated(true);
            setLoading(false);
            return true;
            } catch (error) {
            setUser(null);
            setIsAuthenticated(false);
            setLoading(false);
            return false;
            }
        };

  const logout = async () => {
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

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, loading, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);