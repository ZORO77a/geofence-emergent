import React from 'react';
import { useNavigate } from 'react-router-dom';

function LoginChoice() {
  const navigate = useNavigate();

  return (
    <div className="login-container" data-testid="login-choice-page">
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">G</div>
          <h1 className="login-title">Sign In</h1>
          <p className="login-subtitle">Choose Admin or Employee access</p>
        </div>

        <div className="login-choice">
          <button
            className="submit-btn"
            onClick={() => navigate('/admin/login')}
            data-testid="choose-admin-btn"
          >
            Admin Login
          </button>

          <button
            className="submit-btn"
            onClick={() => navigate('/employee/login')}
            data-testid="choose-employee-btn"
            style={{ marginTop: '0.5rem' }}
          >
            Employee Login
          </button>
        </div>

        <div className="login-footer">
          <small>Need help? Contact the system administrator.</small>
        </div>
      </div>
    </div>
  );
}

export default LoginChoice;
