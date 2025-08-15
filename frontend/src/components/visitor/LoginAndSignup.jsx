import React, { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { toast } from 'react-toastify'
import axiosInstance from '../../api/axiosinstance';
import { syncGuestcart } from '../../utils/syncGuestCart';
import { useNavigate, useLocation } from 'react-router-dom';


const LoginAndSignup = () => {
  const {login} = useAuth();
  const [isLogin,setIsLogin] = useState(true)
  const [formData,setFormData] = useState({
    first_name:'',
    last_name:'',
    email:'',
    password:'',
    re_password:''
  })
  const navigate = useNavigate();
  const location = useLocation();
  const {first_name,last_name,email,password,re_password} = formData

  const handleChange = (e)=>{
    setFormData((prev)=>({...prev,[e.target.name]: e.target.value}))
  }

  const handleLoginSubmit = async (e)=>{
      e.preventDefault();

      if (!email || !password) {
        toast.error("Please enter your email and password")
        return
      }

      const success = await login({
        email:email,
        password:password
      },navigate,location)
      if(success){
        toast.success("Logged in successfully")
        
      }else{
        toast.error("login failed")
      }
  }

  const handleSignupSubmit = async(e)=>{
        e.preventDefault();
        if (!first_name || !last_name || !email || !password || !re_password) {
          toast.error("Please fill all fields")
          return 
        }
        if (password !== re_password) {
          toast.error("Password does not match")
          return
        }

         try {
          const res = await axiosInstance.post("auth/users/", {
              first_name: formData.first_name,
              last_name: formData.last_name,
              email: formData.email,
              password: formData.password,
          });

          if (res.status === 201) {
            toast.success("Signup successful! Please check your email for activation.");
            const success = await login({ email, password }, navigate, location);
           
            setIsLogin(true);
            toast.success("Account created and logged in!");
          }
        } catch (error) {
          const data = error.response?.data;
          if (data) {
            // Example: data might be { email: ["A user with that email already exists."] }
            const messages = Object.values(data).flat().join(" ");
            toast.error("Signup failed: " + messages);
          } else {
            toast.error("Signup failed. Please try again later.");
          }
          }
  };
  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded shadow">
      <h1 className="text-3xl font-bold mb-6">{isLogin ? "Login" : "Signup"}</h1>

      {isLogin ? (
        <form onSubmit={handleLoginSubmit} className="space-y-4">
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={email}
            onChange={handleChange}
            className="w-full border px-3 py-2 rounded"
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={password}
            onChange={handleChange}
            className="w-full border px-3 py-2 rounded"
          />
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
          >
            Login
          </button>
        </form>
      ) : (
        <form onSubmit={handleSignupSubmit} className="space-y-4">
          <input
            type="text"
            name="first_name"
            placeholder="First Name"
            value={first_name}
            onChange={handleChange}
            className="w-full border px-3 py-2 rounded"
          />
          <input
            type="text"
            name="last_name"
            placeholder="Last Name"
            value={last_name}
            onChange={handleChange}
            className="w-full border px-3 py-2 rounded"
          />
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={email}
            onChange={handleChange}
            className="w-full border px-3 py-2 rounded"
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={password}
            onChange={handleChange}
            className="w-full border px-3 py-2 rounded"
          />
          <input
            type="password"
            name="re_password"
            placeholder="Confirm Password"
            value={re_password}
            onChange={handleChange}
            className="w-full border px-3 py-2 rounded"
          />
          <button
            type="submit"
            className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700"
          >
            Signup
          </button>
        </form>
      )}

      <p className="mt-4 text-center text-gray-600">
        {isLogin ? "Don't have an account?" : "Already have an account?"}{" "}
        <button
          className="text-blue-600 hover:underline"
          onClick={() => setIsLogin(!isLogin)}
        >
          {isLogin ? "Signup" : "Login"}
        </button>
      </p>
    </div>
  )
}

export default LoginAndSignup