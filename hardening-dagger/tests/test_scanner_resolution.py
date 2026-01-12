"""Tests for scanner resolution logic."""

import pytest


# Import the scanner groups and resolution logic
# Note: These tests run without Dagger context, testing pure Python logic
SCANNERS = {
    "bandit", "gitleaks", "trivy-iac", "trivy-container",
    "checkov", "grype", "opengrep", "clamav", "codeql", "zap"
}

SCANNER_GROUPS = {
    "all": {"bandit", "gitleaks", "trivy-iac", "checkov", "grype", "opengrep"},
    "full": {"bandit", "gitleaks", "trivy-iac", "checkov", "grype", "opengrep", "codeql", "clamav"},
    "sast": {"bandit", "opengrep", "gitleaks", "codeql"},
    "secrets": {"gitleaks"},
    "iac": {"trivy-iac", "checkov"},
    "container": {"trivy-container", "grype"},
    "dast": {"zap"},
}


def resolve_scanners(scanners: str) -> set[str]:
    """Resolve scanner selection string to set of scanner names."""
    selected = set()

    for token in scanners.lower().replace(" ", "").split(","):
        token = token.strip()

        if token in SCANNER_GROUPS:
            selected.update(SCANNER_GROUPS[token])
        elif token in SCANNERS:
            selected.add(token)
        elif token in ("semgrep", "sast-scanner"):
            selected.add("opengrep")
        elif token in ("secrets-scanner", "secret"):
            selected.add("gitleaks")
        elif token in ("terraform", "infra"):
            selected.update(SCANNER_GROUPS["iac"])
        elif token in ("code-ql", "codeql-sast"):
            selected.add("codeql")
        elif token in ("zap-dast", "owasp-zap", "zaproxy"):
            selected.add("zap")

    return selected


class TestScannerResolution:
    """Tests for scanner string resolution."""

    def test_all_group(self):
        """Test 'all' expands to default scanners."""
        result = resolve_scanners("all")
        assert result == {"bandit", "gitleaks", "trivy-iac", "checkov", "grype", "opengrep"}
        # CodeQL and ZAP should NOT be in 'all'
        assert "codeql" not in result
        assert "zap" not in result

    def test_full_group(self):
        """Test 'full' includes CodeQL and ClamAV."""
        result = resolve_scanners("full")
        assert "codeql" in result
        assert "clamav" in result
        assert "zap" not in result  # DAST still opt-in

    def test_sast_group(self):
        """Test 'sast' includes CodeQL."""
        result = resolve_scanners("sast")
        assert result == {"bandit", "opengrep", "gitleaks", "codeql"}

    def test_dast_group(self):
        """Test 'dast' includes ZAP."""
        result = resolve_scanners("dast")
        assert result == {"zap"}

    def test_individual_scanner(self):
        """Test specifying individual scanners."""
        result = resolve_scanners("bandit")
        assert result == {"bandit"}

    def test_multiple_scanners(self):
        """Test comma-separated scanners."""
        result = resolve_scanners("bandit,gitleaks,trivy-iac")
        assert result == {"bandit", "gitleaks", "trivy-iac"}

    def test_mixed_groups_and_scanners(self):
        """Test mixing groups and individual scanners."""
        result = resolve_scanners("sast,zap")
        assert "bandit" in result
        assert "codeql" in result
        assert "zap" in result

    def test_aliases(self):
        """Test scanner aliases."""
        assert "opengrep" in resolve_scanners("semgrep")
        assert "gitleaks" in resolve_scanners("secrets-scanner")
        assert "trivy-iac" in resolve_scanners("terraform")
        assert "codeql" in resolve_scanners("code-ql")
        assert "zap" in resolve_scanners("owasp-zap")

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert resolve_scanners("BANDIT") == resolve_scanners("bandit")
        assert resolve_scanners("ALL") == resolve_scanners("all")

    def test_whitespace_handling(self):
        """Test whitespace is ignored."""
        result = resolve_scanners("bandit, gitleaks , trivy-iac")
        assert result == {"bandit", "gitleaks", "trivy-iac"}

    def test_unknown_scanner(self):
        """Test unknown scanners are ignored."""
        result = resolve_scanners("bandit,unknown,gitleaks")
        assert result == {"bandit", "gitleaks"}

    def test_empty_string(self):
        """Test empty string returns empty set."""
        result = resolve_scanners("")
        assert result == set()
