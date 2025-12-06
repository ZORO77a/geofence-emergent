import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function OTPVerification() {
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const inputRefs = useRef([]);

  const { username, role } = location.state || {};

  useEffect(() => {
    if (!username || !role) {
      toast.error('Invalid session');
      navigate('/admin/login');
    }
  }, [username, role, navigate]);

  const handleChange = (index, value) => {
    if (value.length > 1) value = value[0];
    if (!/^[0-9]*$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    const otpCode = otp.join('');

    if (otpCode.length !== 6) {
      toast.error('Please enter complete OTP');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/verify-otp`, {
        username,
        otp: otpCode
      });

      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('username', username);
      localStorage.setItem('role', role);

      toast.success('Login successful!');
      
      if (role === 'admin') {
        navigate('/admin/dashboard');
      } else {
        navigate('/employee/dashboard');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container" data-testid="otp-verification-page">
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">🔒</div>
          <h1 className="login-title">Verify OTP</h1>
          <p className="login-subtitle">Enter the code sent to your email</p>
        </div>

        <form onSubmit={handleVerify}>
          <div className="otp-container">
            {otp.map((digit, index) => (
              <input
                key={index}
                ref={(el) => (inputRefs.current[index] = el)}
                type="text"
                maxLength="1"
                className="otp-input"
                value={digit}
                onChange={(e) => handleChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                data-testid={`otp-input-${index}`}
              />
            ))}
          </div>

          <button 
            type="submit" 
            className="submit-btn" 
            disabled={loading}
            data-testid="verify-otp-btn"
          >
            {loading ? 'Verifying...' : 'Verify OTP'}
          </button>
        </form>

        <div className="login-footer">
          <p style={{ color: '#6b7280', fontSize: '14px' }}>OTP expires in 5 minutes</p>
        </div>
      </div>
    </div>
  );
}

export default OTPVerification;
