"""
Test file with potential security issues that should be detected by pre-commit hooks.
This file contains private keys and secrets for testing detection capabilities.
"""

# Fake private keys for testing detection
PRIVATE_KEY_RSA = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN
OPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOP
QRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQR
STUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRST
UVWXYZ1234567890abcdefghijklmnopqrstuvwxyz
-----END RSA PRIVATE KEY-----"""

# Fake API keys
API_KEY = "sk-1234567890abcdefghijklmnopqrstuvwxyz123456"
STRIPE_KEY = "sk_live_1234567890abcdefghijklmnopqrstuvwxyz"
AWS_ACCESS_KEY = "AKIA1234567890ABCDEF"
AWS_SECRET_KEY = "abcdefghijklmnopqrstuvwxyz1234567890ABCDEF"

# Database credentials
DATABASE_URL = "postgresql://admin:password123@localhost:5432/testdb"
MONGODB_URI = "mongodb://root:secretpassword@localhost:27017/myapp"

# JWT secrets
JWT_SECRET = "my-super-secret-jwt-key-that-should-not-be-hardcoded"
ENCRYPTION_KEY = "ThisIsAVerySecretEncryptionKey123456"

# OAuth secrets
GITHUB_CLIENT_SECRET = "abcdef1234567890abcdef1234567890abcdef12"
GOOGLE_CLIENT_SECRET = "GOCSPX-1234567890abcdefghijklmnopqrstuvwx"

# Other sensitive information
PASSWORD = "admin123"
SECRET_TOKEN = "secret-token-12345"
WEBHOOK_SECRET = "whsec_1234567890abcdefghijklmnopqrstuvwxyz"

def main():
    print("This file contains hardcoded secrets for testing detection")

if __name__ == "__main__":
    main()