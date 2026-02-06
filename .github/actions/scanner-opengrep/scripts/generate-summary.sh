#!/bin/bash
# Generate OpenGrep scanner summary markdown
#
# Arguments:
#   $1  - Output file path
#   $2  - Is PR comment (true/false)
#   $3  - Error count
#   $4  - Warning count
#   $5  - Info count
#   $6  - Total count
#   $7  - Repository URL for links
#   $8  - GitHub server URL
#   $9  - Repository (owner/repo)
#   $10 - Run ID

set -e

OUTPUT="$1"
IS_PR_COMMENT="$2"
ERROR_COUNT="${3:-0}"
WARNING_COUNT="${4:-0}"
INFO_COUNT="${5:-0}"
TOTAL="${6:-0}"
REPO_URL="$7"
SERVER_URL="${8}"
REPOSITORY="${9}"
RUN_ID="${10}"

# Start output
if [ "$IS_PR_COMMENT" = "true" ]; then
  echo "<details>" >> "$OUTPUT"
  echo "<summary>🔍 OpenGrep SAST</summary>" >> "$OUTPUT"
else
  echo "## OpenGrep SAST Scan" >> "$OUTPUT"
fi
echo "" >> "$OUTPUT"

# Check if we have results
if [ "$TOTAL" -gt 0 ] || [ -d "opengrep-reports" ]; then
  if [ "$IS_PR_COMMENT" = "true" ]; then
    echo "**Status:** Completed" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi

  # Summary table
  echo "### Findings Summary" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
  echo "| Error | Warning | Info | Total |" >> "$OUTPUT"
  echo "|-------|---------|------|-------|" >> "$OUTPUT"
  echo "| **$ERROR_COUNT** | **$WARNING_COUNT** | **$INFO_COUNT** | **$TOTAL** |" >> "$OUTPUT"
  echo "" >> "$OUTPUT"

  # Priority messages
  if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "**ERROR**: $ERROR_COUNT error-severity findings need immediate attention" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi
  if [ "$WARNING_COUNT" -gt 0 ]; then
    echo "**WARNING**: $WARNING_COUNT warning-severity findings should be reviewed" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi

  if [ "$TOTAL" -eq 0 ]; then
    echo "No security findings detected." >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi

  # Detailed findings (parse JSON if available)
  if [ -f "opengrep-reports/opengrep.json" ] && [ "$TOTAL" -gt 0 ]; then
    echo "<details>" >> "$OUTPUT"
    echo "<summary>Finding Details</summary>" >> "$OUTPUT"
    echo "" >> "$OUTPUT"

    if command -v jq >/dev/null 2>&1; then
      # Extract findings with location info
      findings=$(jq -r --arg repo_url "$REPO_URL" '
        .results[]? |
        (.extra.severity // "INFO") as $severity |
        (.path // "N/A") as $file |
        (.start.line // 1) as $start |
        (.end.line // .start.line // 1) as $end |
        (.check_id // "N/A" | split(".")[-1]) as $rule |
        (.extra.message // .extra.metadata.message // "N/A" | gsub("\n"; " ") | .[0:60]) as $msg |
        "| \($severity) | \($rule) | [\($file)#L\($start)](\($repo_url)/\($file)#L\($start)-L\($end)) | \($msg) |"
      ' opengrep-reports/opengrep.json 2>/dev/null | head -20)

      if [ -n "$findings" ]; then
        echo "| Severity | Rule | Location | Message |" >> "$OUTPUT"
        echo "|----------|------|----------|---------|" >> "$OUTPUT"
        echo "$findings" >> "$OUTPUT"
        echo "" >> "$OUTPUT"

        # Check if truncated
        if [ "$TOTAL" -gt 20 ]; then
          echo "_Showing 20 of $TOTAL findings. See artifacts for complete list._" >> "$OUTPUT"
          echo "" >> "$OUTPUT"
        fi
      fi
    fi

    echo "</details>" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi

  # Artifacts link
  echo "**Artifacts:** [OpenGrep Reports]($SERVER_URL/$REPOSITORY/actions/runs/$RUN_ID#artifacts)" >> "$OUTPUT"
else
  if [ "$IS_PR_COMMENT" = "true" ]; then
    echo "**Status:** Skipped or No Results" >> "$OUTPUT"
  else
    echo "**Status:** No OpenGrep results available" >> "$OUTPUT"
  fi
fi

if [ "$IS_PR_COMMENT" = "true" ]; then
  echo "" >> "$OUTPUT"
  echo "</details>" >> "$OUTPUT"
fi
echo "" >> "$OUTPUT"
