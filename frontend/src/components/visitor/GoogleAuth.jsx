import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { toast } from 'react-toastify';
import { useLocation, useNavigate } from 'react-router-dom';
import axiosInstance from '../../api/axiosinstance';
import { useAuth } from '../../contexts/AuthContext';

const GoogleAuth = () => {
  const navigate = useNavigate();
  const location = useLocation()
  const { login } = useAuth(); // ✅ use the login function from context

  const handleGoogleLogin = async (credentialResponse) => {
    try {
      // Send the Google ID token to backend
      await axiosInstance.post(
        'auth/social/google/',
        { id_token: credentialResponse.credential },
        { withCredentials: true } // important for HttpOnly cookies
      );
      
      // Use context login to fetch user profile
      const { success } = await login();
      
      if (success) {
        toast.success('Logged in with Google!');
        const from = location.state?.from || '/';
        navigate(from, { replace: true }); // redirect after successful login
      } else {
        toast.error('Failed to fetch user after Google login');
      }
    } catch (error) {
      console.error(error);
      toast.error(error.response?.data?.error || 'Google login failed');
    }
  };

  return (
    <div className="d-flex justify-content-center w-100 mb-3">
      <div style={{ width: '100%', maxWidth: '350px' }}>
        <GoogleLogin
          onSuccess={handleGoogleLogin}
          onError={() => toast.error('Google sign-in failed')}
        />
      </div>
    </div>
  );
};

export default GoogleAuth;
