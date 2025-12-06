# GeoCrypt - Geofencing Based Access Control System
## Complete Tutorial & Documentation

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Setup Guide](#setup-guide)
5. [Feature Documentation](#feature-documentation)
6. [API Reference](#api-reference)
7. [Code Explanation](#code-explanation)
8. [Testing Guide](#testing-guide)
9. [Deployment](#deployment)
10. [Troubleshooting](#troubleshooting)

---

## Project Overview

GeoCrypt is a comprehensive geofencing-based access control system for encrypted files. It ensures that employees can only access company files when they meet specific security conditions:

- **Location-based access**: Employee must be within specified geographical boundaries
- **WiFi-based access**: Employee must be connected to authorized WiFi network
- **Time-based access**: Access only during working hours (configurable)
- **Work from home**: Admin can approve exceptions for remote work
- **Post-quantum encryption**: Files are encrypted using AES-256 (quantum-resistant)
- **ML-based monitoring**: AI detects suspicious access patterns

---

## System Architecture

```
┌─────────────────┐
│   React UI      │
│  (Frontend)     │
└────────┬────────┘
         │
         │ HTTPS/REST API
         │
┌────────▼────────┐
│   FastAPI       │
│  (Backend)      │
├─────────────────┤
│ • Auth Service  │
│ • Crypto Service│
│ • Geofence      │
│ • ML Service    │
│ • Email Service │
└────────┬────────┘
         │
┌────────▼────────┐
│   MongoDB       │
│  + GridFS       │
│  (Database)     │
└─────────────────┘
```

---

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Motor**: Async MongoDB driver
- **GridFS**: File storage system for MongoDB
- **PyCryptodome**: Cryptography library (AES-256)
- **scikit-learn**: Machine learning for anomaly detection
- **aiosmtplib**: Async email sending
- **Jose**: JWT token handling
- **Passlib**: Password hashing

### Frontend
- **React 19**: UI library
- **React Router**: Navigation
- **Axios**: HTTP client
- **Sonner**: Toast notifications
- **Lucide React**: Icons
- **Tailwind CSS**: Styling

### Database
- **MongoDB**: Document database
- **GridFS**: Binary file storage

---

## Setup Guide

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB (running on localhost:27017)
- Gmail account with App Password

### Backend Setup

#### 1. Navigate to backend directory
```bash
cd /app/backend
```

#### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

#### 3. Configure environment variables
Edit `/app/backend/.env`:
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="geocrypt_db"
CORS_ORIGINS="*"
SECRET_KEY="your-secret-key-change-in-production"
GMAIL_USER="your-email@gmail.com"
GMAIL_APP_PASSWORD="your-app-password"
```

**Getting Gmail App Password:**
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to https://myaccount.google.com/apppasswords
4. Generate app password for "Mail"
5. Copy the 16-character password

#### 4. Start backend server
```bash
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup

#### 1. Navigate to frontend directory
```bash
cd /app/frontend
```

#### 2. Install dependencies
```bash
yarn install
```

#### 3. Configure environment
Edit `/app/frontend/.env`:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

#### 4. Start frontend
```bash
yarn start
```

The application will be available at `http://localhost:3000`

---

## Feature Documentation

### 1. Authentication System

#### Admin Login
- **Default Credentials**: 
  - Username: `admin`
  - Password: `admin`
  - Email: `ananthakrishnan272004@gmail.com`

#### Employee Login
- Credentials created by admin
- First-time login uses admin-provided password

#### Two-Factor Authentication (OTP)
1. User enters username/password
2. System generates 6-digit OTP
3. OTP sent to user's email via Gmail SMTP
4. User enters OTP within 5 minutes
5. System validates and issues JWT token

**Implementation:**
- File: `/app/backend/auth.py`
- OTP Generation: Random 6-digit number
- OTP Storage: MongoDB with expiry timestamp
- Email: `/app/backend/email_service.py`

### 2. Admin Dashboard Features

#### Employee Management
- **Create Employee**: Add new employees with email and password
- **View Employees**: List all employees with status
- **Delete Employee**: Remove employee accounts
- **Update Employee**: Modify employee credentials

**Location:** `/app/frontend/src/pages/AdminDashboard.jsx`

#### File Management
- **Upload Files**: Drag-and-drop or click to upload
- **Encryption**: Automatic post-quantum encryption on upload
- **View Files**: List all uploaded files with metadata
- **GridFS Storage**: Files stored in MongoDB GridFS

**Backend Implementation:**
- File: `/app/backend/server.py` - `upload_file()` endpoint
- Crypto: `/app/backend/crypto_service.py`

#### Access Log Monitoring
- View all file access attempts
- Filter by success/failure
- See location, WiFi, and time data
- Identify denied access reasons

#### Work From Home Request Management
- View pending WFH requests
- Approve/Reject requests
- Add admin comments
- Track approval history

#### Geofence Configuration
- Set office location (latitude, longitude)
- Define geofence radius (meters)
- Specify allowed WiFi SSID
- Configure working hours (start/end time)

**Configuration Storage:** MongoDB `geofence_config` collection

#### Analytics & AI Monitoring
- View employee access patterns
- ML-based anomaly detection
- Risk level assessment (low/medium/high)
- Suspicious activity alerts

**ML Implementation:** `/app/backend/ml_service.py`
- Algorithm: Isolation Forest
- Features: Hour of day, day of week, access frequency
- Training: Minimum 10 data points required

### 3. Employee Dashboard Features

#### Location Detection
- Uses browser Geolocation API
- Automatic location detection on page load
- Manual refresh option
- Displays current coordinates

**Implementation:** `navigator.geolocation.getCurrentPosition()`

#### WiFi SSID Input
- Manual entry (browser cannot auto-detect)
- Required for file access
- Validated against admin-configured SSID

#### File Access System
**Three Validation Checks:**

1. **Location Validation**
   - Calculates distance from office using Haversine formula
   - Must be within configured radius
   - File: `/app/backend/geofence.py`

2. **WiFi Validation**
   - Compares employee's SSID with allowed SSID
   - Case-insensitive matching

3. **Time Validation**
   - Checks current time against working hours
   - Configurable by admin (default: 9 AM - 5 PM)

**Access Flow:**
```
Employee clicks file → System validates 3 conditions
├─ If WFH approved → Grant access (bypass checks)
├─ If all 3 pass → Decrypt & download file
└─ If any fail → Deny access & log reason
```

#### Work From Home Request
- Submit request with reason
- Track request status (pending/approved/rejected)
- When approved: Access files without restrictions

### 4. File Encryption System

#### Encryption Process
1. Admin uploads file
2. System generates random 256-bit key
3. File encrypted using AES-256-GCM
4. Encrypted file stored in GridFS
5. Encryption key stored in metadata (base64)

**Algorithm:** AES-256 in GCM mode
- **GCM**: Galois/Counter Mode (authenticated encryption)
- **Key Size**: 256 bits (quantum-resistant for symmetric)
- **Implementation**: `/app/backend/crypto_service.py`

#### Decryption Process
1. Employee requests file
2. System validates access conditions
3. Retrieves encrypted file from GridFS
4. Retrieves encryption key from metadata
5. Decrypts file using key
6. Sends decrypted file to employee

**Security Notes:**
- Each file has unique encryption key
- Keys never exposed to frontend
- Admin has unrestricted access

### 5. Geofencing Implementation

#### Distance Calculation
**Haversine Formula:**
```python
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    
    # Convert to radians
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    # Haversine formula
    a = sin(delta_lat/2)^2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)^2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    distance = R * c
    return distance
```

**File:** `/app/backend/geofence.py`

#### Validation Logic
```python
def validate_access(request, config, wfh_approved):
    if wfh_approved:
        return {"allowed": True, "reason": "WFH approved"}
    
    # Check location
    distance = calculate_distance(...)
    location_valid = distance <= config['radius']
    
    # Check WiFi
    wifi_valid = request['wifi_ssid'] == config['allowed_ssid']
    
    # Check time
    current_time = datetime.now().strftime("%H:%M")
    time_valid = config['start_time'] <= current_time <= config['end_time']
    
    return {
        "allowed": location_valid and wifi_valid and time_valid,
        "reason": "...",
        "validations": {...}
    }
```

### 6. Machine Learning Anomaly Detection

#### Features Extracted
- Hour of access (0-23)
- Day of week (0-6)
- Access frequency
- Location variance
- Pattern deviations

#### Algorithm: Isolation Forest
- **Type**: Unsupervised learning
- **Purpose**: Detect outliers in access patterns
- **Contamination**: 10% (expected anomaly rate)
- **Training**: Requires minimum 10 access logs

#### Risk Assessment
```python
risk_ratio = suspicious_count / total_activities

if risk_ratio > 0.3:
    risk_level = "high"
elif risk_ratio > 0.15:
    risk_level = "medium"
else:
    risk_level = "low"
```

**Implementation:** `/app/backend/ml_service.py`

---

## API Reference

### Base URL
```
http://localhost:8001/api
```

### Authentication Endpoints

#### 1. Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin"
}

Response:
{
  "message": "OTP sent to your email",
  "username": "admin",
  "role": "admin"
}
```

#### 2. Verify OTP
```http
POST /api/auth/verify-otp
Content-Type: application/json

{
  "username": "admin",
  "otp": "123456"
}

Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "role": "admin",
  "username": "admin"
}
```

### Admin Endpoints

#### 3. Create Employee
```http
POST /api/admin/employees
Authorization: Bearer {token}
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "password123"
}

Response:
{
  "message": "Employee created successfully",
  "username": "john_doe"
}
```

#### 4. Get Employees
```http
GET /api/admin/employees
Authorization: Bearer {token}

Response:
[
  {
    "username": "john_doe",
    "email": "john@example.com",
    "role": "employee",
    "is_active": true,
    "created_at": "2024-12-06T10:00:00"
  }
]
```

#### 5. Delete Employee
```http
DELETE /api/admin/employees/{username}
Authorization: Bearer {token}

Response:
{
  "message": "Employee deleted successfully"
}
```

#### 6. Get Access Logs
```http
GET /api/admin/access-logs
Authorization: Bearer {token}

Response:
[
  {
    "employee_username": "john_doe",
    "file_id": "...",
    "filename": "document.pdf",
    "action": "access",
    "timestamp": "2024-12-06T14:30:00",
    "location": {"lat": 10.8505, "lon": 76.2711},
    "wifi_ssid": "OfficeWiFi",
    "success": true,
    "reason": "Access granted"
  }
]
```

#### 7. Get WFH Requests
```http
GET /api/admin/wfh-requests
Authorization: Bearer {token}

Response:
[
  {
    "employee_username": "john_doe",
    "reason": "Family emergency",
    "requested_at": "2024-12-06T09:00:00",
    "status": "pending"
  }
]
```

#### 8. Approve/Reject WFH Request
```http
PUT /api/admin/wfh-requests/{employee_username}
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "approved",
  "comment": "Approved for today"
}

Response:
{
  "message": "Request approved"
}
```

#### 9. Get Geofence Config
```http
GET /api/admin/geofence-config
Authorization: Bearer {token}

Response:
{
  "latitude": 10.8505,
  "longitude": 76.2711,
  "radius": 500,
  "allowed_ssid": "OfficeWiFi",
  "start_time": "09:00",
  "end_time": "17:00"
}
```

#### 10. Update Geofence Config
```http
PUT /api/admin/geofence-config
Authorization: Bearer {token}
Content-Type: application/json

{
  "latitude": 10.8505,
  "longitude": 76.2711,
  "radius": 1000,
  "allowed_ssid": "NewOfficeWiFi",
  "start_time": "08:00",
  "end_time": "18:00"
}

Response:
{
  "message": "Configuration updated successfully"
}
```

#### 11. Get Employee Analytics
```http
GET /api/admin/analytics/{employee_username}
Authorization: Bearer {token}

Response:
{
  "total_activities": 50,
  "suspicious_count": 3,
  "risk_level": "low",
  "patterns": [
    "Detected 3 unusual access patterns",
    "Off-hours access detected: 2 instances"
  ]
}
```

### File Endpoints

#### 12. Upload File
```http
POST /api/files/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: [binary data]

Response:
{
  "message": "File uploaded and encrypted",
  "file_id": "507f1f77bcf86cd799439011"
}
```

#### 13. List Files
```http
GET /api/files
Authorization: Bearer {token}

Response:
[
  {
    "file_id": "507f1f77bcf86cd799439011",
    "filename": "document.pdf",
    "uploaded_by": "admin",
    "uploaded_at": "2024-12-06T10:00:00",
    "encrypted": true,
    "size": 102400
  }
]
```

#### 14. Access File
```http
POST /api/files/access
Authorization: Bearer {token}
Content-Type: application/json

{
  "file_id": "507f1f77bcf86cd799439011",
  "latitude": 10.8505,
  "longitude": 76.2711,
  "wifi_ssid": "OfficeWiFi"
}

Response: [Binary file data]
Content-Disposition: attachment; filename=document.pdf
```

### Employee Endpoints

#### 15. Submit WFH Request
```http
POST /api/wfh-request
Authorization: Bearer {token}
Content-Type: application/json

{
  "reason": "Need to work from home due to personal reasons"
}

Response:
{
  "message": "Work from home request submitted"
}
```

#### 16. Get WFH Status
```http
GET /api/wfh-request/status
Authorization: Bearer {token}

Response:
{
  "employee_username": "john_doe",
  "reason": "Personal reasons",
  "requested_at": "2024-12-06T09:00:00",
  "status": "approved",
  "admin_comment": "Approved for today",
  "approved_at": "2024-12-06T09:30:00"
}
```

---

## Code Explanation

### Backend Structure

```
/app/backend/
├── server.py          # Main FastAPI application
├── models.py          # Pydantic data models
├── auth.py            # Authentication utilities
├── email_service.py   # Gmail SMTP service
├── crypto_service.py  # Encryption/decryption
├── geofence.py        # Geofencing validation
├── ml_service.py      # ML anomaly detection
├── requirements.txt   # Python dependencies
└── .env              # Environment variables
```

### Frontend Structure

```
/app/frontend/src/
├── App.js                    # Main app component
├── App.css                   # Global styles
├── pages/
│   ├── AdminLogin.jsx        # Admin login page
│   ├── EmployeeLogin.jsx     # Employee login page
│   ├── OTPVerification.jsx   # OTP verification
│   ├── AdminDashboard.jsx    # Admin dashboard
│   └── EmployeeDashboard.jsx # Employee dashboard
└── components/ui/            # Reusable UI components
```

### Key Code Snippets

#### 1. Password Hashing (auth.py)
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

#### 2. JWT Token Creation (auth.py)
```python
from jose import jwt
from datetime import datetime, timedelta

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt
```

#### 3. File Encryption (crypto_service.py)
```python
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

def encrypt_file(file_data: bytes, key: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(file_data)
    # Combine nonce + tag + ciphertext
    encrypted_data = cipher.nonce + tag + ciphertext
    return encrypted_data

def decrypt_file(encrypted_data: bytes, key: bytes) -> bytes:
    nonce = encrypted_data[:16]
    tag = encrypted_data[16:32]
    ciphertext = encrypted_data[32:]
    
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext
```

#### 4. Geolocation in React
```javascript
const getUserLocation = () => {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        });
      },
      (error) => {
        console.error('Location error:', error);
      }
    );
  }
};
```

#### 5. File Upload in React
```javascript
const handleFileUpload = async (e) => {
  e.preventDefault();
  const formData = new FormData();
  formData.append('file', selectedFile);

  await axios.post(`${API}/files/upload`, formData, {
    headers: { 
      Authorization: `Bearer ${token}`,
      'Content-Type': 'multipart/form-data'
    }
  });
};
```

---

## Testing Guide

### 1. Test Admin Flow

```bash
# Step 1: Login as admin
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Check your email for OTP

# Step 2: Verify OTP
curl -X POST http://localhost:8001/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","otp":"123456"}'

# Save the token from response

# Step 3: Create employee
curl -X POST http://localhost:8001/api/admin/employees \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"test_emp","email":"test@example.com","password":"pass123"}'
```

### 2. Test Employee Flow

```bash
# Step 1: Login as employee
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test_emp","password":"pass123"}'

# Check email for OTP

# Step 2: Verify OTP
curl -X POST http://localhost:8001/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"username":"test_emp","otp":"654321"}'

# Step 3: Submit WFH request
curl -X POST http://localhost:8001/api/wfh-request \
  -H "Authorization: Bearer EMPLOYEE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason":"Personal reasons"}'
```

### 3. Test File Operations

```bash
# Upload file (as admin)
curl -X POST http://localhost:8001/api/files/upload \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -F "file=@/path/to/test.pdf"

# List files
curl http://localhost:8001/api/files \
  -H "Authorization: Bearer TOKEN"

# Access file (as employee)
curl -X POST http://localhost:8001/api/files/access \
  -H "Authorization: Bearer EMPLOYEE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id":"FILE_ID",
    "latitude":10.8505,
    "longitude":76.2711,
    "wifi_ssid":"OfficeWiFi"
  }' \
  -o downloaded_file.pdf
```

### 4. Test Geofence Configuration

```bash
# Get current config
curl http://localhost:8001/api/admin/geofence-config \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Update config
curl -X PUT http://localhost:8001/api/admin/geofence-config \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude":10.8505,
    "longitude":76.2711,
    "radius":1000,
    "allowed_ssid":"MyOfficeWiFi",
    "start_time":"08:00",
    "end_time":"18:00"
  }'
```

---

## Deployment

### Production Checklist

1. **Change Secret Keys**
   ```env
   SECRET_KEY="your-strong-random-secret-key"
   ```

2. **Update CORS Origins**
   ```env
   CORS_ORIGINS="https://yourdomain.com"
   ```

3. **Use Production MongoDB**
   ```env
   MONGO_URL="mongodb://production-host:27017"
   ```

4. **Enable HTTPS**
   - Use reverse proxy (Nginx)
   - Install SSL certificate

5. **Environment Variables**
   - Never commit .env files
   - Use secure secret management

### Docker Deployment (Optional)

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

```dockerfile
# Frontend Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install
COPY . .
RUN yarn build
CMD ["yarn", "start"]
```

---

## Troubleshooting

### Common Issues

#### 1. OTP Email Not Received
**Problem:** Email not being sent

**Solutions:**
- Verify Gmail App Password is correct
- Check `GMAIL_USER` and `GMAIL_APP_PASSWORD` in .env
- Check spam folder
- Verify 2-Step Verification is enabled on Google account

#### 2. File Upload Fails
**Problem:** "Failed to upload file"

**Solutions:**
- Check MongoDB is running
- Verify GridFS is accessible
- Check file size limits
- Ensure proper authorization header

#### 3. Geolocation Not Working
**Problem:** Location not detected

**Solutions:**
- Enable location permissions in browser
- Use HTTPS (required by browsers)
- Check browser console for errors

#### 4. Access Denied Even When Conditions Met
**Problem:** Employee cannot access files

**Solutions:**
- Check geofence configuration in admin dashboard
- Verify time zone settings
- Ensure WiFi SSID matches exactly (case-insensitive)
- Check if within geofence radius

#### 5. MongoDB Connection Error
**Problem:** "Failed to connect to MongoDB"

**Solutions:**
```bash
# Start MongoDB
sudo systemctl start mongodb

# Check MongoDB status
sudo systemctl status mongodb

# Verify connection
mongo --eval "db.version()"
```

---

## Security Best Practices

1. **Password Security**
   - Passwords hashed with bcrypt
   - Never store plain text passwords
   - Enforce strong password policies

2. **Token Security**
   - JWT tokens expire after 60 minutes
   - Store tokens securely in localStorage
   - Validate tokens on every request

3. **File Encryption**
   - Each file has unique encryption key
   - Keys never exposed to client
   - Use AES-256 (quantum-resistant)

4. **API Security**
   - All endpoints require authentication
   - Role-based access control
   - Input validation on all endpoints

5. **Environment Variables**
   - Never commit .env files
   - Use different credentials for dev/prod
   - Rotate secrets regularly

---

## Future Enhancements

1. **Full Post-Quantum Cryptography**
   - Integrate liboqs library
   - Implement CRYSTALS-Kyber
   - Hybrid encryption scheme

2. **Enhanced ML**
   - Deep learning models
   - Real-time anomaly alerts
   - Predictive analytics

3. **Mobile App**
   - React Native implementation
   - Biometric authentication
   - Push notifications

4. **Advanced Features**
   - File versioning
   - Audit trails
   - Multi-tenant support
   - Backup and recovery

---

## Support

For questions or issues:
1. Check this tutorial
2. Review API documentation
3. Check backend logs: `/var/log/supervisor/backend.err.log`
4. Check browser console for frontend errors

---

## License

This project is for educational purposes.

---

**GeoCrypt** - Secure. Controlled. Monitored.
