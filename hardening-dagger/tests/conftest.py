"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_python_code() -> str:
    """Sample Python code with security issues for testing."""
    return """
import os
import subprocess

# Bandit: B602 - subprocess with shell=True
def run_command(cmd):
    subprocess.call(cmd, shell=True)

# Bandit: B105 - hardcoded password
PASSWORD = "secret123"

# Bandit: B301 - pickle usage
import pickle
def load_data(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)
"""


@pytest.fixture
def sample_terraform_code() -> str:
    """Sample Terraform code with misconfigurations for testing."""
    return """
# Trivy/Checkov: S3 bucket without encryption
resource "aws_s3_bucket" "insecure" {
  bucket = "my-insecure-bucket"
  acl    = "public-read"
}

# Missing encryption configuration
resource "aws_ebs_volume" "unencrypted" {
  availability_zone = "us-east-1a"
  size              = 40
  # encrypted = true  # Missing!
}
"""


@pytest.fixture
def sample_secrets_code() -> str:
    """Sample code with hardcoded secrets for testing."""
    return '''
# Gitleaks should detect these
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# API key pattern
api_key = "sk-1234567890abcdef1234567890abcdef"

# Private key
private_key = """
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGy...
-----END RSA PRIVATE KEY-----
"""
'''
