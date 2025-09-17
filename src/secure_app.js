/**
 * Secure JavaScript code that should pass SAST analysis.
 * This file demonstrates security best practices for Node.js applications.
 */

const crypto = require('crypto');
const fs = require('fs').promises;
const path = require('path');
const { promisify } = require('util');

class SecureWebApp {
    constructor() {
        this.allowedOrigins = ['https://example.com', 'https://api.example.com'];
        this.sessionTimeout = 30 * 60 * 1000; // 30 minutes
    }

    /**
     * Secure password hashing using bcrypt-style approach
     */
    async hashPassword(password) {
        if (typeof password !== 'string' || password.length < 8) {
            throw new Error('Password must be at least 8 characters long');
        }

        const salt = crypto.randomBytes(32);
        const hash = await new Promise((resolve, reject) => {
            crypto.pbkdf2(password, salt, 100000, 64, 'sha512', (err, derivedKey) => {
                if (err) reject(err);
                else resolve(derivedKey);
            });
        });

        return {
            salt: salt.toString('hex'),
            hash: hash.toString('hex')
        };
    }

    /**
     * Secure input validation and sanitization
     */
    sanitizeInput(input, type = 'string') {
        if (typeof input !== 'string') {
            throw new Error('Input must be a string');
        }

        switch (type) {
            case 'email':
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(input)) {
                    throw new Error('Invalid email format');
                }
                return input.toLowerCase().trim();

            case 'alphanumeric':
                const alphanumericRegex = /^[a-zA-Z0-9]+$/;
                if (!alphanumericRegex.test(input)) {
                    throw new Error('Input must be alphanumeric');
                }
                return input;

            case 'string':
            default:
                // Remove potentially dangerous characters
                return input.replace(/[<>\"'&]/g, '').trim().substring(0, 100);
        }
    }

    /**
     * Secure file path validation
     */
    validateFilePath(userPath) {
        if (typeof userPath !== 'string') {
            throw new Error('File path must be a string');
        }

        const normalizedPath = path.normalize(userPath);
        const resolvedPath = path.resolve('/safe/uploads', normalizedPath);
        const allowedBase = path.resolve('/safe/uploads');

        // Prevent path traversal
        if (!resolvedPath.startsWith(allowedBase)) {
            throw new Error('Path traversal attempt detected');
        }

        return resolvedPath;
    }

    /**
     * Secure random token generation
     */
    generateSecureToken(length = 32) {
        return crypto.randomBytes(length).toString('hex');
    }

    /**
     * CORS validation
     */
    validateOrigin(origin) {
        if (!origin || !this.allowedOrigins.includes(origin)) {
            throw new Error('Origin not allowed');
        }
        return true;
    }

    /**
     * Secure session management
     */
    createSession(userId) {
        if (!userId || typeof userId !== 'string') {
            throw new Error('Valid user ID required');
        }

        return {
            sessionId: this.generateSecureToken(),
            userId: userId,
            createdAt: new Date(),
            expiresAt: new Date(Date.now() + this.sessionTimeout),
            isValid: true
        };
    }

    /**
     * SQL query with parameterized statements (conceptual)
     */
    buildSecureQuery(table, conditions) {
        const allowedTables = ['users', 'products', 'orders'];
        
        if (!allowedTables.includes(table)) {
            throw new Error('Table not allowed');
        }

        // Return parameterized query structure
        const whereClause = Object.keys(conditions).map(key => `${key} = ?`).join(' AND ');
        return {
            query: `SELECT * FROM ${table} WHERE ${whereClause}`,
            params: Object.values(conditions)
        };
    }

    /**
     * Secure file reading with validation
     */
    async readSecureFile(filename) {
        try {
            const safePath = this.validateFilePath(filename);
            const content = await fs.readFile(safePath, 'utf8');
            return content;
        } catch (error) {
            // Log error without exposing sensitive information
            console.log('File read error occurred');
            throw new Error('File access denied');
        }
    }

    /**
     * Rate limiting helper
     */
    checkRateLimit(clientId, maxRequests = 100, windowMs = 60000) {
        // This would typically use Redis or similar in production
        const now = Date.now();
        const windowStart = now - windowMs;
        
        // Simplified rate limiting logic
        if (!this.rateLimitStore) {
            this.rateLimitStore = new Map();
        }

        const clientRequests = this.rateLimitStore.get(clientId) || [];
        const recentRequests = clientRequests.filter(timestamp => timestamp > windowStart);

        if (recentRequests.length >= maxRequests) {
            throw new Error('Rate limit exceeded');
        }

        recentRequests.push(now);
        this.rateLimitStore.set(clientId, recentRequests);
        
        return true;
    }
}

// Example usage
async function main() {
    const app = new SecureWebApp();

    try {
        // Secure password handling
        const passwordData = await app.hashPassword('SecurePassword123!');
        console.log('Password hashed securely');

        // Input sanitization
        const cleanInput = app.sanitizeInput('user@example.com', 'email');
        console.log('Input sanitized:', cleanInput);

        // Secure token generation
        const token = app.generateSecureToken();
        console.log('Secure token generated');

        // Session creation
        const session = app.createSession('user123');
        console.log('Secure session created');

        // Rate limiting
        app.checkRateLimit('client123');
        console.log('Rate limit check passed');

    } catch (error) {
        console.error('Security operation failed:', error.message);
    }
}

if (require.main === module) {
    main();
}

module.exports = SecureWebApp;