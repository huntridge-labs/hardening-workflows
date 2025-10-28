#!/usr/bin/env node
/**
 * Post-process changelog to categorize chore(deps) commits
 *
 * This script:
 * 1. Reads the generated CHANGELOG.md
 * 2. Identifies chore(deps) commits that update security scanners
 * 3. Moves them to a "Security Tools" section
 * 4. Moves other chore(deps) to "Dependencies" section
 * 5. Keeps other chore commits in "Maintenance"
 */

const fs = require('fs');
const path = require('path');

// Security scanner patterns to detect in commit messages
const securityScannerPatterns = [
  'bridgecrewio/checkov-action',
  'checkov-action',
  'checkov',
  'aquasecurity/trivy-action',
  'trivy-action',
  'trivy',
  'anchore/sbom-action',
  'sbom-action',
  'syft',
  'clamav',
  'snyk',
  'grype',
  'osv-scanner',
  'semgrep',
  'bandit',
  'safety',
  'gitleaks',
  'trufflehog',
  'detect-secrets'
];

function isSecurityScanner(commitText) {
  const lowerText = commitText.toLowerCase();
  return securityScannerPatterns.some(pattern =>
    lowerText.includes(pattern.toLowerCase())
  );
}

function processChangelog() {
  const changelogPath = path.join(process.cwd(), 'CHANGELOG.md');

  if (!fs.existsSync(changelogPath)) {
    console.log('CHANGELOG.md not found, skipping processing');
    return;
  }

  let content = fs.readFileSync(changelogPath, 'utf8');

  // Find the Maintenance section and extract chore commits
  // Match "### Maintenance" followed by commits starting with "*"
  const maintenancePattern = /### Maintenance\n\n((?:\* .*\n?)+)/g;
  const matches = [...content.matchAll(maintenancePattern)];

  if (matches.length === 0) {
    console.log('No Maintenance section found');
    return;
  }

  // Process each Maintenance section (there may be multiple versions)
  matches.forEach(match => {
    const maintenanceSection = match[1];
    const commits = maintenanceSection.match(/^\* .+$/gm) || [];

    const securityToolCommits = [];
    const dependencyCommits = [];
    const maintenanceCommits = [];

    commits.forEach(commit => {
      // Check if it's a deps commit by looking for (deps) or bump patterns
      const isDepsCommit = /\(deps\)|bump .* from .* to/i.test(commit);

      if (isDepsCommit) {
        if (isSecurityScanner(commit)) {
          securityToolCommits.push(commit);
        } else {
          dependencyCommits.push(commit);
        }
      } else {
        maintenanceCommits.push(commit);
      }
    });

    // Build replacement sections
    let replacement = '';

    if (securityToolCommits.length > 0) {
      replacement += '### Security Tools\n\n';
      replacement += securityToolCommits.join('\n') + '\n\n';
    }

    if (dependencyCommits.length > 0) {
      replacement += '### Dependencies\n\n';
      replacement += dependencyCommits.join('\n') + '\n\n';
    }

    if (maintenanceCommits.length > 0) {
      replacement += '### Maintenance\n\n';
      replacement += maintenanceCommits.join('\n') + '\n\n';
    }

    // Replace the original Maintenance section
    content = content.replace(match[0], replacement.trim() + '\n\n');
  });

  // Write back
  fs.writeFileSync(changelogPath, content);
  console.log('✓ Processed CHANGELOG.md - categorized dependency updates');
}

// Run if called directly
if (require.main === module) {
  processChangelog();
}

module.exports = { processChangelog };
