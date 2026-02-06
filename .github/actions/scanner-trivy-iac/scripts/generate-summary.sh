#!/bin/bash
set -euo pipefail

# Trivy IaC Summary Generator
# Usage: generate-summary.sh <output_file> <is_pr_comment> <has_iac> <iac_path> <repo_url> <github_server_url> <github_repo> <github_run_id>

OUTPUT_FILE="${1:-}"
IS_PR_COMMENT="${2:-false}"
HAS_IAC="${3:-false}"
IAC_PATH="${4:-}"
REPO_URL="${5:-}"
GITHUB_SERVER_URL="${6:-https://github.com}"
GITHUB_REPO="${7:-}"
GITHUB_RUN_ID="${8:-}"

if [ -z "$OUTPUT_FILE" ]; then
  echo "Error: output file is required"
  echo "Usage: $0 <output_file> <is_pr_comment> <has_iac> <iac_path> <repo_url> <github_server_url> <github_repo> <github_run_id>"
  exit 1
fi

generate_trivy_iac_summary() {
  local output="$OUTPUT_FILE"
  local is_pr_comment="$IS_PR_COMMENT"

  if [ "$is_pr_comment" = "true" ]; then
    echo "<details>" >> "$output"
    echo "<summary>🔍 Trivy IaC Scanner</summary>" >> "$output"
  else
    echo "## 🔍 Trivy IaC Scanner Summary" >> "$output"
  fi
  echo "" >> "$output"

  if [ "$HAS_IAC" == "true" ]; then
    JSON_FILE="$IAC_PATH/security-reports/trivy-results.json"
    SARIF_FILE="$IAC_PATH/security-reports/trivy-results.sarif"

    if [ -f "$JSON_FILE" ]; then
      if [ "$is_pr_comment" = "true" ]; then
        echo "**Status:** ✅ Completed" >> "$output"
        echo "" >> "$output"
      fi

      CRITICAL=$(jq '[.Results[]?.Misconfigurations[]? | select(.Severity == "CRITICAL")] | length' "$JSON_FILE" 2>/dev/null || echo "0")
      HIGH=$(jq '[.Results[]?.Misconfigurations[]? | select(.Severity == "HIGH")] | length' "$JSON_FILE" 2>/dev/null || echo "0")
      MEDIUM=$(jq '[.Results[]?.Misconfigurations[]? | select(.Severity == "MEDIUM")] | length' "$JSON_FILE" 2>/dev/null || echo "0")
      LOW=$(jq '[.Results[]?.Misconfigurations[]? | select(.Severity == "LOW")] | length' "$JSON_FILE" 2>/dev/null || echo "0")
      TOTAL=$((CRITICAL + HIGH + MEDIUM + LOW))

      echo "### 📊 Findings Summary" >> "$output"
      echo "" >> "$output"
      echo "| 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | 📦 Total |" >> "$output"
      echo "|-------------|---------|-----------|--------|----------|" >> "$output"
      echo "| **$CRITICAL** | **$HIGH** | **$MEDIUM** | **$LOW** | **$TOTAL** |" >> "$output"
      echo "" >> "$output"

      # Detailed findings with clickable links, grouped by severity
      if [ $TOTAL -gt 0 ] && [ -f "$SARIF_FILE" ]; then
        echo "<details>" >> "$output"
        echo "<summary>🔍 Finding Details ($TOTAL)</summary>" >> "$output"
        echo "" >> "$output"

        # Critical severity findings
        if [ $CRITICAL -gt 0 ]; then
          echo "<details>" >> "$output"
          echo "<summary>🚨 Critical Severity ($CRITICAL)</summary>" >> "$output"
          echo "" >> "$output"
          echo "| Rule ID | Location | Message |" >> "$output"
          echo "|---------|----------|---------|" >> "$output"

          jq -r --arg repo_url "$REPO_URL" --arg iac_path "$IAC_PATH" '
            .runs[]? | {rules: (.tool.driver.rules // []), results: .results} |
            .rules as $rules |
            .results[]? |
            . as $result |
            ($rules[] | select(.id == $result.ruleId)) as $rule |
            ($rule.properties["security-severity"] // "0" | tonumber) as $severity |
            select($severity >= 9.0) |
            ($result.locations[0]?.physicalLocation?.artifactLocation?.uri // "N/A" | ltrimstr("./") | ltrimstr("/")) as $relfile |
            (if $relfile == "N/A" then "N/A" else "\($iac_path)/\($relfile)" end) as $file |
            ($result.locations[0]?.physicalLocation?.region?.startLine // 1) as $line |
            "| \($result.ruleId // "N/A") | [\($file)#L\($line)](\($repo_url)/\($file)#L\($line)) | \($result.message.text // "N/A" | gsub("\n"; " ") | .[0:100]) |"
          ' "$SARIF_FILE" 2>/dev/null >> "$output" || echo "| Error parsing | - | - |" >> "$output"

          echo "" >> "$output"
          echo "</details>" >> "$output"
          echo "" >> "$output"
        fi

        # High severity findings
        if [ $HIGH -gt 0 ]; then
          echo "<details>" >> "$output"
          echo "<summary>⚠️ High Severity ($HIGH)</summary>" >> "$output"
          echo "" >> "$output"
          echo "| Rule ID | Location | Message |" >> "$output"
          echo "|---------|----------|---------|" >> "$output"

          jq -r --arg repo_url "$REPO_URL" --arg iac_path "$IAC_PATH" '
            .runs[]? | {rules: (.tool.driver.rules // []), results: .results} |
            .rules as $rules |
            .results[]? |
            . as $result |
            ($rules[] | select(.id == $result.ruleId)) as $rule |
            ($rule.properties["security-severity"] // "0" | tonumber) as $severity |
            select($severity >= 7.0 and $severity < 9.0) |
            ($result.locations[0]?.physicalLocation?.artifactLocation?.uri // "N/A" | ltrimstr("./") | ltrimstr("/")) as $relfile |
            (if $relfile == "N/A" then "N/A" else "\($iac_path)/\($relfile)" end) as $file |
            ($result.locations[0]?.physicalLocation?.region?.startLine // 1) as $line |
            "| \($result.ruleId // "N/A") | [\($file)#L\($line)](\($repo_url)/\($file)#L\($line)) | \($result.message.text // "N/A" | gsub("\n"; " ") | .[0:100]) |"
          ' "$SARIF_FILE" 2>/dev/null >> "$output" || echo "| Error parsing | - | - |" >> "$output"

          echo "" >> "$output"
          echo "</details>" >> "$output"
          echo "" >> "$output"
        fi

        # Medium severity findings
        if [ $MEDIUM -gt 0 ]; then
          echo "<details>" >> "$output"
          echo "<summary>🟡 Medium Severity ($MEDIUM)</summary>" >> "$output"
          echo "" >> "$output"
          echo "| Rule ID | Location | Message |" >> "$output"
          echo "|---------|----------|---------|" >> "$output"

          jq -r --arg repo_url "$REPO_URL" --arg iac_path "$IAC_PATH" '
            .runs[]? | {rules: (.tool.driver.rules // []), results: .results} |
            .rules as $rules |
            .results[]? |
            . as $result |
            ($rules[] | select(.id == $result.ruleId)) as $rule |
            ($rule.properties["security-severity"] // "0" | tonumber) as $severity |
            select($severity >= 4.0 and $severity < 7.0) |
            ($result.locations[0]?.physicalLocation?.artifactLocation?.uri // "N/A" | ltrimstr("./") | ltrimstr("/")) as $relfile |
            (if $relfile == "N/A" then "N/A" else "\($iac_path)/\($relfile)" end) as $file |
            ($result.locations[0]?.physicalLocation?.region?.startLine // 1) as $line |
            "| \($result.ruleId // "N/A") | [\($file)#L\($line)](\($repo_url)/\($file)#L\($line)) | \($result.message.text // "N/A" | gsub("\n"; " ") | .[0:100]) |"
          ' "$SARIF_FILE" 2>/dev/null >> "$output" || echo "| Error parsing | - | - |" >> "$output"

          echo "" >> "$output"
          echo "</details>" >> "$output"
          echo "" >> "$output"
        fi

        # Low severity findings
        if [ $LOW -gt 0 ]; then
          echo "<details>" >> "$output"
          echo "<summary>🔵 Low Severity ($LOW)</summary>" >> "$output"
          echo "" >> "$output"
          echo "| Rule ID | Location | Message |" >> "$output"
          echo "|---------|----------|---------|" >> "$output"

          jq -r --arg repo_url "$REPO_URL" --arg iac_path "$IAC_PATH" '
            .runs[]? | {rules: (.tool.driver.rules // []), results: .results} |
            .rules as $rules |
            .results[]? |
            . as $result |
            ($rules[] | select(.id == $result.ruleId)) as $rule |
            ($rule.properties["security-severity"] // "0" | tonumber) as $severity |
            select($severity < 4.0) |
            ($result.locations[0]?.physicalLocation?.artifactLocation?.uri // "N/A" | ltrimstr("./") | ltrimstr("/")) as $relfile |
            (if $relfile == "N/A" then "N/A" else "\($iac_path)/\($relfile)" end) as $file |
            ($result.locations[0]?.physicalLocation?.region?.startLine // 1) as $line |
            "| \($result.ruleId // "N/A") | [\($file)#L\($line)](\($repo_url)/\($file)#L\($line)) | \($result.message.text // "N/A" | gsub("\n"; " ") | .[0:100]) |"
          ' "$SARIF_FILE" 2>/dev/null >> "$output" || echo "| Error parsing | - | - |" >> "$output"

          echo "" >> "$output"
          echo "</details>" >> "$output"
          echo "" >> "$output"
        fi

        echo "</details>" >> "$output"
        echo "" >> "$output"
      elif [ $TOTAL -eq 0 ]; then
        echo "✅ **No misconfigurations detected!**" >> "$output"
        echo "" >> "$output"
      fi

      if [ -n "$GITHUB_SERVER_URL" ] && [ -n "$GITHUB_REPO" ] && [ -n "$GITHUB_RUN_ID" ]; then
        echo "**📁 Artifacts:** [Trivy IaC Results]($GITHUB_SERVER_URL/$GITHUB_REPO/actions/runs/$GITHUB_RUN_ID#artifacts)" >> "$output"
      fi
    else
      if [ "$is_pr_comment" = "true" ]; then
        echo "**Status:** ⚠️ No results generated" >> "$output"
      else
        echo "**Status:** ⚠️ No Trivy IaC results available" >> "$output"
      fi
    fi
  else
    if [ "$is_pr_comment" = "true" ]; then
      echo "**Status:** ⏭️ Skipped (no IaC directory found)" >> "$output"
    else
      echo "**Status:** ⏭️ No IaC directory found" >> "$output"
    fi
  fi

  if [ "$is_pr_comment" = "true" ]; then
    echo "" >> "$output"
    echo "</details>" >> "$output"
  fi
  echo "" >> "$output"
}

# Generate the summary
generate_trivy_iac_summary
