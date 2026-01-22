#!/bin/bash
set -euo pipefail

# Checkov Summary Generator
# Usage: generate-summary.sh <output_file> <is_pr_comment> <has_iac> <iac_path> <critical> <high> <medium> <low> <passed> <total> <repo_url> <github_server_url> <github_repo> <github_run_id>

OUTPUT_FILE="${1:-}"
IS_PR_COMMENT="${2:-false}"
HAS_IAC="${3:-false}"
IAC_PATH="${4:-}"
CRITICAL="${5:-0}"
HIGH="${6:-0}"
MEDIUM="${7:-0}"
LOW="${8:-0}"
PASSED="${9:-0}"
TOTAL="${10:-0}"
REPO_URL="${11:-}"
GITHUB_SERVER_URL="${12:-https://github.com}"
GITHUB_REPO="${13:-}"
GITHUB_RUN_ID="${14:-}"

if [ -z "$OUTPUT_FILE" ]; then
  echo "Error: output file is required"
  echo "Usage: $0 <output_file> <is_pr_comment> <has_iac> <iac_path> <critical> <high> <medium> <low> <passed> <total> <repo_url> <github_server_url> <github_repo> <github_run_id>"
  exit 1
fi

generate_checkov_summary() {
  local output="$OUTPUT_FILE"
  local is_pr_comment="$IS_PR_COMMENT"

  if [ "$is_pr_comment" = "true" ]; then
    echo "<details>" >> "$output"
    echo "<summary>🏗️ Checkov IaC Security</summary>" >> "$output"
  else
    echo "## 🏗️ Checkov IaC Security Scan Summary" >> "$output"
  fi
  echo "" >> "$output"

  if [ "$HAS_IAC" == "true" ]; then
    JSON_FILE="checkov-reports/checkov-results.json"

    if [ -f "$JSON_FILE" ]; then
      if [ "$is_pr_comment" = "true" ]; then
        echo "**Status:** ✅ Completed" >> "$output"
        echo "" >> "$output"
      fi

      # Get framework info
      CHECK_TYPE=$(jq -r '.check_type // "unknown"' "$JSON_FILE" 2>/dev/null || echo "unknown")

      # Overall Summary Table
      echo "### 📊 Check Summary" >> "$output"
      echo "" >> "$output"
      echo "| 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | ❌ Failed | ✅ Passed |" >> "$output"
      echo "|-------------|---------|-----------|--------|-----------|-----------|" >> "$output"
      echo "| **$CRITICAL** | **$HIGH** | **$MEDIUM** | **$LOW** | **$TOTAL** | **$PASSED** |" >> "$output"
      echo "" >> "$output"

      echo "**Framework:** $CHECK_TYPE" >> "$output"
      echo "" >> "$output"

      # Priority messages
      if [ "$TOTAL" -gt 0 ]; then
        if [ "$CRITICAL" -gt 0 ]; then
          echo "🚨 **CRITICAL**: $CRITICAL critical severity issues require immediate attention" >> "$output"
          echo "" >> "$output"
        elif [ "$HIGH" -gt 0 ]; then
          echo "⚠️ **HIGH**: $HIGH high severity issues need attention" >> "$output"
          echo "" >> "$output"
        else
          echo "❌ **FAILED**: $TOTAL IaC security checks failed" >> "$output"
          echo "" >> "$output"
        fi
      fi

      # Detailed findings with collapsible sections
      if [ "$TOTAL" -gt 0 ]; then
        echo "<details>" >> "$output"
        echo "<summary>🔍 Failed Check Details ($TOTAL)</summary>" >> "$output"
        echo "" >> "$output"

        # Group by severity
        if [ "$CRITICAL" -gt 0 ]; then
          echo "<details open>" >> "$output"
          echo "<summary>🚨 Critical Severity ($CRITICAL)</summary>" >> "$output"
          echo "" >> "$output"
          echo "| Check ID | Check Name | Resource | Location |" >> "$output"
          echo "|----------|------------|----------|----------|" >> "$output"

          jq -r --arg repo_url "$REPO_URL" '.results.failed_checks[]? | select(.severity == "CRITICAL") |
            (.file_path // "N/A" | ltrimstr("/")) as $filepath |
            (.file_line_range[0] // 1) as $start |
            (.file_line_range[1] // 1) as $end |
            "| \(.check_id // "N/A") | \(.check_name // "N/A" | .[0:50]) | \(.resource // "N/A" | .[0:40]) | [\($filepath)#L\($start)-L\($end)](\($repo_url)/\($filepath)#L\($start)-L\($end)) |"' "$JSON_FILE" 2>/dev/null >> "$output" || echo "| Error parsing results | - | - | - |" >> "$output"

          echo "" >> "$output"
          echo "</details>" >> "$output"
          echo "" >> "$output"
        fi

        if [ "$HIGH" -gt 0 ]; then
          echo "<details>" >> "$output"
          echo "<summary>⚠️ High Severity ($HIGH)</summary>" >> "$output"
          echo "" >> "$output"
          echo "| Check ID | Check Name | Resource | Location |" >> "$output"
          echo "|----------|------------|----------|----------|" >> "$output"

          jq -r --arg repo_url "$REPO_URL" '.results.failed_checks[]? | select(.severity == "HIGH") |
            (.file_path // "N/A" | ltrimstr("/")) as $filepath |
            (.file_line_range[0] // 1) as $start |
            (.file_line_range[1] // 1) as $end |
            "| \(.check_id // "N/A") | \(.check_name // "N/A" | .[0:50]) | \(.resource // "N/A" | .[0:40]) | [\($filepath)#L\($start)-L\($end)](\($repo_url)/\($filepath)#L\($start)-L\($end)) |"' "$JSON_FILE" 2>/dev/null >> "$output" || echo "| Error parsing results | - | - | - |" >> "$output"

          echo "" >> "$output"
          echo "</details>" >> "$output"
          echo "" >> "$output"
        fi

        if [ "$MEDIUM" -gt 0 ]; then
          echo "<details>" >> "$output"
          echo "<summary>🟡 Medium Severity ($MEDIUM)</summary>" >> "$output"
          echo "" >> "$output"
          echo "| Check ID | Check Name | Resource | Location |" >> "$output"
          echo "|----------|------------|----------|----------|" >> "$output"

          jq -r --arg repo_url "$REPO_URL" '.results.failed_checks[]? | select(.severity == "MEDIUM") |
            (.file_path // "N/A" | ltrimstr("/")) as $filepath |
            (.file_line_range[0] // 1) as $start |
            (.file_line_range[1] // 1) as $end |
            "| \(.check_id // "N/A") | \(.check_name // "N/A" | .[0:50]) | \(.resource // "N/A" | .[0:40]) | [\($filepath)#L\($start)-L\($end)](\($repo_url)/\($filepath)#L\($start)-L\($end)) |"' "$JSON_FILE" 2>/dev/null >> "$output" || echo "| Error parsing results | - | - | - |" >> "$output"

          echo "" >> "$output"
          echo "</details>" >> "$output"
          echo "" >> "$output"
        fi

        if [ "$LOW" -gt 0 ]; then
          echo "<details>" >> "$output"
          echo "<summary>🔵 Low Severity ($LOW)</summary>" >> "$output"
          echo "" >> "$output"
          echo "| Check ID | Check Name | Resource | Location |" >> "$output"
          echo "|----------|------------|----------|----------|" >> "$output"

          jq -r --arg repo_url "$REPO_URL" '.results.failed_checks[]? | select(.severity == "LOW") |
            (.file_path // "N/A" | ltrimstr("/")) as $filepath |
            (.file_line_range[0] // 1) as $start |
            (.file_line_range[1] // 1) as $end |
            "| \(.check_id // "N/A") | \(.check_name // "N/A" | .[0:50]) | \(.resource // "N/A" | .[0:40]) | [\($filepath)#L\($start)-L\($end)](\($repo_url)/\($filepath)#L\($start)-L\($end)) |"' "$JSON_FILE" 2>/dev/null >> "$output" || echo "| Error parsing results | - | - | - |" >> "$output"

          echo "" >> "$output"
          echo "</details>" >> "$output"
          echo "" >> "$output"
        fi

        # If no severity info, show all failed checks
        if [ "$CRITICAL" -eq 0 ] && [ "$HIGH" -eq 0 ] && [ "$MEDIUM" -eq 0 ] && [ "$LOW" -eq 0 ] && [ "$TOTAL" -gt 0 ]; then
          echo "| Check ID | Check Name | Resource | Location |" >> "$output"
          echo "|----------|------------|----------|----------|" >> "$output"

          jq -r --arg repo_url "$REPO_URL" '.results.failed_checks[]? |
            (.file_path // "N/A" | ltrimstr("/")) as $filepath |
            (.file_line_range[0] // 1) as $start |
            (.file_line_range[1] // 1) as $end |
            "| \(.check_id // "N/A") | \(.check_name // "N/A" | .[0:50]) | \(.resource // "N/A" | .[0:40]) | [\($filepath)#L\($start)-L\($end)](\($repo_url)/\($filepath)#L\($start)-L\($end)) |"' "$JSON_FILE" 2>/dev/null >> "$output" || echo "| Error parsing results | - | - | - |" >> "$output"

          echo "" >> "$output"
        fi

        echo "</details>" >> "$output"
        echo "" >> "$output"
      elif [ "$TOTAL" -eq 0 ] && [ "$PASSED" -gt 0 ]; then
        echo "✅ **All $PASSED security checks passed!**" >> "$output"
        echo "" >> "$output"
      fi

      echo "**📁 Artifacts:** [Checkov Results]($GITHUB_SERVER_URL/$GITHUB_REPO/actions/runs/$GITHUB_RUN_ID#artifacts)" >> "$output"
    else
      if [ "$is_pr_comment" = "true" ]; then
        echo "**Status:** ⚠️ No results generated" >> "$output"
      else
        echo "**Status:** ⚠️ No Checkov results available" >> "$output"
      fi
    fi
  else
    if [ "$is_pr_comment" = "true" ]; then
      echo "**Status:** ⏭️ Skipped (no IaC directory found)" >> "$output"
    else
      echo "**Status:** ⏭️ Skipped - no IaC directory found at '$IAC_PATH'" >> "$output"
    fi
  fi

  if [ "$is_pr_comment" = "true" ]; then
    echo "" >> "$output"
    echo "</details>" >> "$output"
  fi
  echo "" >> "$output"
}

# Generate the summary
generate_checkov_summary
