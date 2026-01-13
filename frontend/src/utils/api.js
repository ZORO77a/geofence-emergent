/**
 * Secure API client with httpOnly cookie support
 * Handles authentication tokens via httpOnly cookies (recommended for production)
 * Falls back to localStorage tokens for backward compatibility (development only)
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

/**
 * Parse JWT token to extract payload
 */
function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    console.error('Error parsing JWT:', e);
    return null;
  }
}

/**
 * Check if token is expired
 */
function isTokenExpired(token) {
  if (!token) return true;
  const payload = parseJwt(token);
  if (!payload || !payload.exp) return true;
  return payload.exp * 1000 < Date.now();
}

/**
 * Get access token from cookies (preferred) or localStorage (fallback)
 */
function getAccessToken() {
  // Try cookie first (production)
  const cookieValue = document.cookie
    .split('; ')
    .find(row => row.startsWith('access_token='));
  
  if (cookieValue) {
    return cookieValue.split('=')[1];
  }

  // Fallback to localStorage (development)
  return localStorage.getItem('token');
}

/**
 * Get refresh token from cookies (preferred) or localStorage (fallback)
 */
function getRefreshToken() {
  // Try cookie first (production)
  const cookieValue = document.cookie
    .split('; ')
    .find(row => row.startsWith('refresh_token='));
  
  if (cookieValue) {
    return cookieValue.split('=')[1];
  }

  // Fallback to localStorage (development)
  return localStorage.getItem('refresh_token');
}

/**
 * Store tokens in both cookies (automatic via Set-Cookie) and localStorage (backward compat)
 */
function storeTokens(accessToken, refreshToken) {
  // Store in localStorage for backward compatibility
  if (accessToken) {
    localStorage.setItem('token', accessToken);
  }
  if (refreshToken) {
    localStorage.setItem('refresh_token', refreshToken);
  }
  // Note: httpOnly cookies are set automatically by server via Set-Cookie header
}

/**
 * Clear all tokens (cookies + localStorage)
 */
function clearTokens() {
  // Clear localStorage
  localStorage.removeItem('token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('username');
  localStorage.removeItem('role');

  // Clear cookies (by setting max-age to 0)
  document.cookie = 'access_token=; max-age=0; path=/';
  document.cookie = 'refresh_token=; max-age=0; path=/';
}

/**
 * Refresh access token using refresh token
 */
async function refreshAccessToken() {
  const refreshToken = getRefreshToken();
  
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh-token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
      credentials: 'include', // Include cookies
    });

    if (!response.ok) {
      if (response.status === 401) {
        clearTokens();
        throw new Error('Refresh token expired. Please login again.');
      }
      throw new Error('Failed to refresh token');
    }

    const data = await response.json();
    storeTokens(data.access_token, refreshToken);
    return data.access_token;
  } catch (error) {
    clearTokens();
    throw error;
  }
}

/**
 * Make API request with automatic token refresh and error handling
 */
async function apiRequest(endpoint, options = {}) {
  let accessToken = getAccessToken();

  // Check if token is expired and refresh if needed
  if (isTokenExpired(accessToken)) {
    try {
      accessToken = await refreshAccessToken();
    } catch (error) {
      // Refresh failed, redirect to login
      window.location.href = '/login';
      throw error;
    }
  }

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add authorization header if we have a token
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  // Get CSRF token if it exists (for state-changing requests)
  const csrfToken = localStorage.getItem('csrf_token');
  if (csrfToken && ['POST', 'PUT', 'DELETE'].includes(options.method || 'GET')) {
    headers['X-CSRF-Token'] = csrfToken;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include', // Include cookies
  });

  // Handle 401 (token invalid/expired)
  if (response.status === 401) {
    clearTokens();
    window.location.href = '/login';
    throw new Error('Authentication failed. Please login again.');
  }

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'API request failed');
  }

  return response.json();
}

/**
 * Login with credentials and OTP
 */
async function login(username, password) {
  const loginResponse = await apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });

  return loginResponse;
}

/**
 * Verify OTP and get access token
 */
async function verifyOTP(username, otp) {
  const response = await apiRequest('/auth/verify-otp', {
    method: 'POST',
    body: JSON.stringify({ username, otp }),
  });

  // Store tokens
  if (response.access_token) {
    storeTokens(response.access_token, response.refresh_token);
  }

  // Store user info
  localStorage.setItem('username', response.username);
  localStorage.setItem('role', response.role);

  // Get CSRF token
  try {
    const csrfResponse = await apiRequest('/auth/csrf-token', { method: 'POST' });
    localStorage.setItem('csrf_token', csrfResponse.csrf_token);
  } catch (error) {
    console.warn('Failed to fetch CSRF token:', error);
  }

  return response;
}

/**
 * Logout and invalidate token
 */
async function logout() {
  try {
    await apiRequest('/auth/logout', {
      method: 'POST',
    });
  } catch (error) {
    console.warn('Logout API call failed (may be already logged out):', error);
  } finally {
    clearTokens();
    window.location.href = '/login';
  }
}

/**
 * Get CSRF token for state-changing requests
 */
async function getCSRFToken() {
  try {
    const response = await apiRequest('/auth/csrf-token', {
      method: 'POST',
    });
    localStorage.setItem('csrf_token', response.csrf_token);
    return response.csrf_token;
  } catch (error) {
    console.error('Failed to get CSRF token:', error);
    throw error;
  }
}

/**
 * Request password reset email
 */
async function requestPasswordReset(email) {
  return apiRequest('/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

/**
 * Reset password with token
 */
async function resetPassword(token, newPassword) {
  return apiRequest('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

/**
 * Change password for authenticated user
 */
async function changePassword(oldPassword, newPassword) {
  return apiRequest('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
  });
}

export {
  apiRequest,
  getAccessToken,
  getRefreshToken,
  storeTokens,
  clearTokens,
  isTokenExpired,
  parseJwt,
  login,
  verifyOTP,
  logout,
  getCSRFToken,
  requestPasswordReset,
  resetPassword,
  changePassword,
  refreshAccessToken,
};
