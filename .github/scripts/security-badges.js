#!/usr/bin/env node

/**
 * Security Badge Generator
 * 
 * Utility to generate dynamic status badges and visual indicators
 * for security reports and PR comments.
 */

/**
 * Generate shield.io compatible badges
 */
function generateBadge(label, message, color, style = 'flat') {
  const encodedLabel = encodeURIComponent(label);
  const encodedMessage = encodeURIComponent(message);
  return `![${label}](https://img.shields.io/badge/${encodedLabel}-${encodedMessage}-${color}?style=${style})`;
}

/**
 * Generate severity badge based on count
 */
function generateSeverityBadge(severity, count) {
  const colors = {
    'critical': 'red',
    'high': 'orange', 
    'medium': 'yellow',
    'low': 'green',
    'info': 'blue'
  };
  
  const color = colors[severity.toLowerCase()] || 'gray';
  const emoji = {
    'critical': '🚨',
    'high': '⚠️',
    'medium': '🟡',
    'low': '🔵',
    'info': 'ℹ️'
  };
  
  return `${emoji[severity.toLowerCase()] || ''} ${generateBadge(severity, count, color)}`;
}

/**
 * Generate risk level badge with color coding
 */
function generateRiskBadge(critical, high, medium, low) {
  let level, color, emoji;
  
  if (critical > 0) {
    level = 'CRITICAL';
    color = 'red';
    emoji = '🚨';
  } else if (high > 5) {
    level = 'HIGH';
    color = 'orange';  
    emoji = '⚠️';
  } else if (high > 0) {
    level = 'MODERATE';
    color = 'yellow';
    emoji = '🟡';
  } else if (medium > 0) {
    level = 'LOW';
    color = 'green';
    emoji = '🔵';
  } else {
    level = 'EXCELLENT';
    color = 'brightgreen';
    emoji = '✅';
  }
  
  return `${emoji} ${generateBadge('Security Risk', level, color)}`;
}

/**
 * Generate coverage badge
 */
function generateCoverageBadge(percentage) {
  let color;
  if (percentage >= 90) color = 'brightgreen';
  else if (percentage >= 75) color = 'green';
  else if (percentage >= 60) color = 'yellow';
  else if (percentage >= 40) color = 'orange';
  else color = 'red';
  
  return generateBadge('Coverage', `${percentage}%`, color);
}

/**
 * Generate workflow status badges
 */
function generateWorkflowBadges(workflows) {
  return Object.entries(workflows)
    .map(([name, status]) => {
      const color = status === 'success' ? 'brightgreen' : 
                   status === 'failure' ? 'red' :
                   status === 'cancelled' ? 'lightgray' : 'yellow';
      return generateBadge(name, status, color);
    })
    .join(' ');
}

/**
 * Generate compliance badges
 */
function generateComplianceBadges(standards) {
  const badges = [];
  
  if (standards.includes('SOX')) {
    badges.push(generateBadge('SOX', 'Compliant', 'blue'));
  }
  
  if (standards.includes('PCI-DSS')) {
    badges.push(generateBadge('PCI-DSS', 'Compliant', 'blue'));
  }
  
  if (standards.includes('GDPR')) {
    badges.push(generateBadge('GDPR', 'Compliant', 'blue'));
  }
  
  if (standards.includes('ISO27001')) {
    badges.push(generateBadge('ISO 27001', 'Compliant', 'blue'));
  }
  
  return badges.join(' ');
}

/**
 * Generate security score visualization
 */
function generateSecurityScore(vulnerabilities) {
  const { critical = 0, high = 0, medium = 0, low = 0 } = vulnerabilities;
  
  // Calculate weighted score (0-100)
  const maxScore = 100;
  const criticalWeight = 10;
  const highWeight = 5;
  const mediumWeight = 2;
  const lowWeight = 1;
  
  const penalty = (critical * criticalWeight) + 
                  (high * highWeight) + 
                  (medium * mediumWeight) + 
                  (low * lowWeight);
  
  const score = Math.max(0, maxScore - penalty);
  
  let grade, color;
  if (score >= 90) { grade = 'A+'; color = 'brightgreen'; }
  else if (score >= 80) { grade = 'A'; color = 'green'; }
  else if (score >= 70) { grade = 'B'; color = 'yellowgreen'; }
  else if (score >= 60) { grade = 'C'; color = 'yellow'; }
  else if (score >= 50) { grade = 'D'; color = 'orange'; }
  else { grade = 'F'; color = 'red'; }
  
  return {
    score,
    grade,
    badge: generateBadge('Security Score', `${score}/100 (${grade})`, color)
  };
}

/**
 * Generate interactive progress bar using Unicode blocks
 */
function generateProgressBar(current, total, width = 20) {
  if (total === 0) return '▓'.repeat(width) + ' (0/0)';
  
  const percentage = Math.round((current / total) * 100);
  const filled = Math.round((current / total) * width);
  const empty = width - filled;
  
  const blocks = '▓'.repeat(filled) + '░'.repeat(empty);
  return `${blocks} ${percentage}% (${current}/${total})`;
}

/**
 * Generate trending indicators
 */
function generateTrendingIndicator(current, previous) {
  if (previous === undefined || previous === null) return '';
  
  const diff = current - previous;
  if (diff > 0) return `📈 +${diff}`;
  if (diff < 0) return `📉 ${diff}`;
  return '➡️ ±0';
}

/**
 * Generate security metrics dashboard
 */
function generateSecurityDashboard(data) {
  const { 
    vulnerabilities = {}, 
    workflows = {}, 
    compliance = [], 
    previousScan = {}
  } = data;
  
  const securityScore = generateSecurityScore(vulnerabilities);
  const riskBadge = generateRiskBadge(
    vulnerabilities.critical || 0,
    vulnerabilities.high || 0, 
    vulnerabilities.medium || 0,
    vulnerabilities.low || 0
  );
  
  return `
### 📊 Security Dashboard

${riskBadge} ${securityScore.badge}

**Vulnerability Breakdown:**
- 🚨 Critical: **${vulnerabilities.critical || 0}** ${generateTrendingIndicator(vulnerabilities.critical, previousScan.critical)}
- ⚠️ High: **${vulnerabilities.high || 0}** ${generateTrendingIndicator(vulnerabilities.high, previousScan.high)}
- 🟡 Medium: **${vulnerabilities.medium || 0}** ${generateTrendingIndicator(vulnerabilities.medium, previousScan.medium)}
- 🔵 Low: **${vulnerabilities.low || 0}** ${generateTrendingIndicator(vulnerabilities.low, previousScan.low)}

**Scan Progress:**
${generateProgressBar(Object.keys(workflows).filter(w => workflows[w] === 'success').length, Object.keys(workflows).length)}

**Workflow Status:**
${generateWorkflowBadges(workflows)}

${compliance.length > 0 ? `**Compliance:**
${generateComplianceBadges(compliance)}` : ''}
`;
}

module.exports = {
  generateBadge,
  generateSeverityBadge,
  generateRiskBadge,
  generateCoverageBadge,
  generateWorkflowBadges,
  generateComplianceBadges,
  generateSecurityScore,
  generateProgressBar,
  generateTrendingIndicator,
  generateSecurityDashboard
};

// Example usage
if (require.main === module) {
  console.log('Security Badge Generator');
  console.log('=======================\n');
  
  const exampleData = {
    vulnerabilities: {
      critical: 2,
      high: 8,
      medium: 15,
      low: 3
    },
    workflows: {
      'SAST': 'success',
      'Container': 'success',
      'Dependencies': 'failure'
    },
    compliance: ['SOX', 'PCI-DSS'],
    previousScan: {
      critical: 3,
      high: 10,
      medium: 12,
      low: 5
    }
  };
  
  console.log(generateSecurityDashboard(exampleData));
}