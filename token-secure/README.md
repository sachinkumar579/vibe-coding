# TokenSecure - Bearer Token Authentication System

A complete end-to-end implementation demonstrating JWT-based bearer token authentication with role-based access control. This project includes frontend UI, backend server, and comprehensive documentation on how tokens are created, validated, and used to protect API endpoints.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [How It Works](#how-it-works)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Security Considerations](#security-considerations)
- [File Descriptions](#file-descriptions)

## 🎯 Project Overview

TokenSecure is an educational and practical project that demonstrates modern authentication patterns using JWT bearer tokens. It showcases:

- User login with credential validation
- Token creation with user data and role information
- Token storage and transmission
- Token verification and signature validation
- Rule-based access control based on user roles
- Protected and public API endpoints

## ✨ Features

### Authentication & Authorization
- **JWT Bearer Token Authentication**: Secure token-based authentication system
- **HS256 Cryptographic Signing**: HMAC-SHA256 algorithm for token signing
- **Token Expiration**: Automatic token expiration (1 hour default)
- **Role-Based Access Control (RBAC)**: Different access levels for users and admins

### Frontend
- Clean login interface
- Protected dashboard with user info display
- Multiple API call examples (public, protected, admin)
- Real-time response display
- Error handling and user feedback

### Backend
- Express.js REST API server
- User authentication with credential validation
- Token middleware for verification
- Admin authorization middleware
- Comprehensive error handling

## 📁 Project Structure

```
TokenSecure/
├── README.md                          # This file
├── token_creation_guide.md            # Detailed token creation & algorithms
├── complete_token_flow_example.md     # Full implementation example
├── server.js                          # Backend Express server
├── login.html                         # Login page (frontend)
└── dashboard.html                     # Protected dashboard (frontend)
```

## 🔧 Prerequisites

### Required
- **Node.js** (v14 or higher)
- **npm** (comes with Node.js)
- **Modern web browser** (Chrome, Firefox, Safari, Edge)

### Optional
- **curl** (for testing API endpoints via terminal)
- **Postman** (for advanced API testing)

## 📦 Installation

### Step 1: Clone or Download the Project

```bash
git clone https://github.com/sachinkumar579/vibe-coding.git
cd tokensecure
```

### Step 2: Install Dependencies

```bash
npm install express jsonwebtoken cors
```

Or use the provided package.json:

```bash
npm install
```

### Step 3: Verify Installation

```bash
node -v  # Check Node.js version
npm -v   # Check npm version
```

## 🚀 Running the Application

### Step 1: Start the Backend Server

```bash
node server.js
```

**Expected output:**
```
Server running on http://localhost:3000

Test users:
Admin: admin@example.com / admin123
User: john@example.com / john123
```

### Step 2: Open Frontend in Browser

Use a simple HTTP server to serve the HTML files:

```bash
# Using Python (if installed)
python -m http.server 8000

# Or using Node.js http-server
npm install -g http-server
http-server
```

Then open your browser and navigate to:
- **Login Page**: `http://localhost:8000/login.html`
- **Dashboard**: `http://localhost:8000/dashboard.html` (after login)

## 🔄 How It Works

### Authentication Flow

```
1. User Login
   └─> User enters email & password on login.html
   └─> Frontend sends POST request to /login

2. Server Validation
   └─> Backend validates credentials against user database
   └─> If valid: creates JWT token with user data & role
   └─> If invalid: returns 401 error

3. Token Storage
   └─> Frontend receives token
   └─> Stores token in sessionStorage (or secure cookie)

4. Protected API Calls
   └─> Frontend sends request with "Authorization: Bearer TOKEN" header
   └─> Backend extracts & verifies token signature
   └─> Backend checks token expiration
   └─> Backend verifies user role against endpoint requirements

5. Rule-Based Response
   └─> Public endpoints: No token needed
   └─> Protected endpoints: Valid token required
   └─> Admin endpoints: Valid token + admin role required
   └─> Server returns data or error based on rules

6. Display Results
   └─> Frontend displays response or error message
```

### Token Structure (JWT)

A token consists of 3 parts separated by dots:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJ1c2VyX2lkIjoyLCJlbWFpbCI6ImpvaG5AZXhhbXBsZS5jb20ifQ.
signature_hash_here

[Header].[Payload].[Signature]
```

**Header**: Algorithm and token type
**Payload**: User data (user_id, email, role, iat, exp)
**Signature**: Cryptographic signature preventing tampering

## 🔌 API Endpoints

### Public Endpoint (No Authentication Required)

```http
GET /api/public
Authorization: (not required)
Response: 200 OK
```

Returns public data accessible to everyone.

### Protected Endpoint (Authentication Required)

```http
GET /api/protected/profile
Authorization: Bearer <token>
Response: 200 OK (if token valid)
Response: 401 Unauthorized (if no token or expired)
```

Returns user profile information. Requires valid token.

### Admin Endpoint (Admin Role Required)

```http
GET /api/admin/dashboard
Authorization: Bearer <token>
Response: 200 OK (if admin)
Response: 403 Forbidden (if not admin)
Response: 401 Unauthorized (if no token)
```

Returns admin dashboard data. Requires valid token AND admin role.

### Delete User Endpoint (Admin Only)

```http
DELETE /api/admin/users/:userId
Authorization: Bearer <token>
Response: 200 OK (if successful)
Response: 403 Forbidden (if not admin)
Response: 404 Not Found (if user doesn't exist)
```

Deletes a user. Requires admin privileges.

## 🧪 Testing

### Test Users

The application comes with pre-configured test users:

| Email | Password | Role |
|-------|----------|------|
| admin@example.com | admin123 | admin |
| john@example.com | john123 | user |
| jane@example.com | jane123 | user |

### Testing with Browser

1. Open login.html
2. Log in with `john@example.com` / `john123`
3. Try accessing different endpoints on dashboard
4. Log out and try with `admin@example.com` / `admin123`
5. Compare the differences in available data

### Testing with curl

#### 1. Login and Get Token

```bash
curl -X POST http://localhost:3000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"john123"}'
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 2,
    "email": "john@example.com",
    "name": "John Doe",
    "role": "user"
  }
}
```

#### 2. Access Public Data (No Token)

```bash
curl -X GET http://localhost:3000/api/public
```

**Response:**
```json
{
  "message": "This is public data, anyone can access",
  "data": {
    "site_name": "My Application",
    "version": "1.0.0"
  }
}
```

#### 3. Access Protected Data (With Token)

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET http://localhost:3000/api/protected/profile \
  -H "Authorization: Bearer $TOKEN"
```

#### 4. Try Admin Endpoint as Regular User

```bash
curl -X GET http://localhost:3000/api/admin/dashboard \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "error": "Access denied. Admin role required.",
  "your_role": "user"
}
```

#### 5. Login as Admin and Try Admin Endpoint

```bash
# Get admin token
curl -X POST http://localhost:3000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'

# Use admin token
ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET http://localhost:3000/api/admin/dashboard \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## 🔒 Security Considerations

### Current Implementation (Development)

This project is designed for **educational purposes**. The following are development shortcuts:

⚠️ **NOT PRODUCTION-READY FEATURES:**

- Secret key is hardcoded in server.js
- Passwords are stored in plain text
- Token stored in sessionStorage (vulnerable to XSS)
- No HTTPS enforcement
- No rate limiting
- No CSRF protection

### Production Security Best Practices

To deploy this in production, implement:

1. **Secret Key Management**
   ```javascript
   const SECRET_KEY = process.env.JWT_SECRET;
   ```
   Store in environment variables or secure vault

2. **Password Hashing**
   ```bash
   npm install bcryptjs
   ```
   Hash passwords with bcrypt before storing

3. **Secure Token Storage**
   ```javascript
   res.cookie('token', token, {
     httpOnly: true,      // Prevents XSS
     secure: true,        // HTTPS only
     sameSite: 'strict'   // CSRF protection
   });
   ```

4. **HTTPS Only**
   - All communication over HTTPS
   - Enforce in production

5. **Rate Limiting**
   ```bash
   npm install express-rate-limit
   ```

6. **Token Refresh**
   - Short-lived access tokens (15 minutes)
   - Long-lived refresh tokens (7 days)

7. **CORS Configuration**
   ```javascript
   const cors = require('cors');
   app.use(cors({
     origin: 'https://yourdomain.com',
     credentials: true
   }));
   ```

## 📖 File Descriptions

### 1. **server.js**
The Express.js backend server implementing:
- POST `/login` - User authentication and token creation
- Middleware for token verification
- Middleware for admin authorization
- Public, protected, and admin endpoints
- Full error handling

**Dependencies:**
- express
- jsonwebtoken
- cors

### 2. **login.html**
Frontend login page featuring:
- Email and password input fields
- Login button with validation
- Error/success message display
- Token storage in sessionStorage
- Redirect to dashboard on successful login

**Functionality:**
- Client-side form validation
- POST request to /login endpoint
- Token extraction from response
- Secure redirect handling

### 3. **dashboard.html**
Protected dashboard with:
- User profile display
- Four different API call examples:
  - Public data access
  - Protected profile access
  - Admin dashboard access
  - Delete user (admin only)
- Response display with formatted JSON
- Logout functionality

**Functionality:**
- Token verification on page load
- Bearer token inclusion in headers
- Real-time response formatting
- HTTP status code display

## 🎓 Learning Resources

### Token Creation Guide
See `token_creation_guide.md` for:
- Detailed token structure
- HS256 vs RS256 algorithms
- Manual signature creation
- Python and JavaScript examples
- Security best practices

### Complete Flow Example
See `complete_token_flow_example.md` for:
- Full UI implementation
- Complete backend code
- Step-by-step flow diagrams
- All API responses
- Curl testing commands

## 🐛 Troubleshooting

### Port Already in Use

If port 3000 is already in use:

```javascript
// In server.js, change:
app.listen(3000, () => {
// to:
app.listen(3001, () => {
```

Then update frontend fetch URLs to `http://localhost:3001`

### CORS Errors

If you get CORS errors:
- Ensure the backend server is running
- Check that frontend is accessing `http://localhost:3000`
- Verify CORS is enabled in server.js

### Token Expired Errors

Tokens expire after 1 hour. To change:

```javascript
// In server.js, change:
expiresIn: '1h'
// to:
expiresIn: '24h'  // 24 hours
```

### Can't Access Dashboard After Login

- Check browser console for errors (F12)
- Verify sessionStorage has the token
- Ensure backend server is running

## 📝 License

This project is provided for educational purposes.

## 🤝 Contributing

Suggestions and improvements welcome! This is an educational project designed to teach JWT authentication concepts.

## 📞 Support

For questions about:
- **JWT Concepts**: See `token_creation_guide.md`
- **Implementation Details**: See `complete_token_flow_example.md`
- **Code Issues**: Check the Troubleshooting section

---

**Happy Learning! 🎉**

TokenSecure demonstrates modern web authentication in a clear, practical way. Use it to understand how tokens protect your applications!
