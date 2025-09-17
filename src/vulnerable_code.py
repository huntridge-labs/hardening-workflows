"""
Vulnerable Python code that should fail SAST analysis.
This file contains multiple security vulnerabilities for testing purposes.
WARNING: This code is intentionally insecure - DO NOT USE IN PRODUCTION!
"""
import os
import subprocess
import sqlite3
import hashlib
import pickle
import urllib.request


class VulnerableCode:
    """Class containing various security vulnerabilities."""
    
    def __init__(self):
        # Hard-coded credentials (CWE-798)
        self.api_key = "sk-1234567890abcdef"  # Hardcoded API key
        self.password = "admin123"            # Hardcoded password
        self.db_connection = "mysql://root:password@localhost/db"  # Hardcoded DB credentials
    
    def execute_command(self, user_input):
        """Command injection vulnerability (CWE-78)."""
        # Directly executing user input without validation
        command = f"ls {user_input}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout
    
    def sql_query(self, user_id):
        """SQL injection vulnerability (CWE-89)."""
        # Building SQL query with string concatenation
        conn = sqlite3.connect("vulnerable.db")
        cursor = conn.cursor()
        
        # Vulnerable SQL query construction
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute(query)
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def weak_crypto(self, data):
        """Weak cryptographic practices (CWE-327)."""
        # Using weak hash algorithm
        md5_hash = hashlib.md5(data.encode()).hexdigest()
        
        # Using insecure random for cryptographic purposes
        import random
        weak_salt = str(random.randint(1000, 9999))
        
        return md5_hash + weak_salt
    
    def path_traversal(self, filename):
        """Path traversal vulnerability (CWE-22)."""
        # No validation on file path
        file_path = f"/var/www/uploads/{filename}"
        
        try:
            with open(file_path, 'r') as file:
                return file.read()
        except FileNotFoundError:
            return "File not found"
    
    def unsafe_deserialization(self, data):
        """Unsafe deserialization (CWE-502)."""
        # Deserializing untrusted data with pickle
        return pickle.loads(data)
    
    def weak_authentication(self, username, password):
        """Weak authentication mechanism."""
        # Storing passwords in plain text
        users = {
            "admin": "admin123",
            "user": "password",
            "test": "test"
        }
        
        # Simple comparison without proper hashing
        if username in users and users[username] == password:
            return True
        return False
    
    def insecure_random(self):
        """Using insecure random for security purposes."""
        import random
        
        # Using predictable random for session tokens
        session_token = str(random.randint(100000, 999999))
        return session_token
    
    def unvalidated_redirect(self, url):
        """Open redirect vulnerability (CWE-601)."""
        # Redirecting to user-controlled URL without validation
        return f"<script>window.location.href='{url}';</script>"
    
    def file_inclusion(self, page):
        """Local file inclusion vulnerability."""
        # Including files based on user input
        file_path = f"pages/{page}.php"
        try:
            with open(file_path, 'r') as file:
                return file.read()
        except FileNotFoundError:
            return "Page not found"
    
    def xxe_vulnerability(self, xml_data):
        """XML External Entity (XXE) vulnerability."""
        import xml.etree.ElementTree as ET
        
        # Parsing XML without disabling external entities
        try:
            root = ET.fromstring(xml_data)
            return ET.tostring(root, encoding='unicode')
        except ET.ParseError:
            return "Invalid XML"
    
    def information_disclosure(self):
        """Information disclosure through error messages."""
        try:
            # Intentionally cause an error
            result = 1 / 0
        except Exception as e:
            # Exposing sensitive information in error messages
            return f"Database connection failed: {self.db_connection}, Error: {str(e)}"
    
    def csrf_vulnerability(self, action):
        """Cross-Site Request Forgery vulnerability."""
        # Performing sensitive actions without CSRF protection
        if action == "delete_user":
            return "User deleted successfully"
        elif action == "transfer_money":
            return "Money transferred"
        else:
            return "Unknown action"
    
    def insecure_file_upload(self, filename, content):
        """Insecure file upload allowing dangerous file types."""
        # No validation on file type or content
        upload_path = f"/var/www/uploads/{filename}"
        
        with open(upload_path, 'w') as file:
            file.write(content)
        
        return f"File uploaded to {upload_path}"
    
    def eval_injection(self, user_expression):
        """Code injection through eval (CWE-94)."""
        # Directly evaluating user input
        try:
            result = eval(user_expression)
            return str(result)
        except Exception as e:
            return f"Error: {e}"


def main():
    """Main function demonstrating vulnerable code."""
    vuln = VulnerableCode()
    
    # Example usage of vulnerable functions
    print("Testing vulnerable code...")
    
    # Command injection
    vuln.execute_command("../../etc/passwd")
    
    # SQL injection
    vuln.sql_query("1 OR 1=1")
    
    # Weak crypto
    vuln.weak_crypto("sensitive data")
    
    # Path traversal
    vuln.path_traversal("../../../etc/passwd")
    
    # Code injection
    vuln.eval_injection("__import__('os').system('rm -rf /')")
    
    print("Vulnerable operations completed")


if __name__ == "__main__":
    main()