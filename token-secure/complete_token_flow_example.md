# Complete Token Flow: UI Login → API Call → Server Validation → Rule-Based Response

## 1. UI (Frontend) - Login Page

```html
<!-- login.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <style>
        body { font-family: Arial; margin: 50px; }
        .form-group { margin: 15px 0; }
        input { padding: 8px; width: 300px; }
        button { padding: 10px 20px; cursor: pointer; }
        .error { color: red; }
        .success { color: green; }
    </style>
</head>
<body>
    <h2>Login</h2>
    <div id="loginForm">
        <div class="form-group">
            <label>Email:</label>
            <input type="email" id="email" placeholder="john@example.com">
        </div>
        <div class="form-group">
            <label>Password:</label>
            <input type="password" id="password" placeholder="password123">
        </div>
        <button onclick="login()">Login</button>
        <div id="message"></div>
    </div>

    <script>
        // Function to handle login
        async function login() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const messageDiv = document.getElementById('message');

            if (!email || !password) {
                messageDiv.innerHTML = '<p class="error">Please enter email and password</p>';
                return;
            }

            try {
                // Step 1: Send login credentials to server
                const response = await fetch('http://localhost:3000/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email, password })
                });

                const data = await response.json();

                if (response.ok) {
                    // Step 2: Server returns token
                    const token = data.token;
                    
                    // Step 3: Store token securely (HTTP-only cookie is best, but we'll use sessionStorage for demo)
                    sessionStorage.setItem('token', token);
                    
                    messageDiv.innerHTML = '<p class="success">Login successful! Redirecting...</p>';
                    
                    // Step 4: Redirect to dashboard
                    setTimeout(() => {
                        window.location.href = '/dashboard.html';
                    }, 1500);
                } else {
                    messageDiv.innerHTML = `<p class="error">Login failed: ${data.error}</p>`;
                }
            } catch (error) {
                messageDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
```

## 2. UI (Frontend) - Dashboard with API Calls

```html
<!-- dashboard.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <style>
        body { font-family: Arial; margin: 50px; }
        .container { max-width: 800px; }
        button { padding: 10px 15px; margin: 5px; cursor: pointer; }
        .section { border: 1px solid #ddd; padding: 20px; margin: 20px 0; }
        .response { background: #f0f0f0; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .success { color: green; }
        .error { color: red; }
        .info { color: blue; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background: #4CAF50; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Dashboard</h1>
        <p id="userInfo"></p>
        <button onclick="logout()">Logout</button>

        <!-- Section 1: Public Data -->
        <div class="section">
            <h2>Public Data (Everyone Can Access)</h2>
            <button onclick="getPublicData()">Get Public Data</button>
            <div id="publicResponse" class="response" style="display:none;"></div>
        </div>

        <!-- Section 2: Protected User Data -->
        <div class="section">
            <h2>Protected User Data (Authenticated Users)</h2>
            <button onclick="getProtectedData()">Get My Profile</button>
            <div id="protectedResponse" class="response" style="display:none;"></div>
        </div>

        <!-- Section 3: Admin Data -->
        <div class="section">
            <h2>Admin Data (Admin Only)</h2>
            <button onclick="getAdminData()">Get Admin Dashboard</button>
            <div id="adminResponse" class="response" style="display:none;"></div>
        </div>

        <!-- Section 4: Delete User (Admin Only) -->
        <div class="section">
            <h2>Admin Actions</h2>
            <input type="number" id="userIdToDelete" placeholder="User ID to delete">
            <button onclick="deleteUser()">Delete User</button>
            <div id="deleteResponse" class="response" style="display:none;"></div>
        </div>
    </div>

    <script>
        // Utility function to get token from storage
        function getToken() {
            return sessionStorage.getItem('token');
        }

        // Utility function to display user info from token
        function displayUserInfo() {
            const token = getToken();
            if (!token) {
                window.location.href = '/login.html';
                return;
            }

            // Decode JWT payload (Note: this is just decoding, not verifying)
            // In production, don't rely on client-side token validation
            try {
                const parts = token.split('.');
                const payload = JSON.parse(atob(parts[1]));
                document.getElementById('userInfo').innerHTML = 
                    `<p class="info">Logged in as: <strong>${payload.email}</strong> (Role: ${payload.role})</p>`;
            } catch (error) {
                console.error('Error decoding token:', error);
            }
        }

        // Call this when page loads
        window.onload = function() {
            displayUserInfo();
        };

        // API Call 1: Get Public Data (No token needed)
        async function getPublicData() {
            try {
                const response = await fetch('http://localhost:3000/api/public', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();
                displayResponse('publicResponse', response.status, data);
            } catch (error) {
                displayResponse('publicResponse', 'error', { error: error.message });
            }
        }

        // API Call 2: Get Protected Data (Token required)
        async function getProtectedData() {
            try {
                const token = getToken();
                
                if (!token) {
                    displayResponse('protectedResponse', 'error', { error: 'No token found. Please login.' });
                    return;
                }

                const response = await fetch('http://localhost:3000/api/protected/profile', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`  // Pass token in header
                    }
                });

                const data = await response.json();
                displayResponse('protectedResponse', response.status, data);
            } catch (error) {
                displayResponse('protectedResponse', 'error', { error: error.message });
            }
        }

        // API Call 3: Get Admin Data (Token + Admin Role required)
        async function getAdminData() {
            try {
                const token = getToken();
                
                if (!token) {
                    displayResponse('adminResponse', 'error', { error: 'No token found. Please login.' });
                    return;
                }

                const response = await fetch('http://localhost:3000/api/admin/dashboard', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    }
                });

                const data = await response.json();
                displayResponse('adminResponse', response.status, data);
            } catch (error) {
                displayResponse('adminResponse', 'error', { error: error.message });
            }
        }

        // API Call 4: Delete User (Admin Only)
        async function deleteUser() {
            const userId = document.getElementById('userIdToDelete').value;
            
            if (!userId) {
                displayResponse('deleteResponse', 'error', { error: 'Please enter a User ID' });
                return;
            }

            try {
                const token = getToken();
                
                const response = await fetch(`http://localhost:3000/api/admin/users/${userId}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    }
                });

                const data = await response.json();
                displayResponse('deleteResponse', response.status, data);
            } catch (error) {
                displayResponse('deleteResponse', 'error', { error: error.message });
            }
        }

        // Logout function
        function logout() {
            sessionStorage.removeItem('token');
            window.location.href = '/login.html';
        }

        // Helper function to display responses
        function displayResponse(elementId, status, data) {
            const element = document.getElementById(elementId);
            const statusClass = (status >= 200 && status < 300) ? 'success' : 'error';
            const statusText = (typeof status === 'number') ? `HTTP ${status}` : status;
            
            element.innerHTML = `
                <p class="${statusClass}"><strong>Status:</strong> ${statusText}</p>
                <pre>${JSON.stringify(data, null, 2)}</pre>
            `;
            element.style.display = 'block';
        }
    </script>
</body>
</html>
```

## 3. Backend Server (Node.js/Express)

```javascript
// server.js
const express = require('express');
const jwt = require('jsonwebtoken');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

// Secret key (in production, use environment variable)
const SECRET_KEY = 'your-secret-key-12345';

// Mock database of users
const users = [
    {
        id: 1,
        email: 'admin@example.com',
        password: 'admin123',
        role: 'admin',
        name: 'Admin User'
    },
    {
        id: 2,
        email: 'john@example.com',
        password: 'john123',
        role: 'user',
        name: 'John Doe'
    },
    {
        id: 3,
        email: 'jane@example.com',
        password: 'jane123',
        role: 'user',
        name: 'Jane Smith'
    }
];

// ============ Step 1: Login Endpoint (Issues Token) ============
app.post('/login', (req, res) => {
    const { email, password } = req.body;

    // Find user in database
    const user = users.find(u => u.email === email && u.password === password);

    if (!user) {
        return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Create token with user data
    const token = jwt.sign(
        {
            user_id: user.id,
            email: user.email,
            role: user.role,
            name: user.name
        },
        SECRET_KEY,
        {
            expiresIn: '1h',
            algorithm: 'HS256'
        }
    );

    res.json({ 
        success: true,
        token,
        user: {
            id: user.id,
            email: user.email,
            name: user.name,
            role: user.role
        }
    });
});

// ============ Step 2: Middleware to Verify Token ============
function verifyToken(req, res, next) {
    const authHeader = req.headers['authorization'];
    
    // Extract token from "Bearer TOKEN"
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ error: 'No token provided' });
    }

    try {
        // Verify and decode token
        const decoded = jwt.verify(token, SECRET_KEY);
        
        // Attach decoded user info to request
        req.user = decoded;
        
        next();
    } catch (error) {
        if (error.name === 'TokenExpiredError') {
            return res.status(401).json({ error: 'Token has expired' });
        }
        return res.status(403).json({ error: 'Invalid token' });
    }
}

// ============ Step 3: Middleware to Check Admin Role ============
function requireAdmin(req, res, next) {
    if (req.user.role !== 'admin') {
        return res.status(403).json({ 
            error: 'Access denied. Admin role required.',
            your_role: req.user.role
        });
    }
    next();
}

// ============ Step 4: Endpoints with Different Rules ============

// PUBLIC Endpoint - No authentication required
app.get('/api/public', (req, res) => {
    res.json({
        message: 'This is public data, anyone can access',
        data: {
            site_name: 'My Application',
            version: '1.0.0',
            features: ['login', 'dashboard', 'admin']
        }
    });
});

// PROTECTED Endpoint - Authentication required
app.get('/api/protected/profile', verifyToken, (req, res) => {
    // req.user contains decoded token data
    const user = users.find(u => u.id === req.user.user_id);

    if (!user) {
        return res.status(404).json({ error: 'User not found' });
    }

    res.json({
        message: 'This is your protected profile',
        profile: {
            id: user.id,
            email: user.email,
            name: user.name,
            role: user.role,
            joined_at: '2024-01-15',
            last_login: new Date().toISOString()
        }
    });
});

// ADMIN ONLY Endpoint - Admin role required
app.get('/api/admin/dashboard', verifyToken, requireAdmin, (req, res) => {
    // Only admin users can access this
    
    res.json({
        message: 'Welcome to admin dashboard',
        admin_data: {
            total_users: users.length,
            total_admins: users.filter(u => u.role === 'admin').length,
            total_regular_users: users.filter(u => u.role === 'user').length,
            users: users.map(u => ({
                id: u.id,
                email: u.email,
                name: u.name,
                role: u.role
            }))
        }
    });
});

// DELETE USER Endpoint - Admin only
app.delete('/api/admin/users/:userId', verifyToken, requireAdmin, (req, res) => {
    const userIdToDelete = parseInt(req.params.userId);
    const userIndex = users.findIndex(u => u.id === userIdToDelete);

    if (userIndex === -1) {
        return res.status(404).json({ error: 'User not found' });
    }

    const deletedUser = users.splice(userIndex, 1)[0];

    res.json({
        message: 'User deleted successfully',
        deleted_user: {
            id: deletedUser.id,
            email: deletedUser.email,
            name: deletedUser.name
        }
    });
});

// ============ Error Handling ============
app.use((err, req, res, next) => {
    console.error('Error:', err);
    res.status(500).json({ error: 'Internal server error' });
});

app.listen(3000, () => {
    console.log('Server running on http://localhost:3000');
    console.log('\nTest users:');
    console.log('Admin: admin@example.com / admin123');
    console.log('User: john@example.com / john123');
});
```

## 4. Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        UI/FRONTEND                              │
└─────────────────────────────────────────────────────────────────┘
         │
         │ 1. User enters email & password
         │ POST /login {email, password}
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND SERVER                               │
│ - Validates credentials                                         │
│ - Creates JWT token with user data & role                       │
│ - Sends token back                                              │
└─────────────────────────────────────────────────────────────────┘
         │
         │ 2. Token received
         │ Store in sessionStorage
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    UI/FRONTEND                                  │
│ Now has token, can make API calls                               │
└─────────────────────────────────────────────────────────────────┘
         │
         │ 3. Call protected API
         │ GET /api/protected/profile
         │ Header: "Authorization: Bearer TOKEN"
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND SERVER                               │
│                                                                 │
│ Step A: Extract token from Authorization header                 │
│ Step B: Verify token signature (using SECRET_KEY)               │
│ Step C: Check if token is expired                               │
│ Step D: Extract user data from token                            │
│         (user_id, email, role)                                  │
│                                                                 │
│ Step E: Apply RULES based on token data                         │
│                                                                 │
│   IF endpoint == "/api/public"                                  │
│      └─> ALLOW (no auth needed)                                │
│                                                                 │
│   ELSE IF endpoint == "/api/protected/..."                      │
│      └─> CHECK if token exists                                 │
│      └─> IF token valid → ALLOW                                │
│      └─> IF token invalid/expired → DENY (401)                 │
│                                                                 │
│   ELSE IF endpoint == "/api/admin/..."                          │
│      └─> CHECK if token exists                                 │
│      └─> CHECK if user.role == "admin"                         │
│      └─> IF valid token AND admin role → ALLOW                 │
│      └─> IF no admin role → DENY (403)                         │
│      └─> IF no valid token → DENY (401)                        │
│                                                                 │
│ Step F: Fetch data from database based on rule                  │
│ Step G: Send response                                           │
└─────────────────────────────────────────────────────────────────┘
         │
         │ 4. Response received
         │ Display to user
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    UI/FRONTEND                                  │
│ Display response based on status code:                          │
│ - 200: Show data                                                │
│ - 401: Show "Login required" or "Token expired"                │
│ - 403: Show "Access denied"                                     │
└─────────────────────────────────────────────────────────────────┘
```

## 5. Example API Responses

```javascript
// Response 1: Successful Login
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJlbWFpbCI6ImpvaG5AZXhhbXBsZS5jb20iLCJyb2xlIjoidXNlciIsIm5hbWUiOiJKb2huIERvZSIsImlhdCI6MTcwODQ1MDAwMCwiZXhwIjoxNzA4NDUzNjAwfQ.signature",
  "user": {
    "id": 2,
    "email": "john@example.com",
    "name": "John Doe",
    "role": "user"
  }
}

// Response 2: Invalid Login
{
  "error": "Invalid credentials"
}

// Response 3: Protected Data Success (User with valid token)
{
  "message": "This is your protected profile",
  "profile": {
    "id": 2,
    "email": "john@example.com",
    "name": "John Doe",
    "role": "user",
    "joined_at": "2024-01-15",
    "last_login": "2024-02-20T10:53:20.000Z"
  }
}

// Response 4: No Token Provided
{
  "error": "No token provided"
}

// Response 5: Invalid/Expired Token
{
  "error": "Token has expired"
}

// Response 6: Insufficient Permissions (User tries admin endpoint)
{
  "error": "Access denied. Admin role required.",
  "your_role": "user"
}

// Response 7: Admin Data Success (Admin with valid token)
{
  "message": "Welcome to admin dashboard",
  "admin_data": {
    "total_users": 3,
    "total_admins": 1,
    "total_regular_users": 2,
    "users": [
      { "id": 1, "email": "admin@example.com", "name": "Admin User", "role": "admin" },
      { "id": 2, "email": "john@example.com", "name": "John Doe", "role": "user" },
      { "id": 3, "email": "jane@example.com", "name": "Jane Smith", "role": "user" }
    ]
  }
}
```

## 6. Testing the Flow

```bash
# Terminal 1: Start the server
node server.js
# Output: Server running on http://localhost:3000

# Terminal 2: Test with curl

# Step 1: Login
curl -X POST http://localhost:3000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"john123"}'

# Response (copy the token):
# {
#   "success": true,
#   "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   ...
# }

# Step 2: Call protected API with token
curl -X GET http://localhost:3000/api/protected/profile \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Step 3: Try admin API with regular user (should fail)
curl -X GET http://localhost:3000/api/admin/dashboard \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Response: { "error": "Access denied. Admin role required." }

# Step 4: Login as admin
curl -X POST http://localhost:3000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'

# Step 5: Try admin API with admin token (should succeed)
curl -X GET http://localhost:3000/api/admin/dashboard \
  -H "Authorization: Bearer [ADMIN_TOKEN]"
```

## Summary of the Complete Flow

1. **UI Login**: User enters credentials
2. **Server Validation**: Server checks credentials against database
3. **Token Creation**: Server creates JWT with user data and role
4. **Token Storage**: UI stores token (in sessionStorage/cookie)
5. **API Call**: UI sends request with token in Authorization header
6. **Token Verification**: Server extracts token, verifies signature, checks expiration
7. **Rule Application**: Server checks token and role against endpoint rules
8. **Response**: Server returns data or error based on rules
9. **UI Display**: UI shows data or error message to user

The key concept: **Token contains user info and role**, server uses these to decide what data to return.
