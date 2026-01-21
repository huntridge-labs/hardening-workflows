#!/usr/bin/env bash
# Generate ZAP DAST summary from scan results
# Usage: generate-zap-summary.sh
#
# Environment variables:
#   ZAP_PARSER         - Path to ZAP parser script (required)
#   ZAP_SCAN_TYPE      - Scan type for title (baseline/full/api, optional)
#   GITHUB_STEP_SUMMARY - Path to step summary file (optional)
#   GITHUB_REPOSITORY   - Repository name for links (optional)
#   GITHUB_RUN_ID       - Run ID for artifact links (optional)

set -euo pipefail

# Ensure required env vars
: "${ZAP_PARSER:?ZAP_PARSER must be set}"

mkdir -p scanner-summaries
shopt -s nullglob

# Format scan type for display
format_scan_type() {
  local scan_type="${1:-${ZAP_SCAN_TYPE:-}}"
  local display=""

  if [ -n "$scan_type" ]; then
    case "$scan_type" in
      baseline) display=" - Baseline" ;;
      full) display=" - Full Scan" ;;
      api) display=" - API Scan" ;;
      *) display=" - ${scan_type^}" ;;
    esac
  fi

  echo "$display"
}

# Write summary header
write_summary_header() {
  local output="$1"
  local scan_type_display="$2"

  if [[ "$output" == *"zap.md" ]]; then
    echo "<details><summary>🕷️ ZAP (DAST)${scan_type_display}</summary>" >> "$output"
    echo -e "\n**Status:** ✅ Completed\n" >> "$output"
  else
    echo -e "## 🕷️ ZAP DAST Summary${scan_type_display}\n" >> "$output"
  fi
}

# Write skipped summary
write_skipped_summary() {
  local scan_type_display="$1"

  echo "<details><summary>🕷️ ZAP (DAST)${scan_type_display}</summary>" > scanner-summaries/zap.md
  echo -e "\n**Status:** ⏭️ Skipped\n</details>" >> scanner-summaries/zap.md

  if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
    echo -e "## 🕷️ ZAP DAST Summary${scan_type_display}\n\n**Status:** ⏭️ No scans performed" >> "$GITHUB_STEP_SUMMARY"
  fi
}

echo "📊 Generating ZAP DAST summary..."

# Debug: Show what we're looking for
echo "🔍 Looking for ZAP artifacts in: zap-downloads/"
echo "🔍 Current directory: $(pwd)"
echo "🔍 Zap downloads directory structure:"
ls -la zap-downloads/ 2>/dev/null || echo "  ⚠️  zap-downloads/ directory not found"
echo ""
echo "🔍 Searching recursively for report_json.json files:"
find zap-downloads/ -name "report_json.json" -type f 2>/dev/null || echo "  ⚠️  No report_json.json files found"
echo ""

# Initialize aggregates
TOTAL_CRIT=0; TOTAL_HIGH=0; TOTAL_MED=0; TOTAL_LOW=0
SCANNED=0; FAILED=0
declare -a SCAN_RESULTS=()

# Find all ZAP report artifacts
# Note: actions/download-artifact@v6 behavior:
#   - Single artifact: extracts directly to path (zap-downloads/report_json.json)
#   - Multiple artifacts: creates subdirectories (zap-downloads/artifact-name/report_json.json)
echo "🔍 Searching for report files..."
while IFS= read -r report; do
  [ -f "$report" ] || continue
  echo "  ✅ Found report: $report"

  # Determine artifact name from path
  # Path can be either:
  #   zap-downloads/report_json.json (single artifact)
  #   zap-downloads/zap-reports-{inv_key}-{inv_nonce}-{scan_type}-{job_id}/report_json.json (multiple artifacts)

  dir=$(dirname "$report")
  if [[ "$dir" == "zap-downloads" ]]; then
    # Single artifact case - artifact name not in path, need to get it from the artifact metadata
    # For now, we'll use a placeholder and extract scan_type from ZAP_SCAN_TYPE env var
    artifact_name="zap-reports-single-artifact"
    scan_type="${ZAP_SCAN_TYPE:-unknown}"
    echo "  📦 Single artifact detected, using scan_type from env: $scan_type"
  else
    # Multiple artifacts case - artifact name is the directory name
    artifact_name=$(basename "$dir")
    echo "  📦 Artifact name: $artifact_name"

    # Parse artifact name format: zap-reports-{config_hash}-{scan_type}-{target_hash}
    # Example: zap-reports-a1b2c3d4-baseline-e5f6a7

    # Remove "zap-reports-" prefix
    remainder="${artifact_name#zap-reports-}"
    echo "  🔍 After removing prefix: $remainder"

    # Format: {config_hash}-{scan_type}-{target_hash}
    # Look for pattern: {hex8}-{scan_type}-{hex6}
    if [[ "$remainder" =~ ^[0-9a-f]{8}-(baseline|full|api)-[0-9a-f]{6}$ ]]; then
      scan_type="${BASH_REMATCH[1]}"
      echo "  ✅ Extracted scan_type: $scan_type"
    else
      # Fallback
      scan_type="unknown"
      echo "  ⚠️  Could not extract scan_type, using: $scan_type"
    fi
  fi

  # Get counts from parser
  read crit high med low <<< "$("$ZAP_PARSER" counts "$report")"
  total=$((crit + high + med + low))
  unique=$("$ZAP_PARSER" unique "$report")
  target=$("$ZAP_PARSER" target "$report")

  # Store data (removed target_part since we don't use it)
  SCAN_RESULTS+=("$scan_type|$target|$crit|$high|$med|$low|$total|$unique|$artifact_name")
  TOTAL_CRIT=$((TOTAL_CRIT + crit))
  TOTAL_HIGH=$((TOTAL_HIGH + high))
  TOTAL_MED=$((TOTAL_MED + med))
  TOTAL_LOW=$((TOTAL_LOW + low))
  SCANNED=$((SCANNED + 1))

  echo "  ✅ $scan_type scan on $target: $total alerts ($crit crit, $high high, $med med, $low low)"
done < <(find zap-downloads/ -name "report_json.json" -type f 2>/dev/null)

# Check if we have results
if [ "$SCANNED" -eq 0 ]; then
  echo "⏭️ No ZAP scan results found"
  write_skipped_summary "$(format_scan_type)"
  exit 0
fi

TOTAL=$((TOTAL_CRIT + TOTAL_HIGH + TOTAL_MED + TOTAL_LOW))
SCAN_TYPE_DISPLAY="$(format_scan_type)"

# Build output targets
OUTPUT_TARGETS=("scanner-summaries/zap.md")
[ -n "${GITHUB_STEP_SUMMARY:-}" ] && OUTPUT_TARGETS+=("$GITHUB_STEP_SUMMARY")

# Generate reports
for output in "${OUTPUT_TARGETS[@]}"; do
  write_summary_header "$output" "$SCAN_TYPE_DISPLAY"

  # Summary table
  cat >> "$output" << EOF
### 📊 Overall Findings Summary

| 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | 📦 Total |
|-------------|---------|-----------|---------|----------|
| **$TOTAL_CRIT** | **$TOTAL_HIGH** | **$TOTAL_MED** | **$TOTAL_LOW** | **$TOTAL** |

**Scanned:** $SCANNED target(s) | **Scan Failures:** $FAILED

EOF

  # Scan breakdown (only for multiple scans)
  if [ "$SCANNED" -ne 1 ]; then
    echo "### 📦 Scan Breakdown" >> "$output"
    echo -e "\n| Scan Type | Target | 🚨 Crit | ⚠️ High | 🟡 Med | 🔵 Low | Total | Unique | Status |" >> "$output"
    echo "|-----------|--------|---------|---------|--------|--------|-------|--------|--------|" >> "$output"
    for data in "${SCAN_RESULTS[@]}"; do
      IFS='|' read -r scan_type target c h m l t u artifact_name <<< "$data"
      echo "| $scan_type | \`$target\` | $c | $h | $m | $l | $t | $u | ✅ |" >> "$output"
    done
    echo "" >> "$output"
  fi

  # Detailed findings
  echo -e "### 🔍 Detailed Findings by Scan\n" >> "$output"
  for data in "${SCAN_RESULTS[@]}"; do
    IFS='|' read -r scan_type target crit high med low total unique artifact_name <<< "$data"

    # Determine emoji
    if [ "$crit" -gt 0 ]; then emoji="🚨"
    elif [ "$high" -gt 0 ]; then emoji="⚠️"
    elif [ "$total" -gt 0 ]; then emoji="🟡"
    else emoji="✅"; fi

    cat >> "$output" << EOF
<details>
<summary>$emoji <strong>$scan_type scan</strong> on <code>$target</code> - $total alerts ($unique unique)</summary>

**Target:** \`$target\`
**Scan Type:** $scan_type

#### Alert Summary

| 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | Total | Unique |
|-------------|---------|-----------|---------|-------|--------|
| $crit | $high | $med | $low | $total | $unique |

EOF

    # Detailed findings by severity
    # For single artifact, file is at zap-downloads/report_json.json
    # For multiple artifacts, file is at zap-downloads/{artifact_name}/report_json.json
    if [[ "$artifact_name" == "zap-reports-single-artifact" ]]; then
      report="./zap-downloads/report_json.json"
    else
      report="./zap-downloads/${artifact_name}/report_json.json"
    fi

    if [ -f "$report" ]; then
      if [ "$total" -eq 0 ]; then
        echo "✅ No security alerts detected" >> "$output"
      else
        # Critical findings (nested collapsible)
        if [ "$crit" -gt 0 ]; then
          echo "<details>" >> "$output"
          echo "<summary>🚨 <strong>Critical Severity</strong> ($crit findings)</summary>" >> "$output"
          echo "" >> "$output"
          "$ZAP_PARSER" details "$report" -s critical -l 50 >> "$output"
          echo "</details>" >> "$output"
          echo "" >> "$output"
        fi

        # High findings (nested collapsible)
        if [ "$high" -gt 0 ]; then
          echo "<details>" >> "$output"
          echo "<summary>⚠️ <strong>High Severity</strong> ($high findings)</summary>" >> "$output"
          echo "" >> "$output"
          "$ZAP_PARSER" details "$report" -s high -l 50 >> "$output"
          echo "</details>" >> "$output"
          echo "" >> "$output"
        fi

        # Medium findings (compact table)
        if [ "$med" -gt 0 ]; then
          echo "<details>" >> "$output"
          echo "<summary>🟡 <strong>Medium Severity</strong> ($med findings)</summary>" >> "$output"
          echo "" >> "$output"
          "$ZAP_PARSER" compact-table "$report" -s medium -l 50 >> "$output"
          echo "" >> "$output"
          echo "</details>" >> "$output"
          echo "" >> "$output"
        fi

        # Low findings (compact table)
        if [ "$low" -gt 0 ]; then
          echo "<details>" >> "$output"
          echo "<summary>🔵 <strong>Low Severity</strong> ($low findings)</summary>" >> "$output"
          echo "" >> "$output"
          "$ZAP_PARSER" compact-table "$report" -s low -l 50 >> "$output"
          echo "" >> "$output"
          echo "</details>" >> "$output"
          echo "" >> "$output"
        fi
      fi
    fi

    echo -e "\n</details>\n" >> "$output"
  done

  # Artifact link
  if [ -n "${GITHUB_REPOSITORY:-}" ] && [ -n "${GITHUB_RUN_ID:-}" ]; then
    echo "**📁 Artifacts:** [ZAP Scan Reports](https://github.com/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}#artifacts)" >> "$output"
  fi

  [[ "$output" == *"zap.md" ]] && echo -e "\n</details>" >> "$output"
done

echo "✅ ZAP summary generated"
