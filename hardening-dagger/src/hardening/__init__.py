"""
Hardening - Security scanning pipeline that runs anywhere.

Usage:
    dagger call scan --source . --scanners all
    dagger call scan --source . --scanners "bandit,gitleaks" --severity-threshold high
"""

from main import Hardening

__all__ = ["Hardening"]
