#!/usr/bin/env node

/**
 * Enhanced PR Comment Generator
 *
 * This script demonstrates how to transform verbose security reports
 * into user-friendly, actionable PR comments with better UX.
 */

const fs = require('fs');

/**
 * Parse SAST summary report and extract key metrics
 */
function parseSASTReport(reportContent) {
  const data = {
    tools: [],
    totalCritical: 0,
    totalHigh: 0,
    totalMedium: 0,
    totalLow: 0
  };

  // Extract tool results table
  const tableMatch = reportContent.match(/\| Tool \| Critical \| High \| Medium \| Low \| Total \| Status \|(.*?)(?=\n\n|\n\|)/s);
  if (tableMatch) {
    const rows = tableMatch[1].split('\n').filter(row => row.includes('|'));

    rows.forEach(row => {
      const parts = row.split('|').map(p => p.trim()).filter(p => p);
      if (parts.length >= 7 && parts[0] !== '---') {
        const tool = {
          name: parts[0],
          critical: parseInt(parts[1]) || 0,
          high: parseInt(parts[2]) || 0,
          medium: parseInt(parts[3]) || 0,
          low: parseInt(parts[4]) || 0,
          total: parseInt(parts[5]) || 0,
          status: parts[6]
        };

        // Skip total row
        if (!parts[0].includes('TOTAL')) {
          data.tools.push(tool);
          data.totalCritical += tool.critical;
          data.totalHigh += tool.high;
          data.totalMedium += tool.medium;
          data.totalLow += tool.low;
        }
      }
    });
  }

  return data;
}

/**
 * Parse Container security report and extract key metrics
 */
function parseContainerReport(reportContent) {
  const data = {
    containers: [],
    totalCritical: 0,
    totalHigh: 0,
    totalMedium: 0,
    totalLow: 0,
    scannedContainers: 0,
    buildFailures: 0
  };

  // Extract totals from TOTAL row
  const totalMatch = reportContent.match(/\| \*\*TOTAL\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* \|/);
  if (totalMatch) {
    data.totalCritical = parseInt(totalMatch[1]) || 0;
    data.totalHigh = parseInt(totalMatch[2]) || 0;
    data.totalMedium = parseInt(totalMatch[3]) || 0;
    data.totalLow = parseInt(totalMatch[4]) || 0;
  }

  // Extract scan overview
  const scanMatch = reportContent.match(/\| Containers Scanned \| (\d+) \|.*?\| Build Failures \| (\d+) \|/s);
  if (scanMatch) {
    data.scannedContainers = parseInt(scanMatch[1]) || 0;
    data.buildFailures = parseInt(scanMatch[2]) || 0;
  }

  // Extract individual container results from the vulnerability table
  const tableMatch = reportContent.match(/\| Container \| Critical \| High \| Medium \| Low \| Total \| Build Status \|(.*?)(?=\| \*\*TOTAL\*\*)/s);
  if (tableMatch) {
    const rows = tableMatch[1].split('\n').filter(row => row.includes('|') && !row.includes('---'));

    rows.forEach(row => {
      const parts = row.split('|').map(p => p.trim()).filter(p => p);
      if (parts.length >= 7) {
        const containerName = parts[0];
        const buildStatus = parts[6];

        // Check if this is a successful build with vulnerability data
        if (buildStatus.includes('Success') && parts[1] !== '-') {
          const container = {
            name: containerName,
            critical: parseInt(parts[1]) || 0,
            high: parseInt(parts[2]) || 0,
            medium: parseInt(parts[3]) || 0,
            low: parseInt(parts[4]) || 0,
            total: parseInt(parts[5]) || 0,
            buildStatus: 'success'
          };
          data.containers.push(container);
        } else if (buildStatus.includes('Failed')) {
          data.containers.push({
            name: containerName,
            buildStatus: 'failed'
          });
        }
      }
    });
  }

  return data;
}

/**
 * Determine risk level based on vulnerability counts
 */
function getRiskLevel(critical, high) {
  if (critical > 0) return 'CRITICAL';
  if (high > 5) return 'HIGH';
  if (high > 0) return 'MODERATE';
  return 'LOW';
}

/**
 * Get risk badge markdown
 */
function getRiskBadge(riskLevel) {
  const badges = {
    'CRITICAL': '![Critical](https://img.shields.io/badge/Risk-CRITICAL-red)',
    'HIGH': '![High](https://img.shields.io/badge/Risk-HIGH-orange)',
    'MODERATE': '![Moderate](https://img.shields.io/badge/Risk-MODERATE-yellow)',
    'LOW': '![Low](https://img.shields.io/badge/Risk-LOW-green)'
  };
  return badges[riskLevel] || '![Unknown](https://img.shields.io/badge/Risk-UNKNOWN-gray)';
}

/**
 * Generate action items based on vulnerability counts
 */
function generateActionItems(critical, high, medium) {
  const items = [];

  if (critical > 0) {
    items.push(`🚨 **URGENT**: ${critical} critical vulnerabilities need immediate attention`);
  }
  if (high > 0) {
    items.push(`⚠️ **HIGH**: ${high} high-severity vulnerabilities to address within 24h`);
  }
  if (medium > 0) {
    items.push(`🟡 **MEDIUM**: ${medium} medium issues for next sprint`);
  }
  if (critical === 0 && high === 0 && medium === 0) {
    items.push(`✅ **GREAT JOB**: No high-priority security issues found!`);
  }

  return items.join('\n');
}

/**
 * Generate enhanced SAST comment
 */
function generateEnhancedSASTComment(sastData, runId, repoOwner, repoName) {
  const { totalCritical, totalHigh, totalMedium, totalLow, tools } = sastData;
  const totalVulns = totalCritical + totalHigh + totalMedium + totalLow;
  const riskLevel = getRiskLevel(totalCritical, totalHigh);
  const riskEmoji = totalCritical > 0 ? '🚨' : totalHigh > 0 ? '⚠️' : '✅';

  return `## 🔍 SAST Security Analysis ${riskEmoji}

### 📊 Quick Summary
${getRiskBadge(riskLevel)} **Risk Level: ${riskLevel}**

| 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | 📊 Total |
|-------------|---------|-----------|---------|----------|
| **${totalCritical}** | **${totalHigh}** | **${totalMedium}** | **${totalLow}** | **${totalVulns}** |

${generateActionItems(totalCritical, totalHigh, totalMedium)}

### 📥 Quick Access
- 📋 **[Download All SAST Reports](https://github.com/${repoOwner}/${repoName}/actions/runs/${runId}#artifacts)**
- 🔍 **[View in GitHub Security](https://github.com/${repoOwner}/${repoName}/security/code-scanning)**
- ⚙️ **[Configure Dependabot](https://github.com/${repoOwner}/${repoName}/settings/security_analysis)**

<details>
<summary>🛠️ <strong>Tool Results</strong> (${tools.length} tools ran)</summary>

| Tool | Critical | High | Medium | Low | Status |
|------|----------|------|--------|-----|--------|
${tools.map(t => `| ${t.name} | ${t.critical} | ${t.high} | ${t.medium} | ${t.low} | ${t.status} |`).join('\n')}

</details>

<details>
<summary>🚨 <strong>Priority Findings</strong></summary>

${totalCritical > 0 ? `
#### 🚨 Critical Issues (${totalCritical})
- Require immediate attention
- Block deployment until resolved
- [Download detailed reports](https://github.com/${repoOwner}/${repoName}/actions/runs/${runId}#artifacts)
` : ''}

${totalHigh > 0 ? `
#### ⚠️ High Priority Issues (${totalHigh})
- Address within 24 hours
- Review during next development cycle
` : ''}

${totalVulns === 0 ? `
#### ✅ No Security Issues Found
Great work! All SAST tools passed without detecting security vulnerabilities.
` : ''}

</details>

---
*Generated: ${new Date().toLocaleString()} | [View Workflow](https://github.com/${repoOwner}/${repoName}/actions/runs/${runId})*`;
}

/**
 * Generate enhanced Container comment
 */
function generateEnhancedContainerComment(containerData, runId, repoOwner, repoName) {
  const { containers, totalCritical, totalHigh, totalMedium, totalLow, scannedContainers, buildFailures } = containerData;
  const totalVulns = totalCritical + totalHigh + totalMedium + totalLow;
  const riskLevel = getRiskLevel(totalCritical, totalHigh);
  const riskEmoji = totalCritical > 0 ? '🚨' : totalHigh > 0 ? '⚠️' : '✅';

  // Build individual container sections
  let containerSections = '';
  if (containers && containers.length > 0) {
    containerSections = containers.map(container => {
      if (container.buildStatus === 'failed') {
        return `
<details>
<summary>🐳 <strong>${container.name}</strong> - ❌ Build Failed</summary>

**Status:** Build failed - this may be expected for intentionally vulnerable test containers.

**Actions:**
- Review build logs in the [workflow run](https://github.com/${repoOwner}/${repoName}/actions/runs/${runId})
- Check Dockerfile syntax and dependencies

</details>`;
      }

      const containerVulns = container.total || 0;
      const containerRiskEmoji = container.critical > 0 ? '🚨' : container.high > 0 ? '⚠️' : containerVulns > 0 ? '🟡' : '✅';
      const containerRiskLevel = getRiskLevel(container.critical, container.high);

      return `
<details>
<summary>🐳 <strong>${container.name}</strong> - ${containerRiskEmoji} ${containerVulns} vulnerabilities</summary>

### Vulnerability Breakdown
| 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | Total |
|-------------|---------|-----------|---------|-------|
| ${container.critical} | ${container.high} | ${container.medium} | ${container.low} | ${container.total} |

**Risk Level:** ${containerRiskLevel} ${containerRiskEmoji}

${container.critical > 0 ? `
#### 🚨 Critical Issues
- **${container.critical} critical vulnerabilities** require immediate attention
- These should be addressed before deployment
` : ''}

${container.high > 0 ? `
#### ⚠️ High Priority
- **${container.high} high-severity vulnerabilities** found
- Address within 24 hours
` : ''}

${containerVulns === 0 ? `
#### ✅ No Vulnerabilities
Great! This container has no detected vulnerabilities.
` : ''}

**📥 Download Reports:**
- [Trivy SARIF Results](https://github.com/${repoOwner}/${repoName}/actions/runs/${runId}#artifacts)
- [Grype Scan Results](https://github.com/${repoOwner}/${repoName}/actions/runs/${runId}#artifacts)
- [SBOM (CycloneDX)](https://github.com/${repoOwner}/${repoName}/actions/runs/${runId}#artifacts)

</details>`;
    }).join('\n');
  }

  return `## 🐳 Container Security Analysis ${riskEmoji}

### 📊 Overall Summary
${getRiskBadge(riskLevel)} **Risk Level: ${riskLevel}**

| 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | 📦 Total |
|-------------|---------|-----------|---------|----------|
| **${totalCritical}** | **${totalHigh}** | **${totalMedium}** | **${totalLow}** | **${totalVulns}** |

**Scanned:** ${scannedContainers} containers | **Build Failures:** ${buildFailures}

${generateActionItems(totalCritical, totalHigh, totalMedium)}

### 📦 Container Results
${containerSections || 'No container scan results available.'}

### 📥 All Reports
- 📋 **[Download All Container Reports](https://github.com/${repoOwner}/${repoName}/actions/runs/${runId}#artifacts)**
- 🔍 **[View in GitHub Security](https://github.com/${repoOwner}/${repoName}/security/code-scanning)**

<details>
<summary>🛠️ <strong>Remediation Guide</strong></summary>

#### Immediate Actions (Critical/High)
${totalCritical > 0 ? `
- 🚨 **${totalCritical} critical vulnerabilities** across all containers require immediate patching
- 📋 Review individual container reports above for specific issues
- 🔄 Update base images and dependencies
` : ''}
${totalHigh > 0 ? `
- ⚠️ **${totalHigh} high-severity vulnerabilities** should be addressed within 24h
` : ''}

#### Best Practices
- 🐧 Use minimal base images (Alpine, distroless)
- 🏗️ Implement multi-stage builds
- 👤 Run containers as non-root users
- 🔒 Enable GitHub Advanced Security for integrated reporting
- 📦 Regularly update dependencies and base images
- 🔍 Review SBOMs to understand container composition

</details>

---
*Generated: ${new Date().toLocaleString()} | [View Workflow](https://github.com/${repoOwner}/${repoName}/actions/runs/${runId})*`;
}

/**
 * Generate consolidated security overview with advanced UX features
 */
function generateSecurityOverview(sastData, containerData, runId, repoOwner, repoName) {
  const totalCritical = (sastData?.totalCritical || 0) + (containerData?.totalCritical || 0);
  const totalHigh = (sastData?.totalHigh || 0) + (containerData?.totalHigh || 0);
  const totalMedium = (sastData?.totalMedium || 0) + (containerData?.totalMedium || 0);
  const totalLow = (sastData?.totalLow || 0) + (containerData?.totalLow || 0);
  const totalVulns = totalCritical + totalHigh + totalMedium + totalLow;

  const riskLevel = getRiskLevel(totalCritical, totalHigh);
  const riskEmoji = totalCritical > 0 ? '🚨' : totalHigh > 0 ? '⚠️' : '✅';

  // Try to load advanced features
  let advancedFeatures = null;
  try {
    const advanced = require('./advanced-pr-enhancements.js');
    advancedFeatures = advanced;
  } catch (error) {
    // Fallback to basic overview if advanced features not available
  }

  if (advancedFeatures) {
    return advancedFeatures.generateComprehensiveSecurityOverview(sastData, containerData, runId, repoOwner, repoName);
  }

  // Fallback to original implementation
  return `## 🛡️ Security Hardening Pipeline ${riskEmoji}

### 🎯 Security Score
${getRiskBadge(riskLevel)} **Overall Risk: ${riskLevel}**

| Component | 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | Status |
|-----------|-------------|---------|-----------|---------|---------|
| 🔍 SAST Analysis | ${sastData?.totalCritical || 0} | ${sastData?.totalHigh || 0} | ${sastData?.totalMedium || 0} | ${sastData?.totalLow || 0} | ✅ Complete |
| 🐳 Container Security | ${containerData?.totalCritical || 0} | ${containerData?.totalHigh || 0} | ${containerData?.totalMedium || 0} | ${containerData?.totalLow || 0} | ✅ Complete |
| **🎯 Total** | **${totalCritical}** | **${totalHigh}** | **${totalMedium}** | **${totalLow}** | **${totalVulns} issues** |

### 🚀 Next Steps
${generateActionItems(totalCritical, totalHigh, totalMedium)}

### 📥 Download All Reports
- 📋 **[All Security Artifacts](https://github.com/${repoOwner}/${repoName}/actions/runs/${runId}#artifacts)**
- 🔍 **[GitHub Security Dashboard](https://github.com/${repoOwner}/${repoName}/security)**
- ⚙️ **[Security Settings](https://github.com/${repoOwner}/${repoName}/settings/security_analysis)**

---
*Generated: ${new Date().toLocaleString()} | [View Full Workflow](https://github.com/${repoOwner}/${repoName}/actions/runs/${runId})*`;
}

// Example usage with sample data
if (require.main === module) {
  console.log('Enhanced PR Comment Generator');
  console.log('=============================\n');

  // Sample SAST data
  const sastData = {
    tools: [
      { name: 'CodeQL', critical: 0, high: 0, medium: 0, low: 0, total: 0, status: 'success' },
      { name: 'OpenGrep', critical: 3, high: 13, medium: 1, low: 0, total: 17, status: 'success' },
      { name: 'Bandit', critical: 2, high: 6, medium: 14, low: 0, total: 22, status: 'success' },
      { name: 'Safety', critical: 0, high: 0, medium: 0, low: 0, total: 0, status: 'success' },
      { name: 'Gitleaks', critical: 19, high: 0, medium: 0, low: 0, total: 19, status: 'success' }
    ],
    totalCritical: 24,
    totalHigh: 19,
    totalMedium: 15,
    totalLow: 0
  };

  // Sample Container data
  const containerData = {
    containers: [
      {
        name: 'docker-vulnerable',
        critical: 74,
        high: 1220,
        medium: 2853,
        low: 1146,
        total: 5293,
        buildStatus: 'success'
      },
      {
        name: 'docker-secure',
        critical: 0,
        high: 0,
        medium: 0,
        low: 0,
        total: 0,
        buildStatus: 'success'
      }
    ],
    totalCritical: 74,
    totalHigh: 1220,
    totalMedium: 2853,
    totalLow: 1146,
    scannedContainers: 2,
    buildFailures: 0
  };

  const runId = '12345';
  const repoOwner = 'huntridge-labs';
  const repoName = 'hardening-workflows';

  // Generate enhanced comments
  console.log('SAST Comment:');
  console.log(generateEnhancedSASTComment(sastData, runId, repoOwner, repoName));
  console.log('\n' + '='.repeat(80) + '\n');

  console.log('Container Comment:');
  console.log(generateEnhancedContainerComment(containerData, runId, repoOwner, repoName));
  console.log('\n' + '='.repeat(80) + '\n');

  console.log('Security Overview:');
  console.log(generateSecurityOverview(sastData, containerData, runId, repoOwner, repoName));
}

module.exports = {
  parseSASTReport,
  parseContainerReport,
  generateEnhancedSASTComment,
  generateEnhancedContainerComment,
  generateSecurityOverview,
  getRiskLevel,
  getRiskBadge,
  generateActionItems
};
