// server.js
const express = require('express');
const jwt = require('jsonwebtoken');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

// Secret key (in production, use environment variable)
const SECRET_KEY = '12345';

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