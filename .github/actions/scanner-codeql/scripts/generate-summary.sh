#!/bin/bash
# Generate CodeQL scanner summary markdown
#
# Arguments:
#   $1  - Output file path
#   $2  - Is PR comment (true/false)
#   $3  - Language analyzed
#   $4  - Critical count
#   $5  - High count
#   $6  - Medium count
#   $7  - Low count
#   $8  - Total count
#   $9  - Repository URL for links
#   $10 - GitHub server URL
#   $11 - Repository (owner/repo)
#   $12 - Run ID

set -e

OUTPUT="$1"
IS_PR_COMMENT="$2"
LANGUAGE="$3"
CRITICAL="${4:-0}"
HIGH="${5:-0}"
MEDIUM="${6:-0}"
LOW="${7:-0}"
TOTAL="${8:-0}"
REPO_URL="$9"
SERVER_URL="${10}"
REPOSITORY="${11}"
RUN_ID="${12}"

# Capitalize first letter of language for display (portable across BSD/GNU)
LANG_DISPLAY="$(echo "$LANGUAGE" | awk '{print toupper(substr($0,1,1)) substr($0,2)}')"

# Start output
if [ "$IS_PR_COMMENT" = "true" ]; then
  echo "<details>" >> "$OUTPUT"
  echo "<summary>🔬 CodeQL SAST ($LANG_DISPLAY)</summary>" >> "$OUTPUT"
else
  echo "## 🔬 CodeQL SAST Scan ($LANG_DISPLAY)" >> "$OUTPUT"
fi
echo "" >> "$OUTPUT"

# Check if we have results
if [ "$TOTAL" -gt 0 ] || [ -d "codeql-reports/sarif" ]; then
  if [ "$IS_PR_COMMENT" = "true" ]; then
    echo "**Status:** Completed" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi

  # Summary table
  echo "### Findings Summary" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
  echo "| Critical | High | Medium | Low | Total |" >> "$OUTPUT"
  echo "|----------|------|--------|-----|-------|" >> "$OUTPUT"
  echo "| **$CRITICAL** | **$HIGH** | **$MEDIUM** | **$LOW** | **$TOTAL** |" >> "$OUTPUT"
  echo "" >> "$OUTPUT"

  # Priority messages
  if [ "$CRITICAL" -gt 0 ]; then
    echo "**CRITICAL**: $CRITICAL critical-severity findings (CVSS >= 9.0) need immediate attention" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi
  if [ "$HIGH" -gt 0 ]; then
    echo "**HIGH**: $HIGH high-severity findings (CVSS >= 7.0) should be addressed promptly" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi

  if [ "$TOTAL" -eq 0 ]; then
    echo "No security findings detected for $LANG_DISPLAY." >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi

  # Detailed findings (parse SARIF files if available)
  if [ -d "codeql-reports/sarif" ] && [ "$TOTAL" -gt 0 ]; then
    echo "<details>" >> "$OUTPUT"
    echo "<summary>Finding Details</summary>" >> "$OUTPUT"
    echo "" >> "$OUTPUT"

    for sarif_file in codeql-reports/sarif/*.sarif; do
      if [ -f "$sarif_file" ] && command -v jq >/dev/null 2>&1; then
        # Extract findings with location info
        findings=$(jq -r --arg repo_url "$REPO_URL" '
          .runs[]? | {rules: (.tool.driver.rules // []), results: .results} |
          .rules as $rules |
          .results[]? |
          . as $result |
          ($rules[] | select(.id == $result.ruleId)) as $rule |
          ($rule.properties["security-severity"] // "0" | tonumber) as $severity |
          ($result.locations[0]?.physicalLocation?.artifactLocation?.uri // "N/A") as $file |
          ($result.locations[0]?.physicalLocation?.region?.startLine // 1) as $line |
          (if $severity >= 9.0 then "Critical"
           elif $severity >= 7.0 then "High"
           elif $severity >= 4.0 then "Medium"
           elif $severity > 0 then "Low"
           else "Info" end) as $level |
          "| \($level) | \($result.ruleId // "N/A") | [\($file)#L\($line)](\($repo_url)/\($file)#L\($line)) | \($result.message.text // "N/A" | gsub("\n"; " ") | .[0:50]) |"
        ' "$sarif_file" 2>/dev/null | head -20)

        if [ -n "$findings" ]; then
          echo "| Severity | Rule | Location | Message |" >> "$OUTPUT"
          echo "|----------|------|----------|---------|" >> "$OUTPUT"
          echo "$findings" >> "$OUTPUT"
          echo "" >> "$OUTPUT"

          # Check if truncated
          total_findings=$(jq -r '[.runs[]?.results[]?] | length' "$sarif_file" 2>/dev/null || echo "0")
          if [ "$total_findings" -gt 20 ]; then
            echo "_Showing 20 of $total_findings findings. See artifacts for complete list._" >> "$OUTPUT"
            echo "" >> "$OUTPUT"
          fi
        fi
      fi
    done

    echo "</details>" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi

  # Artifacts link
  echo "**Artifacts:** [CodeQL Reports ($LANG_DISPLAY)]($SERVER_URL/$REPOSITORY/actions/runs/$RUN_ID#artifacts)" >> "$OUTPUT"
else
  if [ "$IS_PR_COMMENT" = "true" ]; then
    echo "**Status:** Skipped or No Results" >> "$OUTPUT"
  else
    echo "**Status:** No CodeQL results available for $LANG_DISPLAY" >> "$OUTPUT"
  fi
fi

if [ "$IS_PR_COMMENT" = "true" ]; then
  echo "" >> "$OUTPUT"
  echo "</details>" >> "$OUTPUT"
fi
echo "" >> "$OUTPUT"
