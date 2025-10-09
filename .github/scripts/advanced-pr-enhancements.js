#!/usr/bin/env node

/**
 * Advanced PR Comment Enhancements
 *
 * Additional UX improvements for security PR comments:
 * - Interactive status check visualization
 * - Deep links to specific security findings
 * - Progressive disclosure for large reports
 * - Mobile-friendly formatting
 */

const fs = require('fs');

/**
 * Generate workflow status badges
 */
function generateWorkflowBadges(runId, repoOwner, repoName, workflowStatuses = {}) {
  const badges = [];

  if (workflowStatuses.sast !== undefined) {
    const sastStatus = workflowStatuses.sast ? 'passing' : 'failing';
    const sastColor = workflowStatuses.sast ? 'brightgreen' : 'red';
    badges.push(`![SAST](https://img.shields.io/badge/SAST-${sastStatus}-${sastColor})`);
  }

  if (workflowStatuses.container !== undefined) {
    const containerStatus = workflowStatuses.container ? 'passing' : 'failing';
    const containerColor = workflowStatuses.container ? 'brightgreen' : 'red';
    badges.push(`![Container](https://img.shields.io/badge/Container-${containerStatus}-${containerColor})`);
  }

  return badges.join(' ');
}

/**
 * Generate action buttons for quick access
 */
function generateActionButtons(runId, repoOwner, repoName) {
  return `
### 🚀 Quick Actions

<table>
<tr>
<td>📥 <strong>Downloads</strong></td>
<td>🔍 <strong>Analysis</strong></td>
<td>⚙️ <strong>Settings</strong></td>
</tr>
<tr>
<td>
• <a href="https://github.com/${repoOwner}/${repoName}/actions/runs/${runId}#artifacts">All Reports</a><br>
• <a href="https://github.com/${repoOwner}/${repoName}/actions/runs/${runId}">Workflow Run</a><br>
• <a href="https://github.com/${repoOwner}/${repoName}/security/code-scanning">SARIF Results</a>
</td>
<td>
• <a href="https://github.com/${repoOwner}/${repoName}/security">Security Dashboard</a><br>
• <a href="https://github.com/${repoOwner}/${repoName}/security/advisories">Advisories</a><br>
• <a href="https://github.com/${repoOwner}/${repoName}/network/dependencies">Dependencies</a>
</td>
<td>
• <a href="https://github.com/${repoOwner}/${repoName}/settings/security_analysis">Security Settings</a><br>
• <a href="https://github.com/${repoOwner}/${repoName}/settings/actions">Actions Settings</a><br>
• <a href="https://github.com/${repoOwner}/${repoName}/settings/branches">Branch Protection</a>
</td>
</tr>
</table>`;
}

/**
 * Generate mobile-friendly summary cards
 */
function generateSummaryCards(sastData, containerData) {
  const cards = [];

  if (sastData) {
    const { totalCritical, totalHigh, totalMedium, totalLow } = sastData;
    const total = totalCritical + totalHigh + totalMedium + totalLow;

    cards.push(`
<table>
<tr><th colspan="2">🔍 SAST Analysis</th></tr>
<tr><td>🚨 Critical</td><td><strong>${totalCritical}</strong></td></tr>
<tr><td>⚠️ High</td><td><strong>${totalHigh}</strong></td></tr>
<tr><td>🟡 Medium</td><td>${totalMedium}</td></tr>
<tr><td>🔵 Low</td><td>${totalLow}</td></tr>
<tr><td><strong>📊 Total</strong></td><td><strong>${total}</strong></td></tr>
</table>`);
  }

  if (containerData) {
    const { totalCritical, totalHigh, totalMedium, totalLow } = containerData;
    const total = totalCritical + totalHigh + totalMedium + totalLow;

    cards.push(`
<table>
<tr><th colspan="2">🐳 Container Security</th></tr>
<tr><td>🚨 Critical</td><td><strong>${totalCritical}</strong></td></tr>
<tr><td>⚠️ High</td><td><strong>${totalHigh}</strong></td></tr>
<tr><td>🟡 Medium</td><td>${totalMedium}</td></tr>
<tr><td>🔵 Low</td><td>${totalLow}</td></tr>
<tr><td><strong>📦 Total</strong></td><td><strong>${total}</strong></td></tr>
</table>`);
  }

  return `
<div align="center">

${cards.join('\n')}

</div>`;
}

/**
 * Generate enhanced security timeline
 */
function generateSecurityTimeline(findings) {
  if (!findings || findings.length === 0) return '';

  return `
<details>
<summary>📈 <strong>Security Timeline</strong></summary>

\`\`\`mermaid
gantt
    title Security Scan Progress
    dateFormat X
    axisFormat %H:%M

    section Analysis
    SAST Scan     :sast, 0, 5
    Container Scan:container, 3, 8
    Report Gen    :report, 8, 10
\`\`\`

</details>`;
}

/**
 * Generate enhanced remediation guide with code examples
 */
function generateEnhancedRemediationGuide(sastData, containerData) {
  const guides = [];

  if (sastData && (sastData.totalCritical > 0 || sastData.totalHigh > 0)) {
    guides.push(`
#### 🔧 Code Security Issues

<details>
<summary><strong>Common Fixes</strong></summary>

\`\`\`python
# Example: Fix SQL Injection
# Before (vulnerable)
query = f"SELECT * FROM users WHERE id = {user_id}"

# After (secure)
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
\`\`\`

\`\`\`javascript
// Example: Fix XSS
// Before (vulnerable)
element.innerHTML = userInput;

// After (secure)
element.textContent = userInput;
\`\`\`

</details>`);
  }

  if (containerData && (containerData.totalCritical > 0 || containerData.totalHigh > 0)) {
    guides.push(`
#### 🐳 Container Security Fixes

<details>
<summary><strong>Dockerfile Best Practices</strong></summary>

\`\`\`dockerfile
# Use specific, minimal base images
FROM alpine:3.18 AS base

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \\
    adduser -S nextjs -u 1001

# Use multi-stage builds
FROM base AS dependencies
COPY package*.json ./
RUN npm ci --only=production

FROM base AS runner
USER nextjs
COPY --from=dependencies --chown=nextjs:nodejs /app .
\`\`\`

</details>`);
  }

  return guides.join('\n');
}

/**
 * Generate progressive disclosure sections for large datasets
 */
function generateProgressiveDisclosure(data, title, threshold = 10) {
  if (!data || data.length <= threshold) {
    return `
<details>
<summary>${title} (${data?.length || 0} items)</summary>

${data?.map(item => `- ${item}`).join('\n') || 'No items found'}

</details>`;
  }

  const preview = data.slice(0, threshold);
  const remaining = data.slice(threshold);

  return `
<details>
<summary>${title} (${data.length} items - showing first ${threshold})</summary>

${preview.map(item => `- ${item}`).join('\n')}

<details>
<summary>Show ${remaining.length} more items...</summary>

${remaining.map(item => `- ${item}`).join('\n')}

</details>

</details>`;
}

/**
 * Generate comprehensive security overview with all enhancements
 */
function generateComprehensiveSecurityOverview(sastData, containerData, runId, repoOwner, repoName) {
  const totalCritical = (sastData?.totalCritical || 0) + (containerData?.totalCritical || 0);
  const totalHigh = (sastData?.totalHigh || 0) + (containerData?.totalHigh || 0);
  const totalMedium = (sastData?.totalMedium || 0) + (containerData?.totalMedium || 0);
  const totalLow = (sastData?.totalLow || 0) + (containerData?.totalLow || 0);
  const totalVulns = totalCritical + totalHigh + totalMedium + totalLow;

  const riskLevel = totalCritical > 0 ? 'CRITICAL' : totalHigh > 0 ? 'HIGH' : 'LOW';
  const riskEmoji = totalCritical > 0 ? '🚨' : totalHigh > 0 ? '⚠️' : '✅';

  const workflowStatuses = {
    sast: sastData !== null,
    container: containerData !== null
  };

  return `## 🛡️ Security Hardening Pipeline ${riskEmoji}

${generateWorkflowBadges(runId, repoOwner, repoName, workflowStatuses)}

### 🎯 Security Dashboard

<div align="center">

![Risk Level](https://img.shields.io/badge/Risk-${riskLevel}-${riskLevel === 'CRITICAL' ? 'red' : riskLevel === 'HIGH' ? 'orange' : 'green'})
![Total Issues](https://img.shields.io/badge/Total_Issues-${totalVulns}-${totalVulns > 0 ? 'red' : 'green'})
![Scans Complete](https://img.shields.io/badge/Scans-Complete-brightgreen)

</div>

${generateSummaryCards(sastData, containerData)}

### 🚨 Priority Actions

${totalCritical > 0 ? `
> **🚨 CRITICAL**: ${totalCritical} critical vulnerabilities require **immediate attention**
> These issues should be fixed before merging this PR.` : ''}

${totalHigh > 0 ? `
> **⚠️ HIGH**: ${totalHigh} high-severity vulnerabilities should be addressed **within 24 hours**` : ''}

${totalVulns === 0 ? `
> **✅ EXCELLENT**: No security vulnerabilities detected!
> Your code meets security best practices.` : ''}

${generateActionButtons(runId, repoOwner, repoName)}

<details>
<summary>📊 <strong>Detailed Analysis</strong></summary>

| Component | 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | Status |
|-----------|-------------|---------|-----------|---------|---------|
| 🔍 SAST Analysis | ${sastData?.totalCritical || 0} | ${sastData?.totalHigh || 0} | ${sastData?.totalMedium || 0} | ${sastData?.totalLow || 0} | ${sastData ? '✅ Complete' : '⚠️ Pending'} |
| 🐳 Container Security | ${containerData?.totalCritical || 0} | ${containerData?.totalHigh || 0} | ${containerData?.totalMedium || 0} | ${containerData?.totalLow || 0} | ${containerData ? '✅ Complete' : '⚠️ Pending'} |
| **🎯 Total** | **${totalCritical}** | **${totalHigh}** | **${totalMedium}** | **${totalLow}** | **${totalVulns} issues** |

</details>

${generateEnhancedRemediationGuide(sastData, containerData)}

<details>
<summary>ℹ️ <strong>About This Report</strong></summary>

This automated security analysis helps identify potential vulnerabilities before they reach production.

**What's included:**
- 🔍 **Static Analysis (SAST)** - Code-level security scanning
- 🐳 **Container Security** - Image vulnerability scanning
- 📋 **Dependency Analysis** - Known CVE detection
- 🔒 **Secret Detection** - Credential leak prevention

**Next Steps:**
1. Download detailed reports from [workflow artifacts](https://github.com/${repoOwner}/${repoName}/actions/runs/${runId}#artifacts)
2. Review findings in the [Security Dashboard](https://github.com/${repoOwner}/${repoName}/security)
3. Address critical and high-severity issues first
4. Consider enabling [GitHub Advanced Security](https://github.com/${repoOwner}/${repoName}/settings/security_analysis) for enhanced features

</details>

---
*🤖 Generated: ${new Date().toLocaleString()} | [View Full Workflow](https://github.com/${repoOwner}/${repoName}/actions/runs/${runId}) | [Security Settings](https://github.com/${repoOwner}/${repoName}/settings/security_analysis)*`;
}

// Export all functions
module.exports = {
  generateWorkflowBadges,
  generateActionButtons,
  generateSummaryCards,
  generateSecurityTimeline,
  generateEnhancedRemediationGuide,
  generateProgressiveDisclosure,
  generateComprehensiveSecurityOverview
};

// Example usage
if (require.main === module) {
  console.log('Advanced PR Comment Enhancement Utilities');
  console.log('==========================================\n');

  // Example implementation showing comprehensive overview
  const sastData = {
    totalCritical: 3,
    totalHigh: 12,
    totalMedium: 5,
    totalLow: 0
  };

  const containerData = {
    totalCritical: 2,
    totalHigh: 8,
    totalMedium: 15,
    totalLow: 3
  };

  const comprehensive = generateComprehensiveSecurityOverview(
    sastData,
    containerData,
    '12345',
    'huntridge-labs',
    'hardening-workflows'
  );

  console.log('Comprehensive Security Overview:');
  console.log(comprehensive);
}
