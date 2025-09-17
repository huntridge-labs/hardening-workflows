/**
 * Vulnerable JavaScript code that should fail SAST analysis.
 * This file contains multiple security vulnerabilities for testing purposes.
 * WARNING: This code is intentionally insecure - DO NOT USE IN PRODUCTION!
 */

const fs = require('fs');
const exec = require('child_process').exec;
const crypto = require('crypto');

class VulnerableWebApp {
    constructor() {
        // Hard-coded secrets (CWE-798)
        this.apiKey = 'sk-1234567890abcdef';
        this.dbPassword = 'admin123';
        this.jwtSecret = 'supersecret';
        this.adminPassword = 'password';
    }

    /**
     * Command injection vulnerability (CWE-78)
     */
    executeUserCommand(userInput) {
        // Directly executing user input without validation
        const command = `ls ${userInput}`;
        exec(command, (error, stdout, stderr) => {
            if (error) {
                console.log(`Error: ${error}`);
                return;
            }
            console.log(stdout);
        });
    }

    /**
     * SQL injection vulnerability (CWE-89)
     */
    getUserData(userId) {
        // Building SQL query with string concatenation
        const query = `SELECT * FROM users WHERE id = ${userId}`;
        console.log(`Executing query: ${query}`);
        
        // Simulated database query (vulnerable)
        return `Database result for query: ${query}`;
    }

    /**
     * Path traversal vulnerability (CWE-22)
     */
    readUserFile(filename) {
        // No validation on file path
        const filePath = `./uploads/${filename}`;
        
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            return content;
        } catch (error) {
            return `Error reading file: ${error.message}`;
        }
    }

    /**
     * Weak cryptographic practices (CWE-327)
     */
    hashPassword(password) {
        // Using weak MD5 hash
        return crypto.createHash('md5').update(password).digest('hex');
    }

    /**
     * Insecure random number generation (CWE-338)
     */
    generateSessionToken() {
        // Using predictable Math.random for security tokens
        return Math.random().toString(36).substring(2);
    }

    /**
     * Code injection through eval (CWE-94)
     */
    calculateUserExpression(expression) {
        try {
            // Directly evaluating user input
            const result = eval(expression);
            return result;
        } catch (error) {
            return `Calculation error: ${error.message}`;
        }
    }

    /**
     * XML External Entity (XXE) vulnerability
     */
    parseXMLData(xmlString) {
        // Vulnerable XML parsing (conceptual)
        try {
            // This would be vulnerable if using a real XML parser without security settings
            console.log(`Parsing XML: ${xmlString}`);
            return xmlString;
        } catch (error) {
            return `XML parsing error: ${error.message}`;
        }
    }

    /**
     * Open redirect vulnerability (CWE-601)
     */
    redirectUser(url) {
        // Redirecting to user-controlled URL without validation
        return `<script>window.location.href='${url}';</script>`;
    }

    /**
     * Cross-Site Scripting (XSS) vulnerability
     */
    displayUserContent(userContent) {
        // Directly inserting user content without sanitization
        return `<div>${userContent}</div>`;
    }

    /**
     * Information disclosure through error messages
     */
    authenticateUser(username, password) {
        try {
            // Simulating database error
            throw new Error(`Database connection failed: host=db.internal.com, user=admin, pass=${this.dbPassword}`);
        } catch (error) {
            // Exposing sensitive information in error messages
            return `Authentication failed: ${error.message}`;
        }
    }

    /**
     * Insecure direct object reference
     */
    getUserProfile(userId) {
        // No authorization check - any user can access any profile
        return `Profile data for user ${userId}: ${this.getPrivateUserData(userId)}`;
    }

    getPrivateUserData(userId) {
        return `Private data for user ${userId}: SSN, credit cards, etc.`;
    }

    /**
     * Weak authentication mechanism
     */
    isValidUser(username, password) {
        // Storing passwords in plain text
        const users = {
            'admin': 'admin',
            'user': 'password',
            'test': '123456'
        };

        // Simple comparison without proper hashing
        return users[username] === password;
    }

    /**
     * Insecure file upload
     */
    uploadFile(filename, content) {
        // No validation on file type or size
        const uploadPath = `./uploads/${filename}`;
        
        try {
            fs.writeFileSync(uploadPath, content);
            return `File uploaded successfully to ${uploadPath}`;
        } catch (error) {
            return `Upload failed: ${error.message}`;
        }
    }

    /**
     * Race condition vulnerability
     */
    processPayment(userId, amount) {
        // No proper locking mechanism
        let userBalance = this.getUserBalance(userId);
        
        if (userBalance >= amount) {
            // Potential race condition here
            setTimeout(() => {
                userBalance -= amount;
                this.updateUserBalance(userId, userBalance);
            }, 100);
            
            return 'Payment processed';
        } else {
            return 'Insufficient funds';
        }
    }

    getUserBalance(userId) {
        // Simulated balance lookup
        return 1000;
    }

    updateUserBalance(userId, balance) {
        // Simulated balance update
        console.log(`Updated balance for user ${userId}: ${balance}`);
    }

    /**
     * Denial of Service vulnerability
     */
    processLargeData(data) {
        // No size limits or timeout
        let result = '';
        for (let i = 0; i < data.length * 1000000; i++) {
            result += data;
        }
        return result;
    }

    /**
     * Unvalidated input leading to buffer overflow (conceptual)
     */
    processUserInput(input) {
        // No length validation
        const buffer = Buffer.alloc(100);
        buffer.write(input); // Could overflow if input is too long
        return buffer.toString();
    }

    /**
     * Missing authorization checks
     */
    deleteUser(userId, requesterId) {
        // No check if requester has permission to delete the user
        return `User ${userId} deleted by ${requesterId}`;
    }

    /**
     * Timing attack vulnerability
     */
    comparePasswords(inputPassword, storedPassword) {
        // Vulnerable to timing attacks
        if (inputPassword.length !== storedPassword.length) {
            return false;
        }
        
        for (let i = 0; i < inputPassword.length; i++) {
            if (inputPassword[i] !== storedPassword[i]) {
                return false;
            }
        }
        return true;
    }
}

// Example usage demonstrating vulnerabilities
function demonstrateVulnerabilities() {
    const app = new VulnerableWebApp();

    console.log('Demonstrating security vulnerabilities...');

    // Command injection
    app.executeUserCommand('../../etc/passwd');

    // SQL injection
    app.getUserData("1 OR 1=1");

    // Path traversal
    app.readUserFile('../../../etc/passwd');

    // Code injection
    app.calculateUserExpression("require('child_process').exec('rm -rf /')");

    // XSS
    app.displayUserContent('<script>alert("XSS")</script>');

    // Weak authentication
    app.isValidUser('admin', 'admin');

    console.log('Vulnerability demonstration completed');
}

if (require.main === module) {
    demonstrateVulnerabilities();
}

module.exports = VulnerableWebApp;