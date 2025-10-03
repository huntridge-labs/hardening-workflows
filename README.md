# Security Hardening Workflows

This repository provides a comprehensive security hardening pipeline for modern software development. It includes both test files for validation and **reusable workflows** that can be easily integrated into other projects.

## 🚀 Quick Start - Reuse This Pipeline

**Want to use this security pipeline in your project?** You don't need to copy-paste anything!

```yaml
# Add this to your .github/workflows/security.yml
name: Security Pipeline
on: [push, pull_request]

jobs:
  # Optional: Run code quality checks
  linting:
    uses: huntridge-labs/hardening-workflows/.github/workflows/linting.yml@main
    permissions:
      contents: read
      pull-requests: write
      checks: write

  # Required: Run security hardening
  security:
    needs: linting  # Optional: wait for linting
    if: always()    # Run even if linting fails
    uses: huntridge-labs/hardening-workflows/.github/workflows/reusable-security-hardening.yml@main
    with:
      scan_type: 'full'
      python_version: '3.11'
    secrets:
      AWS_ACCOUNT_ID: ${{ secrets.AWS_ACCOUNT_ID }}
    permissions:
      contents: read
      security-events: write
      pull-requests: write
```

**That's it!** You now have linting + security scanning. 📖 [See full documentation](docs/reusing-workflows.md)

## 📋 Table of Contents

1. [Reusing This Pipeline](#-reusing-this-pipeline)
2. [Test Files Structure](#test-files-structure)
3. [Security Features](#-security-features)
4. [Example Outputs](#-example-outputs)
5. [Contributing](#-contributing)

## 🔄 Reusing This Pipeline

### Three Ways to Reuse:

1. **Reusable Workflow** (Recommended) - Call our workflow from your repo
2. **Composite Actions** - Use individual security tools
3. **Workflow Templates** - Organization-wide standards

👉 **[Complete Reuse Guide](docs/reusing-workflows.md)**

## Directory Structure

```
hardening-workflows/
├── src/                    # Source code files
├── config/                 # Configuration files
├── docker/                 # Container definitions
├── infrastructure/         # Infrastructure as Code
├── tests/                  # Test files
└── README.md              # This file
```

## Test File Categories

### ✅ Files That Should PASS Security Checks

#### Python Files
- **`src/secure_code.py`** - Demonstrates secure coding practices:
  - Proper input validation and sanitization
  - Secure password hashing with PBKDF2
  - Path traversal prevention
  - Environment variable usage for secrets
  - Proper exception handling
  - Secure logging practices

#### JavaScript Files
- **`src/secure_app.js`** - Secure Node.js application:
  - Parameterized database queries
  - Strong cryptographic practices
  - Input validation and sanitization
  - CORS validation
  - Rate limiting implementation
  - Secure session management

#### Configuration Files
- **`config/valid-config.yml`** - Well-formed YAML configuration:
  - Proper indentation and formatting
  - Environment variable references for secrets
  - Secure default settings
  - Valid YAML syntax

#### Container Files
- **`docker/Dockerfile.secure`** - Secure container configuration:
  - Multi-stage builds
  - Non-root user execution
  - Minimal attack surface
  - Security updates applied
  - Health checks implemented

#### Infrastructure Files
- **`infrastructure/secure.tf`** - Secure Terraform configuration:
  - Provider version pinning
  - Encrypted storage
  - Private networking
  - Principle of least privilege
  - Input validation

#### Test Files
- **`tests/valid.json`** - Valid JSON configuration
- **`tests/clean_test.py`** - Clean Python code following best practices

### ❌ Files That Should FAIL Security Checks

#### Python Files
- **`src/vulnerable_code.py`** - Contains multiple security vulnerabilities:
  - Command injection (CWE-78)
  - SQL injection (CWE-89)
  - Path traversal (CWE-22)
  - Hard-coded credentials (CWE-798)
  - Weak cryptography (CWE-327)
  - Code injection via eval() (CWE-94)
  - Unsafe deserialization (CWE-502)
  - Information disclosure
  - Insecure file operations

#### JavaScript Files
- **`src/vulnerable_app.js`** - Vulnerable Node.js application:
  - Command injection
  - SQL injection vulnerabilities
  - XSS vulnerabilities
  - Hard-coded secrets
  - Weak authentication
  - Path traversal issues
  - Insecure random generation
  - Missing authorization checks

#### Configuration Files
- **`config/invalid-config.yml`** - YAML with multiple issues:
  - Syntax errors
  - Hard-coded credentials
  - Insecure configurations
  - Inconsistent formatting
  - Line length violations
  - Trailing whitespace

#### Container Files
- **`docker/Dockerfile.vulnerable`** - Insecure container:
  - Outdated base images
  - Running as root user
  - Hard-coded secrets
  - Unnecessary exposed ports
  - Insecure package installations
  - Missing security updates

#### Infrastructure Files
- **`infrastructure/vulnerable.tf`** - Insecure Terraform:
  - Hard-coded credentials
  - Overly permissive security groups
  - Public access configurations
  - Unencrypted storage
  - Outdated resource versions
  - Excessive IAM permissions

#### Test Files
- **`tests/invalid.json`** - Invalid JSON with syntax errors
- **`tests/secrets_test.py`** - Contains hard-coded secrets and API keys
- **`tests/formatting_issues.txt`** - File with formatting problems

## Security Tools That Should Detect Issues

### 1. SAST (Static Application Security Testing)
- **CodeQL** - Should detect vulnerabilities in Python and JavaScript files
- **Target files**: `src/vulnerable_code.py`, `src/vulnerable_app.js`

### 2. Pre-commit Hooks
- **Trailing whitespace detection** - `tests/formatting_issues.txt`
- **JSON validation** - `tests/invalid.json`
- **Private key detection** - `tests/secrets_test.py`
- **Python syntax checking** - All `.py` files

### 3. YAML Linting
- **yamllint** - Should catch issues in `config/invalid-config.yml`
- **Valid YAML** - Should pass `config/valid-config.yml`

### 4. Container Scanning
- **Container security scanners** - Should flag `docker/Dockerfile.vulnerable`
- **Secure containers** - Should pass `docker/Dockerfile.secure`

### 5. Infrastructure Security
- **Terraform security scanners** - Should detect issues in `infrastructure/vulnerable.tf`
- **Secure IaC** - Should validate `infrastructure/secure.tf`

## Expected Pipeline Behavior

### Passing Tests
Files in the "pass" category should:
- ✅ Pass SAST analysis without high/critical findings
- ✅ Pass pre-commit hook validations
- ✅ Pass YAML linting
- ✅ Pass container security scans
- ✅ Pass infrastructure security checks

### Failing Tests
Files in the "fail" category should:
- ❌ Trigger SAST alerts with specific vulnerability types
- ❌ Fail pre-commit hooks for various reasons
- ❌ Fail YAML linting with syntax/format errors
- ❌ Fail container scans with security findings
- ❌ Fail infrastructure security with misconfigurations

## Usage Instructions

### Running Individual Checks

1. **SAST Analysis**:
   ```bash
   # CodeQL analysis will run automatically on push/PR
   # Check .github/workflows/sast.yml for configuration
   ```

2. **Pre-commit Hooks**:
   ```bash
   pre-commit run --all-files
   ```

3. **YAML Linting**:
   ```bash
   yamllint config/
   ```

4. **Container Scanning**:
   ```bash
   # Build and scan containers
   docker build -f docker/Dockerfile.secure -t secure-app .
   docker build -f docker/Dockerfile.vulnerable -t vulnerable-app .
   ```

### AWS Configuration (Optional)

The security hardening pipeline includes optional AWS security analysis. **This is not required** - the pipeline works perfectly without AWS components.

#### If you want to enable AWS security analysis:

1. **Set up AWS OIDC Role** for your repository:
   - Create an IAM role with trust policy for your GitHub repository
   - Grant necessary read permissions for security analysis

2. **Update the workflow environment variables** in `.github/workflows/security-hardening.yml`:
   ```yaml
   env:
     AWS_ACCOUNT_ID: YOUR_ACCOUNT_ID  # Replace with your AWS account ID
     AWS_REGION: us-east-1           # Replace with your preferred region
   ```

3. **Required permissions** for the AWS role:
   - `s3:ListAllMyBuckets`
   - `iam:ListRoles`
   - `lambda:ListFunctions`
   - `sts:GetCallerIdentity`

#### If you don't need AWS analysis:
- The pipeline will automatically detect missing AWS credentials
- All other security scans will continue normally
- A report will be generated explaining the AWS analysis was skipped

### Testing the Pipeline

1. **Create a test branch**:
   ```bash
   git checkout -b test-security-pipeline
   ```

2. **Commit changes to trigger workflows**:
   ```bash
   git add .
   git commit -m "test: add security test files"
   git push origin test-security-pipeline
   ```

3. **Create a pull request** to trigger all security checks

4. **Review the results** in GitHub Actions and security tabs

## Vulnerability Reference

| File | Vulnerability Type | CWE | CVSS | Tool Detection |
|------|-------------------|-----|------|----------------|
| `vulnerable_code.py` | Command Injection | CWE-78 | High | CodeQL |
| `vulnerable_code.py` | SQL Injection | CWE-89 | High | CodeQL |
| `vulnerable_code.py` | Hard-coded Credentials | CWE-798 | Medium | SAST/Pre-commit |
| `vulnerable_app.js` | XSS | CWE-79 | Medium | CodeQL |
| `secrets_test.py` | Exposed Secrets | CWE-798 | High | Pre-commit hooks |
| `vulnerable.tf` | Insecure Configuration | CWE-16 | Medium | IaC scanners |

## Contributing

When adding new test files:

1. **Document the expected behavior** (pass/fail)
2. **Specify which tools should detect issues**
3. **Include vulnerability references** (CWE, CVSS if applicable)
4. **Test both positive and negative cases**
5. **Update this README** with new file descriptions

## Security Notice

⚠️ **WARNING**: The files in this repository contain intentionally vulnerable code and configurations for testing purposes only. **DO NOT** use any of the "vulnerable" examples in production environments.

## License

This project is intended for educational and testing purposes. Please ensure compliance with your organization's security policies when using these test files.
