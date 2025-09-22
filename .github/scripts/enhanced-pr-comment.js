/**
 * Enhanced PR Comment Generator for Security Workflows
 * Provides better UX with collapsible sections, direct links, and cleaner formatting
 */

/**
 * Generate enhanced container security comment
 */
function generateContainerSecurityComment(reportData, runId, repoInfo) {
  const { containers, vulnerabilities, buildFailures } = reportData;
  const { owner, repo } = repoInfo;

  // Calculate totals and risk level
  const totalVulns = vulnerabilities.critical + vulnerabilities.high + vulnerabilities.medium + vulnerabilities.low;
  const riskLevel = getRiskLevel(vulnerabilities.critical, vulnerabilities.high);
  const riskEmoji = getRiskEmoji(riskLevel);

  return `## 🐳 Container Security Analysis ${riskEmoji}

### 📊 Quick Summary
${getRiskBadge(riskLevel)} **Risk Level: ${riskLevel}**

| 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | 📦 Total |
|-------------|---------|-----------|---------|----------|
| **${vulnerabilities.critical}** | **${vulnerabilities.high}** | **${vulnerabilities.medium}** | **${vulnerabilities.low}** | **${totalVulns}** |

${generateActionItems(vulnerabilities)}

### 📥 Download Reports
- 📋 **[Download All Container Reports](https://github.com/${owner}/${repo}/actions/runs/${runId}#artifacts)**
- 🔍 **[View Detailed SARIF Results](https://github.com/${owner}/${repo}/security/code-scanning)**

<details>
<summary>📋 <strong>Container Details</strong> (${containers.scanned} scanned, ${buildFailures} failures)</summary>

| Container | Critical | High | Medium | Low | Total | Status |
|-----------|----------|------|--------|-----|-------|---------|
${containers.details.map(c =>
  `| ${c.name} | ${c.vulnerabilities.critical} | ${c.vulnerabilities.high} | ${c.vulnerabilities.medium} | ${c.vulnerabilities.low} | ${c.total} | ${c.buildStatus} |`
).join('\n')}

</details>

<details>
<summary>🛠️ <strong>Remediation Guide</strong></summary>

#### Immediate Actions (Critical/High)
${vulnerabilities.critical > 0 ? `
- 🚨 **${vulnerabilities.critical} critical vulnerabilities** require immediate patching
- 📋 [Download detailed vulnerability report](https://github.com/${owner}/${repo}/actions/runs/${runId}#artifacts)
- 🔄 Update base images and dependencies
` : ''}
${vulnerabilities.high > 0 ? `
- ⚠️ **${vulnerabilities.high} high-severity vulnerabilities** should be addressed within 24h
` : ''}

#### Best Practices
- 🐧 Use minimal base images (Alpine, distroless)
- 🏗️ Implement multi-stage builds
- 👤 Run containers as non-root users
- 🔒 Enable GitHub Advanced Security for integrated reporting

</details>

---
*Generated: ${new Date().toLocaleString()} | [View Workflow](https://github.com/${owner}/${repo}/actions/runs/${runId})*`;
}

/**
 * Generate enhanced SAST security comment
 */
function generateSASTComment(reportData, runId, repoInfo) {
  const { tools, vulnerabilities } = reportData;
  const { owner, repo } = repoInfo;

  const totalVulns = vulnerabilities.critical + vulnerabilities.high + vulnerabilities.medium + vulnerabilities.low;
  const riskLevel = getRiskLevel(vulnerabilities.critical, vulnerabilities.high);
  const riskEmoji = getRiskEmoji(riskLevel);

  return `## 🔍 SAST Security Analysis ${riskEmoji}

### 📊 Quick Summary
${getRiskBadge(riskLevel)} **Risk Level: ${riskLevel}**

| 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | 📊 Total |
|-------------|---------|-----------|---------|----------|
| **${vulnerabilities.critical}** | **${vulnerabilities.high}** | **${vulnerabilities.medium}** | **${vulnerabilities.low}** | **${totalVulns}** |

${generateActionItems(vulnerabilities)}

### 📥 Quick Access
- 📋 **[Download All SAST Reports](https://github.com/${owner}/${repo}/actions/runs/${runId}#artifacts)**
- 🔍 **[View in GitHub Security](https://github.com/${owner}/${repo}/security/code-scanning)**
- ⚙️ **[Configure Dependabot](https://github.com/${owner}/${repo}/settings/security_analysis)**

<details>
<summary>🛠️ <strong>Tool Results</strong> (${tools.length} tools ran)</summary>

| Tool | Critical | High | Medium | Low | Status |
|------|----------|------|--------|-----|--------|
${tools.map(t =>
  `| ${t.name} | ${t.vulnerabilities.critical} | ${t.vulnerabilities.high} | ${t.vulnerabilities.medium} | ${t.vulnerabilities.low} | ${t.status} |`
).join('\n')}

</details>

<details>
<summary>🚨 <strong>Priority Findings</strong></summary>

${vulnerabilities.critical > 0 ? `
#### 🚨 Critical Issues (${vulnerabilities.critical})
- Require immediate attention
- Block deployment until resolved
- [Download detailed reports](https://github.com/${owner}/${repo}/actions/runs/${runId}#artifacts)
` : ''}

${vulnerabilities.high > 0 ? `
#### ⚠️ High Priority Issues (${vulnerabilities.high})
- Address within 24 hours
- Review during next development cycle
` : ''}

${totalVulns === 0 ? `
#### ✅ No Security Issues Found
Great work! All SAST tools passed without detecting security vulnerabilities.
` : ''}

</details>

---
*Generated: ${new Date().toLocaleString()} | [View Workflow](https://github.com/${owner}/${repo}/actions/runs/${runId})*`;
}

/**
 * Generate consolidated security overview comment
 */
function generateSecurityOverviewComment(allReports, runId, repoInfo) {
  const { owner, repo } = repoInfo;
  const { sast, container, infrastructure } = allReports;

  // Calculate aggregate metrics
  const totalCritical = (sast?.vulnerabilities.critical || 0) + (container?.vulnerabilities.critical || 0);
  const totalHigh = (sast?.vulnerabilities.high || 0) + (container?.vulnerabilities.high || 0);
  const totalMedium = (sast?.vulnerabilities.medium || 0) + (container?.vulnerabilities.medium || 0);
  const totalLow = (sast?.vulnerabilities.low || 0) + (container?.vulnerabilities.low || 0);
  const totalVulns = totalCritical + totalHigh + totalMedium + totalLow;

  const riskLevel = getRiskLevel(totalCritical, totalHigh);
  const riskEmoji = getRiskEmoji(riskLevel);

  return `## 🛡️ Security Hardening Pipeline ${riskEmoji}

### 🎯 Security Score
${getRiskBadge(riskLevel)} **Overall Risk: ${riskLevel}**

| Component | 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | Status |
|-----------|-------------|---------|-----------|---------|---------|
| 🔍 SAST Analysis | ${sast?.vulnerabilities.critical || 0} | ${sast?.vulnerabilities.high || 0} | ${sast?.vulnerabilities.medium || 0} | ${sast?.vulnerabilities.low || 0} | ${sast?.status || 'Pending'} |
| 🐳 Container Security | ${container?.vulnerabilities.critical || 0} | ${container?.vulnerabilities.high || 0} | ${container?.vulnerabilities.medium || 0} | ${container?.vulnerabilities.low || 0} | ${container?.status || 'Pending'} |
| 🏗️ Infrastructure | ${infrastructure?.vulnerabilities.critical || 0} | ${infrastructure?.vulnerabilities.high || 0} | ${infrastructure?.vulnerabilities.medium || 0} | ${infrastructure?.vulnerabilities.low || 0} | ${infrastructure?.status || 'Pending'} |
| **🎯 Total** | **${totalCritical}** | **${totalHigh}** | **${totalMedium}** | **${totalLow}** | **${totalVulns} issues** |

### 🚀 Next Steps
${generateActionItems({critical: totalCritical, high: totalHigh, medium: totalMedium, low: totalLow})}

### 📥 Download All Reports
- 📋 **[All Security Artifacts](https://github.com/${owner}/${repo}/actions/runs/${runId}#artifacts)**
- 🔍 **[GitHub Security Dashboard](https://github.com/${owner}/${repo}/security)**
- ⚙️ **[Security Settings](https://github.com/${owner}/${repo}/settings/security_analysis)**

<details>
<summary>📊 <strong>Detailed Breakdown</strong></summary>

#### 🔍 SAST Analysis
${sast ? generateSASTSummary(sast) : '⏳ Running...'}

#### 🐳 Container Security
${container ? generateContainerSummary(container) : '⏳ Running...'}

#### 🏗️ Infrastructure Security
${infrastructure ? generateInfrastructureSummary(infrastructure) : '⏳ Running...'}

</details>

---
*Generated: ${new Date().toLocaleString()} | [View Full Workflow](https://github.com/${owner}/${repo}/actions/runs/${runId})*`;
}

/**
 * Helper functions
 */
function getRiskLevel(critical, high) {
  if (critical > 0) return 'CRITICAL';
  if (high > 5) return 'HIGH';
  if (high > 0) return 'MODERATE';
  return 'LOW';
}

function getRiskEmoji(riskLevel) {
  switch(riskLevel) {
    case 'CRITICAL': return '🚨';
    case 'HIGH': return '⚠️';
    case 'MODERATE': return '🟡';
    case 'LOW': return '✅';
    default: return '📊';
  }
}

function getRiskBadge(riskLevel) {
  switch(riskLevel) {
    case 'CRITICAL': return '![Critical](https://img.shields.io/badge/Risk-CRITICAL-red)';
    case 'HIGH': return '![High](https://img.shields.io/badge/Risk-HIGH-orange)';
    case 'MODERATE': return '![Moderate](https://img.shields.io/badge/Risk-MODERATE-yellow)';
    case 'LOW': return '![Low](https://img.shields.io/badge/Risk-LOW-green)';
    default: return '![Unknown](https://img.shields.io/badge/Risk-UNKNOWN-gray)';
  }
}

function generateActionItems(vulnerabilities) {
  const items = [];

  if (vulnerabilities.critical > 0) {
    items.push(`🚨 **URGENT**: ${vulnerabilities.critical} critical issues need immediate attention`);
  }
  if (vulnerabilities.high > 0) {
    items.push(`⚠️ **HIGH**: ${vulnerabilities.high} high-severity issues to address within 24h`);
  }
  if (vulnerabilities.medium > 0) {
    items.push(`🟡 **MEDIUM**: ${vulnerabilities.medium} medium issues for next sprint`);
  }
  if (vulnerabilities.critical === 0 && vulnerabilities.high === 0 && vulnerabilities.medium === 0) {
    items.push(`✅ **GREAT JOB**: No high-priority security issues found!`);
  }

  return items.length > 0 ? items.join('\n') : '';
}

function generateSASTSummary(sast) {
  return `- ${sast.tools.length} tools executed
- ${sast.vulnerabilities.critical + sast.vulnerabilities.high + sast.vulnerabilities.medium + sast.vulnerabilities.low} total findings
- Status: ${sast.status}`;
}

function generateContainerSummary(container) {
  return `- ${container.containers.scanned} containers scanned
- ${container.buildFailures} build failures
- ${container.vulnerabilities.critical + container.vulnerabilities.high + container.vulnerabilities.medium + container.vulnerabilities.low} total vulnerabilities
- Status: ${container.status}`;
}

function generateInfrastructureSummary(infrastructure) {
  return `- Terraform security analysis
- ${infrastructure.vulnerabilities.critical + infrastructure.vulnerabilities.high + infrastructure.vulnerabilities.medium + infrastructure.vulnerabilities.low} total findings
- Status: ${infrastructure.status}`;
}

module.exports = {
  generateContainerSecurityComment,
  generateSASTComment,
  generateSecurityOverviewComment
};
