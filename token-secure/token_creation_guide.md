# Token Creation and Validation - Code Examples

## 1. Creating a JWT Token (Node.js with jsonwebtoken library)

```javascript
const jwt = require('jsonwebtoken');

// Secret key - should be stored in environment variables, not in code
const SECRET_KEY = 'your-super-secret-key-12345-keep-it-safe';

// Function to create a token
function createToken(user) {
  // Payload: the data you want to include in the token
  const payload = {
    user_id: user.id,           // User's unique ID
    email: user.email,           // User's email
    role: user.role,             // User's role (e.g., 'admin', 'user')
    iat: Math.floor(Date.now() / 1000),  // Issued at (current time in seconds)
    exp: Math.floor(Date.now() / 1000) + (60 * 60)  // Expires in 1 hour
  };

  // Create token using HS256 algorithm
  const token = jwt.sign(payload, SECRET_KEY, { 
    algorithm: 'HS256',
    header: { typ: 'JWT' }
  });

  return token;
}

// Example usage
const user = {
  id: 123,
  email: 'john@example.com',
  role: 'user'
};

const token = createToken(user);
console.log('Generated Token:', token);
// Output: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjMsImVtYWlsIjoiam9obkBleGFtcGxlLmNvbSIsInJvbGUiOiJ1c2VyIiwiaWF0IjoxNzA4NDUwMDAwLCJleHAiOjE3MDg0NTM2MDB9.SIGNATURE_HERE
```

## 2. Decoding the Token (What's Inside)

```javascript
// The token above breaks down into 3 parts separated by dots:

// PART 1: Header (Base64 Decoded)
{
  "alg": "HS256",      // Algorithm: HMAC with SHA-256
  "typ": "JWT"         // Type: JSON Web Token
}

// PART 2: Payload (Base64 Decoded)
{
  "user_id": 123,
  "email": "john@example.com",
  "role": "user",
  "iat": 1708450000,        // Issued at: Feb 20, 2024, 10:53:20 AM UTC
  "exp": 1708453600         // Expires at: Feb 20, 2024, 11:53:20 AM UTC
}

// PART 3: Signature (Cryptographic Hash)
// Created by: HMAC-SHA256(base64(header) + "." + base64(payload), SECRET_KEY)
// Raw signature: some long cryptographic string
// Base64 encoded: SIGNATURE_HERE
```

## 3. Validating a Token

```javascript
// Function to validate a token
function validateToken(token) {
  try {
    // Verify the token using the same secret key
    const decoded = jwt.verify(token, SECRET_KEY, {
      algorithms: ['HS256']
    });
    
    // If we reach here, token is valid
    console.log('Token is valid!');
    console.log('User ID:', decoded.user_id);
    console.log('Email:', decoded.email);
    console.log('Role:', decoded.role);
    
    return decoded;
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      console.log('Token has expired');
    } else if (error.name === 'JsonWebTokenError') {
      console.log('Token is invalid or tampered with');
    }
    return null;
  }
}

// Example: validating a token from a request
const receivedToken = req.headers.authorization.split(' ')[1];  // Remove "Bearer " prefix
const userData = validateToken(receivedToken);

if (userData) {
  console.log('User authenticated as:', userData.email);
} else {
  console.log('Authentication failed');
}
```

## 4. What Happens When Token Is Tampered With

```javascript
// Original token
const originalToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjMsImVtYWlsIjoiam9obkBleGFtcGxlLmNvbSIsInJvbGUiOiJ1c2VyIn0.SIGNATURE';

// Attacker tries to change the payload manually
// They change "role": "user" to "role": "admin"
// But they don't know the SECRET_KEY, so they can't recalculate the signature

const tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjMsImVtYWlsIjoiam9obkBleGFtcGxlLmNvbSIsInJvbGUiOiJhZG1pbiJ9.WRONG_SIGNATURE';

// When server tries to validate:
validateToken(tamperedToken);
// Output: "Token is invalid or tampered with"
// Because the payload changed, but signature doesn't match
```

## 5. How the Signature is Created (The Math Behind It)

```javascript
const crypto = require('crypto');

// This is what happens internally when creating a JWT
function createSignatureManually(header, payload, secretKey) {
  // Step 1: Base64 encode header and payload
  const headerEncoded = Buffer.from(JSON.stringify(header)).toString('base64url');
  const payloadEncoded = Buffer.from(JSON.stringify(payload)).toString('base64url');
  
  // Step 2: Create the message to sign
  const message = `${headerEncoded}.${payloadEncoded}`;
  
  // Step 3: Use HMAC-SHA256 to create signature
  const signature = crypto
    .createHmac('sha256', secretKey)
    .update(message)
    .digest('base64url');
  
  // Step 4: Combine all three parts
  const token = `${message}.${signature}`;
  
  return token;
}

// Example
const header = { alg: 'HS256', typ: 'JWT' };
const payload = { user_id: 123, email: 'john@example.com' };
const secret = 'your-super-secret-key-12345-keep-it-safe';

const token = createSignatureManually(header, payload, secret);
console.log('Manually created token:', token);
```

## 6. Python Example (Flask + PyJWT)

```python
import jwt
from datetime import datetime, timedelta
import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')

# Creating a token
def create_token(user_id, email, role):
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'iat': datetime.utcnow(),  # Issued at
        'exp': datetime.utcnow() + timedelta(hours=1)  # Expires in 1 hour
    }
    
    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm='HS256'
    )
    
    return token

# Validating a token
def validate_token(token):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        print('Token has expired')
        return None
    except jwt.InvalidTokenError:
        print('Invalid token')
        return None

# Example usage
token = create_token(123, 'john@example.com', 'user')
print('Token:', token)

decoded = validate_token(token)
print('Decoded payload:', decoded)
```

## 7. Algorithm Comparison

### HS256 (HMAC with SHA-256)
- **Type**: Symmetric encryption (same key for signing and verifying)
- **Speed**: Fast
- **Use case**: Simple applications, internal services
- **Drawback**: Server must keep secret key safe; if compromised, attacker can forge tokens
- **Example**:
  ```
  Secret: "my-secret-key"
  Message: "header.payload"
  Signature: HMAC-SHA256(Message, Secret) = "a1b2c3d4e5f6..."
  ```

### RS256 (RSA with SHA-256)
- **Type**: Asymmetric encryption (different keys for signing and verifying)
- **Speed**: Slower than HS256
- **Use case**: Large distributed systems, OAuth providers
- **Advantage**: Public key can be shared; only private key is kept secret
- **Example**:
  ```
  Private Key (Server only): Keep secret
  Public Key (Clients): Can be shared
  Server signs with private key, clients verify with public key
  ```

**HS256 Example Code**:
```javascript
const token = jwt.sign(payload, 'secret-key', { algorithm: 'HS256' });
```

**RS256 Example Code**:
```javascript
const fs = require('fs');
const privateKey = fs.readFileSync('private.pem', 'utf8');
const publicKey = fs.readFileSync('public.pem', 'utf8');

// Signing (server only)
const token = jwt.sign(payload, privateKey, { algorithm: 'RS256' });

// Verifying (can be done anywhere with public key)
const decoded = jwt.verify(token, publicKey, { algorithms: ['RS256'] });
```

## 8. Token Lifecycle Timeline

```
Time 0:00:00 - User logs in with password
  └─> Server validates password
  └─> Server creates token with iat: 0:00:00, exp: 1:00:00

Time 0:15:30 - User makes a request
  └─> Client sends: Authorization: Bearer TOKEN
  └─> Server validates signature
  └─> Server checks: token not expired yet
  └─> Request processed ✓

Time 0:59:50 - User makes another request
  └─> Server validates signature
  └─> Server checks: token still valid (11 seconds left)
  └─> Request processed ✓

Time 1:00:01 - User tries to make a request
  └─> Server validates signature ✓ (signature is still valid)
  └─> Server checks: exp 1:00:00 < current time 1:00:01
  └─> Request rejected ✗ (token expired)
  └─> User needs to log in again to get new token
```

## 9. Security Best Practices in Code

```javascript
// ✓ GOOD: Secret key from environment variable
const SECRET_KEY = process.env.JWT_SECRET;

// ✗ BAD: Secret key hardcoded in code
const SECRET_KEY = 'hardcoded-secret-key';

// ✓ GOOD: Use HTTPS
app.use(express.json());
app.use((req, res, next) => {
  if (req.protocol !== 'https' && process.env.NODE_ENV === 'production') {
    return res.status(400).send('HTTPS required');
  }
  next();
});

// ✓ GOOD: Store token in secure HTTP-only cookie
res.cookie('token', token, {
  httpOnly: true,        // Can't be accessed by JavaScript
  secure: true,          // Only sent over HTTPS
  sameSite: 'strict',    // Prevents CSRF attacks
  maxAge: 3600000        // 1 hour
});

// ✗ BAD: Storing token in localStorage (vulnerable to XSS)
// localStorage.setItem('token', token);  // Don't do this!

// ✓ GOOD: Extract token from header safely
function extractToken(req) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null;
  }
  return authHeader.substring(7);  // Remove "Bearer " prefix
}

// ✓ GOOD: Use short expiration times
const token = jwt.sign(payload, SECRET_KEY, {
  expiresIn: '15m'  // 15 minutes for access token
});

// ✓ GOOD: Implement refresh tokens for longer sessions
const refreshToken = jwt.sign(payload, REFRESH_SECRET, {
  expiresIn: '7d'  // 7 days for refresh token
});
```

## 10. Complete Login and Middleware Example

```javascript
const express = require('express');
const jwt = require('jsonwebtoken');
const app = express();

const SECRET_KEY = process.env.JWT_SECRET || 'dev-secret-key';

// Middleware to verify token
function verifyToken(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];
  
  if (!token) {
    return res.status(401).json({ error: 'No token provided' });
  }
  
  try {
    const decoded = jwt.verify(token, SECRET_KEY);
    req.user = decoded;  // Attach user info to request
    next();
  } catch (error) {
    return res.status(403).json({ error: 'Invalid or expired token' });
  }
}

// Login endpoint
app.post('/login', (req, res) => {
  const user = {
    id: 123,
    email: 'john@example.com',
    role: 'user'
  };
  
  const token = jwt.sign(user, SECRET_KEY, {
    expiresIn: '1h',
    algorithm: 'HS256'
  });
  
  res.json({ token });
});

// Protected endpoint
app.get('/protected', verifyToken, (req, res) => {
  res.json({
    message: 'This is protected',
    user: req.user
  });
});

app.listen(3000);
```

## Summary

**Token Creation Process**:
1. User logs in with username/password
2. Server validates credentials
3. Server creates payload with user info + timestamps
4. Server signs payload with secret key using SHA256
5. Server sends complete token to client

**Token Validation Process**:
1. Client includes token in Authorization header
2. Server extracts the three parts (header.payload.signature)
3. Server recalculates signature using same algorithm and secret key
4. If signatures match AND token not expired, request is processed
5. If signature doesn't match OR token expired, request is rejected

**Key Insight**: The signature is what prevents tampering. Anyone can read the payload, but without the secret key, they can't create a valid signature.
