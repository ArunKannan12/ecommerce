import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import { useNavigate, useLocation } from 'react-router-dom';
import { FaEnvelope, FaEye, FaEyeSlash, FaLock,FaUser } from 'react-icons/fa';
import GoogleAuth from './GoogleAuth';
import FacebookAuth from './FacebookAuth';
import axiosInstance from '../../api/axiosinstance';
import { useAuth } from '../../contexts/authContext';
import { AnimatePresence, motion } from 'framer-motion';
import Beston from '../../../Beston.png'
import Lottie from "lottie-react";
import ShoppingCart from '../../../ShoppingCart.json'

const LoginAndSignup = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();

  // Toggle between login/signup
  const [isLogin, setIsLogin] = useState(true);

  /*** COMMON STATES ***/
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const inputFocus = useRef(null);

  /*** LOGIN STATES ***/
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [loginErrors, setLoginErrors] = useState({});
  const [rememberMe, setRememberMe] = useState(false);

  /*** SIGNUP STATES ***/
  const [signupData, setSignupData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    re_password: '',
  });
  const [signupErrors, setSignupErrors] = useState({});

  

  /*** COMMON FUNCTIONS ***/
  const togglePassword = () => setShowPassword(prev => !prev);

  /*** LOGIN FUNCTIONS ***/
  const handleLoginChange = (e) => {
    setLoginData({ ...loginData, [e.target.name]: e.target.value });
    setLoginErrors(prev => ({ ...prev, [e.target.name]: '' }));
  };

  const validateLogin = () => {
    const errors = {};
    if (!loginData.email.trim()) errors.email = 'Email is required';
    if (!loginData.password.trim()) errors.password = 'Password is required';
    return errors;
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();

    const errors = validateLogin();
    if (Object.keys(errors).length > 0) {
      setLoginErrors(errors);
      return;
    }

    try {
        setLoading(true);
        const redirectFrom = location.state?.from || "/"; 
        const res = await login(loginData, null, redirectFrom); 
        console.log("res", res);

        if (res.success) {
          toast.success("Login successful");
          navigate(res.from, { replace: true });
        } else if (res.reason === "unverified") {
          // Only go to verify page if truly unverified
          navigate("/verify-email", { state: { email: res.email } });
        } else if (res.reason === "inactive") {
          toast.info("Your account is inactive. Contact support.");
        }
  } catch (err) {
      console.log('eer',err);
      
      const backendMessage =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "❌ Login failed. Please check your credentials.";

      toast.error(backendMessage);
    } finally {
      setLoading(false);
    }
  };


  /*** SIGNUP FUNCTIONS ***/
  const handleSignupChange = (e) => {
    const { name, value } = e.target;
    setSignupData((prev) => ({ ...prev, [name]: value }));

    // Re-validate this specific field live
    setSignupErrors((prev) => {
      const newErrors = { ...prev };
      if (name === "email") {
        if (!value) newErrors.email = "Email is required";
        else if (!/\S+@\S+\.\S+/.test(value)) newErrors.email = "Invalid email format";
        else delete newErrors.email;
      }
      if (name === "first_name") {
        if (!value) newErrors.first_name = "First name is required";
        else delete newErrors.first_name;
      }
      if (name === "last_name") {
        if (!value) newErrors.last_name = "Last name is required";
        else delete newErrors.last_name;
      }
      if (name === "password") {
        if (!value) newErrors.password = "Password is required";
        else if (!/^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/.test(value)) {
          newErrors.password = "Must be 8+ chars, 1 letter & 1 number";
        } else delete newErrors.password;
      }
      if (name === "re_password") {
        if (!value) newErrors.re_password = "Confirm your password";
        else if (value !== signupData.password) {
          newErrors.re_password = "Passwords do not match";
        } else delete newErrors.re_password;
      }
      return newErrors;
    });
  };


  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;

  const validateSignup = () => {
    const errors = {};
    const { email, first_name, last_name, password, re_password } = signupData;

    if (!email.trim()) errors.email = 'Email is required';
    else if (!emailRegex.test(email)) errors.email = 'Invalid email format';

    if (!first_name.trim()) errors.first_name = 'First name is required';
    if (!last_name.trim()) errors.last_name = 'Last name is required';

    if (!password.trim()) errors.password = 'Password is required';
    else if (!passwordRegex.test(password))
      errors.password = 'Password must be at least 8 characters, include uppercase, lowercase, number, and special character.';

    if (!re_password.trim()) errors.re_password = 'Confirm password is required';
    else if (password !== re_password) errors.re_password = 'Passwords do not match';

    return errors;
  };

  const handleSignupSubmit = async (e) => {
    e.preventDefault();
    const errors = validateSignup();
    if (Object.keys(errors).length > 0) {
      setSignupErrors(errors);
      return;
    }

    try {
      setLoading(true);
      const res = await axiosInstance.post('auth/users/', signupData);
      if (res.status === 201) {
        toast.success('Registration successful! Please check your email to verify.');
        setSignupErrors({});
        setTimeout(() => {
          const from = location.state?.from || '/';
          navigate('/verify-email', { state: { email: signupData.email, from } });
        }, 200);
      }
    } catch (err) {
      if (err.response?.data) {
        const apiErrors = {};
        for (const key in err.response.data) {
          apiErrors[key] = Array.isArray(err.response.data[key])
            ? err.response.data[key][0]
            : err.response.data[key];
        }
        setSignupErrors(apiErrors);
      } else {
        setSignupErrors({ api: 'Registration failed. Please try again later.' });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (location.state?.mode) {
      setIsLogin(location.state.mode === 'login' ? true : false);
      navigate('/login', { replace: true, state: {} }); // Clear mode from history
    }
  }, []);

  useEffect(() => {
    inputFocus.current?.focus();

    if (location.state?.mode) {
      setIsLogin(location.state.mode === 'login');
      navigate('/login', { replace: true, state: {} }); // Clear mode from history
    }

    if (isAuthenticated) {
      const from = location.state?.from || '/';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location.state]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100 grid grid-cols-1 lg:grid-cols-2">
      {/* Left Section */}
      <div className="hidden lg:flex items-center justify-center bg-gradient-to-tr from-indigo-500 to-blue-600 text-white p-12">
        <div className="max-w-md text-center space-y-6">
          <Lottie
            animationData={ShoppingCart}
            loop={true}
            className="w-80 mx-auto"
          />
          <h1 className="text-4xl font-extrabold">Welcome to Beston Connect</h1>
          <p className="text-lg opacity-90">Shop smarter. Live better.</p>
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center justify-center px-4 py-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="w-full max-w-md sm:max-w-lg md:max-w-xl bg-white/90 backdrop-blur-2xl rounded-3xl shadow-2xl border border-gray-200 p-6 sm:p-8 overflow-y-auto"
          style={{ maxHeight: "calc(100vh - 3rem)" }}
        >
          {/* Title */}
          <h2 className="text-3xl font-extrabold text-center text-gray-900 mb-2">
            {isLogin ? "Welcome Back 👋" : "Create Account 🚀"}
          </h2>
          <p className="text-center text-gray-500 mb-6">
            {isLogin
              ? "Login to continue shopping"
              : "Join us and start shopping today"}
          </p>

          {/* Forms */}
          <AnimatePresence mode="wait">
            {isLogin ? (
              <motion.form
                key="login"
                onSubmit={handleLoginSubmit}
                initial={{ x: 50, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -50, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="space-y-4"
              >
                {/* Email */}
                <div className="relative">
                  <FaEnvelope className="absolute left-3 top-3 text-gray-400" />
                  <input
                    ref={inputFocus}
                    type="email"
                    name="email"
                    value={loginData.email}
                    onChange={handleLoginChange}
                    placeholder="Email"
                    className={`w-full pl-10 pr-3 py-2 border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      loginErrors.email
                        ? "border-red-500"
                        : "border-gray-300"
                    }`}
                  />
                  {loginErrors.email && (
                    <p className="text-sm text-red-500 mt-1">
                      {loginErrors.email}
                    </p>
                  )}
                </div>

                {/* Password */}
                <div className="relative">
                  <FaLock className="absolute left-3 top-3 text-gray-400" />
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={loginData.password}
                    onChange={handleLoginChange}
                    placeholder="Password"
                    className={`w-full pl-10 pr-10 py-2 border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      loginErrors.password
                        ? "border-red-500"
                        : "border-gray-300"
                    }`}
                  />
                  <span
                    onClick={togglePassword}
                    className="absolute right-3 top-3 text-gray-500 cursor-pointer"
                  >
                    {showPassword ? <FaEyeSlash /> : <FaEye />}
                  </span>
                  {loginErrors.password && (
                    <p className="text-sm text-red-500 mt-1">
                      {loginErrors.password}
                    </p>
                  )}
                </div>

                {/* Remember Me / Forgot Password */}
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={() => setRememberMe(!rememberMe)}
                      className="accent-blue-600"
                    />
                    Remember Me
                  </label>
                  <a
                    href="/forgot-password"
                    className="text-blue-600 hover:underline font-medium"
                  >
                    Forgot Password?
                  </a>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-2 rounded-xl font-semibold shadow hover:opacity-90 transition"
                >
                  {loading ? "Logging in..." : "Login"}
                </button>
              </motion.form>
            ) : (
              <motion.form
                key="signup"
                onSubmit={handleSignupSubmit}
                initial={{ x: 50, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -50, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="space-y-4"
              >
                {/* Email */}
                <div className="relative">
                  <FaEnvelope className="absolute left-3 top-3 text-gray-400" />
                  <input
                    type="email"
                    name="email"
                    value={signupData.email}
                    onChange={handleSignupChange}
                    placeholder="Email"
                    className={`w-full pl-10 pr-3 py-2 border rounded-lg shadow-sm focus:ring-2 focus:ring-green-500 ${
                      signupErrors.email
                        ? "border-red-500"
                        : "border-gray-300"
                    }`}
                  />
                  {signupErrors.email && (
                    <p className="text-sm text-red-500 mt-1">
                      {signupErrors.email}
                    </p>
                  )}
                </div>

                {/* First & Last Name */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {["first_name", "last_name"].map((field) => (
                    <div key={field} className="relative">
                      <FaUser className="absolute left-3 top-3 text-gray-400" />
                      <input
                        type="text"
                        name={field}
                        value={signupData[field]}
                        onChange={handleSignupChange}
                        placeholder={
                          field === "first_name"
                            ? "First Name"
                            : "Last Name"
                        }
                        className={`w-full pl-10 py-2 border rounded-lg shadow-sm focus:ring-2 focus:ring-green-500 ${
                          signupErrors[field]
                            ? "border-red-500"
                            : "border-gray-300"
                        }`}
                      />
                      {signupErrors[field] && (
                        <p className="text-sm text-red-500 mt-1">
                          {signupErrors[field]}
                        </p>
                      )}
                    </div>
                  ))}
                </div>

                {/* Password */}
                <div className="relative">
                  <FaLock className="absolute left-3 top-3 text-gray-400" />
                  <input
                    type="password"
                    name="password"
                    value={signupData.password}
                    onChange={handleSignupChange}
                    placeholder="Password"
                    className={`w-full pl-10 py-2 border rounded-lg shadow-sm focus:ring-2 focus:ring-green-500 ${
                      signupErrors.password
                        ? "border-red-500"
                        : "border-gray-300"
                    }`}
                  />
                  {signupErrors.password && (
                    <p className="text-sm text-red-500 mt-1">
                      {signupErrors.password}
                    </p>
                  )}
                </div>

                {/* Confirm Password */}
                <div className="relative">
                  <FaLock className="absolute left-3 top-3 text-gray-400" />
                  <input
                    type="password"
                    name="re_password"
                    value={signupData.re_password}
                    onChange={handleSignupChange}
                    placeholder="Confirm Password"
                    className={`w-full pl-10 py-2 border rounded-lg shadow-sm focus:ring-2 focus:ring-green-500 ${
                      signupErrors.re_password
                        ? "border-red-500"
                        : "border-gray-300"
                    }`}
                  />
                  {signupErrors.re_password && (
                    <p className="text-sm text-red-500 mt-1">
                      {signupErrors.re_password}
                    </p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white py-2 rounded-xl font-semibold shadow hover:opacity-90 transition"
                >
                  {loading ? "Registering..." : "Register"}
                </button>
              </motion.form>
            )}
          </AnimatePresence>

          {/* Divider */}
          <div className="flex items-center my-5">
            <hr className="flex-grow border-gray-300" />
            <span className="px-3 text-gray-400 text-sm">
              or continue with
            </span>
            <hr className="flex-grow border-gray-300" />
          </div>

          {/* Google Auth */}
          <div className="flex justify-center w-full px-4 sm:px-0">
            <div className="w-full max-w-sm">
              <GoogleAuth />
            </div>
          </div>

          {/* Toggle Login/Signup */}
          <p className="text-center text-gray-600 mt-6">
            {isLogin
              ? "Don’t have an account?"
              : "Already have an account?"}{" "}
            <span
              onClick={() => setIsLogin(!isLogin)}
              className="text-blue-600 font-semibold cursor-pointer hover:underline"
            >
              {isLogin ? "Sign Up" : "Login"}
            </span>
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default LoginAndSignup;
