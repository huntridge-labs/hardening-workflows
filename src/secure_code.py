"""
Secure Python code that should pass SAST analysis.
This file demonstrates security best practices.
"""
import os
import secrets
import hashlib
import logging
from pathlib import Path

# Configure secure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SecureDataHandler:
    """Secure data handler with proper input validation and sanitization."""
    
    def __init__(self):
        self.salt = secrets.token_bytes(32)
    
    def hash_password(self, password: str) -> str:
        """Securely hash a password using PBKDF2."""
        if not isinstance(password, str) or len(password) < 8:
            raise ValueError("Password must be a string with at least 8 characters")
        
        # Use a secure hash function with salt
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            self.salt,
            100000  # Number of iterations
        )
        return password_hash.hex()
    
    def validate_file_path(self, file_path: str) -> Path:
        """Validate and sanitize file path to prevent path traversal."""
        if not isinstance(file_path, str):
            raise ValueError("File path must be a string")
        
        # Use pathlib for secure path handling
        path = Path(file_path).resolve()
        
        # Ensure the path is within allowed directory
        allowed_base = Path("/tmp/secure_uploads").resolve()
        try:
            path.relative_to(allowed_base)
        except ValueError:
            raise ValueError("Path traversal attempt detected")
        
        return path
    
    def read_config_securely(self, config_name: str) -> str:
        """Read configuration with proper validation."""
        # Validate input
        if not isinstance(config_name, str) or not config_name.isalnum():
            raise ValueError("Invalid configuration name")
        
        # Use environment variables for sensitive config
        config_value = os.environ.get(f"SECURE_{config_name.upper()}")
        if config_value is None:
            logger.warning(f"Configuration {config_name} not found")
            return ""
        
        return config_value
    
    def sanitize_user_input(self, user_input: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        if not isinstance(user_input, str):
            raise ValueError("Input must be a string")
        
        # Remove potentially dangerous characters
        safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ._-")
        sanitized = ''.join(char for char in user_input if char in safe_chars)
        
        # Limit length to prevent DoS
        return sanitized[:100]


def main():
    """Main function demonstrating secure coding practices."""
    handler = SecureDataHandler()
    
    # Example usage
    try:
        # Secure password handling
        test_password = "SecurePassword123!"
        hashed = handler.hash_password(test_password)
        logger.info("Password hashed successfully")
        
        # Secure file path validation
        safe_path = handler.validate_file_path("/tmp/secure_uploads/data.txt")
        logger.info(f"Validated path: {safe_path}")
        
        # Secure config reading
        config = handler.read_config_securely("database_url")
        logger.info("Configuration read securely")
        
        # Input sanitization
        user_input = "Hello World! This is a test."
        sanitized = handler.sanitize_user_input(user_input)
        logger.info(f"Sanitized input: {sanitized}")
        
    except Exception as e:
        logger.error(f"Error in secure operations: {e}")


if __name__ == "__main__":
    main()