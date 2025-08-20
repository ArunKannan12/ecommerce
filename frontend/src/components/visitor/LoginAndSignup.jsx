import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import { useNavigate, useLocation } from 'react-router-dom';
import { FaEye, FaEyeSlash } from 'react-icons/fa';
import GoogleAuth from './GoogleAuth';
import FacebookAuth from './FacebookAuth';
import axiosInstance from '../../api/axiosinstance';
import { useAuth } from '../../contexts/authContext';

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
      const redirectFrom = location.state?.from || "/"; // ← preserve the intended page
      const res = await login(loginData, null, redirectFrom); 

     if (res.success) {
        if (!res.data.is_active) {
          toast.info("Your account isn't verified yet. Please check your email.");
          navigate('/verify-email', { state: { email: loginData.email } });
        } else {
          toast.success("Login successful");
          navigate(res.from, { replace: true });
        }
      }
    } catch (err) {
      toast.error("Invalid email or password!");
    } finally {
      setLoading(false);
    }
  };


  /*** SIGNUP FUNCTIONS ***/
  const handleSignupChange = (e) => {
    setSignupData({ ...signupData, [e.target.name]: e.target.value });
    setSignupErrors(prev => ({ ...prev, [e.target.name]: '' }));
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
    <div className="min-h-screen flex justify-center bg-gray-100 px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-xl shadow-lg p-8">
        <h2 className="text-2xl font-bold text-center mb-6 text-gray-800">
          {isLogin ? 'Login' : 'Sign Up'}
        </h2>

        {isLogin ? (
          <form onSubmit={handleLoginSubmit} noValidate className="space-y-4">
            <div>
              <label className="block text-gray-700 mb-1">Email</label>
              <input
                ref={inputFocus}
                type="email"
                name="email"
                value={loginData.email}
                onChange={handleLoginChange}
                placeholder="Enter your email"
                className={`w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  loginErrors.email ? 'border-red-500' : ''
                }`}
              />
              {loginErrors.email && <p className="text-red-500 text-sm mt-1">{loginErrors.email}</p>}
            </div>

            <div className="relative">
              <label className="block text-gray-700 mb-1">Password</label>
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={loginData.password}
                onChange={handleLoginChange}
                placeholder="Enter your password"
                className={`w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  loginErrors.password ? 'border-red-500' : ''
                }`}
              />
              {loginErrors.password && (
                <p className="text-red-500 text-sm mt-1">{loginErrors.password}</p>
              )}
              <span
                onClick={togglePassword}
                className="absolute top-3.5 right-3 text-gray-500 cursor-pointer"
              >
                {showPassword ? <FaEyeSlash /> : <FaEye />}
              </span>
            </div>

            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="rememberMe"
                  checked={rememberMe}
                  onChange={() => setRememberMe(!rememberMe)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="rememberMe" className="ml-2 text-gray-700">
                  Remember Me
                </label>
              </div>
              <div>
                <a href="/forgot-password" className="text-sm text-blue-600 hover:underline">
                  Forgot Password?
                </a>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition font-semibold"
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>

            <div className="flex items-center my-4">
              <hr className="flex-grow border-gray-300" />
              <span className="px-2 text-gray-400">or</span>
              <hr className="flex-grow border-gray-300" />
            </div>

            <div className="flex flex-col space-y-2">
              <GoogleAuth />
              <FacebookAuth />
            </div>
          </form>
        ) : (
          <form onSubmit={handleSignupSubmit} noValidate className="space-y-4">
            {signupErrors.api && (
              <div className="text-red-500 text-sm text-center">{signupErrors.api}</div>
            )}

            <div>
              <label className="block text-gray-700 mb-1">Email</label>
              <input
                type="email"
                name="email"
                value={signupData.email}
                onChange={handleSignupChange}
                placeholder="Enter your email"
                className={`w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-green-500 ${
                  signupErrors.email ? 'border-red-500' : ''
                }`}
              />
              {signupErrors.email && <p className="text-red-500 text-sm mt-1">{signupErrors.email}</p>}
            </div>

            <div>
              <label className="block text-gray-700 mb-1">First Name</label>
              <input
                type="text"
                name="first_name"
                value={signupData.first_name}
                onChange={handleSignupChange}
                placeholder="John"
                className={`w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-green-500 ${
                  signupErrors.first_name ? 'border-red-500' : ''
                }`}
              />
              {signupErrors.first_name && (
                <p className="text-red-500 text-sm mt-1">{signupErrors.first_name}</p>
              )}
            </div>

            <div>
              <label className="block text-gray-700 mb-1">Last Name</label>
              <input
                type="text"
                name="last_name"
                value={signupData.last_name}
                onChange={handleSignupChange}
                placeholder="Doe"
                className={`w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-green-500 ${
                  signupErrors.last_name ? 'border-red-500' : ''
                }`}
              />
              {signupErrors.last_name && (
                <p className="text-red-500 text-sm mt-1">{signupErrors.last_name}</p>
              )}
            </div>

            <div>
              <label className="block text-gray-700 mb-1">Password</label>
              <input
                type="password"
                name="password"
                value={signupData.password}
                onChange={handleSignupChange}
                placeholder="********"
                className={`w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-green-500 ${
                  signupErrors.password ? 'border-red-500' : ''
                }`}
              />
              {signupErrors.password && (
                <p className="text-red-500 text-sm mt-1">{signupErrors.password}</p>
              )}
            </div>

            <div>
              <label className="block text-gray-700 mb-1">Confirm Password</label>
              <input
                type="password"
                name="re_password"
                value={signupData.re_password}
                onChange={handleSignupChange}
                placeholder="********"
                className={`w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-green-500 ${
                  signupErrors.re_password ? 'border-red-500' : ''
                }`}
              />
              {signupErrors.re_password && (
                <p className="text-red-500 text-sm mt-1">{signupErrors.re_password}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition font-semibold"
            >
              {loading ? 'Registering...' : 'Register'}
            </button>
          </form>
        )}

        <div className="text-center mt-4">
          <p className="text-gray-600">
            {isLogin ? "Don't have an account?" : 'Already have an account?'}{' '}
            <span
              onClick={() => setIsLogin(!isLogin)}
              className="text-blue-600 hover:underline cursor-pointer"
            >
              {isLogin ? 'Sign Up' : 'Login'}
            </span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginAndSignup;
