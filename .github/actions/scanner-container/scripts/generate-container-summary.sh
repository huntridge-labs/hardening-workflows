#!/usr/bin/env bash
# Generate container security summary from scan results
# Usage: generate-container-summary.sh [options]
#
# Environment variables:
#   TRIVY_PARSER   - Path to trivy parser script (required)
#   GRYPE_PARSER   - Path to grype parser script (required)
#   GITHUB_STEP_SUMMARY - Path to step summary file (optional)
#   GITHUB_REPOSITORY   - Repository name for links (optional)
#   GITHUB_RUN_ID       - Run ID for artifact links (optional)

set -euo pipefail

# Ensure required env vars
: "${TRIVY_PARSER:?TRIVY_PARSER must be set}"
: "${GRYPE_PARSER:?GRYPE_PARSER must be set}"

mkdir -p scanner-summaries
shopt -s nullglob

# Reorganize artifacts into expected directory structure
echo "🔄 Reorganizing artifacts..."
for trivy_file in ./trivy-*-results.json; do
  [ -f "$trivy_file" ] || continue
  container_name=$(basename "$trivy_file" | sed 's/trivy-//; s/-results\.json//')
  mkdir -p "container-scan-results-${container_name}"
  mv ./trivy-"${container_name}"-results.* "container-scan-results-${container_name}/" 2>/dev/null || true
  mv ./grype-"${container_name}"-results.* "container-scan-results-${container_name}/" 2>/dev/null || true
  mv ./container-summary-"${container_name}".md "container-scan-results-${container_name}/" 2>/dev/null || true
done

# Check if we have results
if ! compgen -G "container-scan-results-*" > /dev/null 2>&1; then
  echo "⏭️ No container scan results found"
  echo "<details><summary>🐳 Container Security</summary>" > scanner-summaries/container.md
  echo -e "\n**Status:** ⏭️ Skipped\n</details>" >> scanner-summaries/container.md
  if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
    echo -e "## 🐳 Container Security Scan Summary\n\n**Status:** ⏭️ No containers found" >> "$GITHUB_STEP_SUMMARY"
  fi
  exit 0
fi

echo "📊 Generating container security summary..."

# Initialize
TOTAL_CRIT=0; TOTAL_HIGH=0; TOTAL_MED=0; TOTAL_LOW=0
SCANNED=0; FAILED=0
declare -a CONTAINERS=()
ALL_CVES=""

# Parse each container
for dir in container-scan-results-*; do
  [ -d "$dir" ] || continue
  name="${dir#container-scan-results-}"
  [[ "$name" == sbom-* ]] && continue

  trivy_json="$dir/trivy-${name}-results.json"
  grype_json="$dir/grype-${name}-results.json"

  if [ -f "$trivy_json" ] || [ -f "$grype_json" ]; then
    # Get counts from each scanner
    read t_crit t_high t_med t_low <<< "$("$TRIVY_PARSER" counts "$trivy_json")"
    read g_crit g_high g_med g_low <<< "$("$GRYPE_PARSER" counts "$grype_json")"

    t_total=$("$TRIVY_PARSER" total "$trivy_json")
    t_unique=$("$TRIVY_PARSER" unique "$trivy_json")
    g_total=$("$GRYPE_PARSER" total "$grype_json")
    g_unique=$("$GRYPE_PARSER" unique "$grype_json")

    # Combine CVEs and deduplicate
    trivy_cves=$("$TRIVY_PARSER" cves "$trivy_json")
    grype_cves=$("$GRYPE_PARSER" cves "$grype_json")
    combined_cves=$(printf "%s\n%s" "$trivy_cves" "$grype_cves" | sort -u | grep -v '^$' || true)
    combined_unique=$(echo "$combined_cves" | grep -c . || true)
    combined_unique=${combined_unique:-0}
    ALL_CVES=$(printf "%s\n%s" "$ALL_CVES" "$combined_cves")

    # Get deduplicated counts by severity
    crit=$(printf "%s\n%s" \
      "$("$TRIVY_PARSER" cves-by-severity "$trivy_json" -s CRITICAL)" \
      "$("$GRYPE_PARSER" cves-by-severity "$grype_json" -s Critical)" | sort -u | grep -c . || true)
    crit=${crit:-0}
    high=$(printf "%s\n%s" \
      "$("$TRIVY_PARSER" cves-by-severity "$trivy_json" -s HIGH)" \
      "$("$GRYPE_PARSER" cves-by-severity "$grype_json" -s High)" | sort -u | grep -c . || true)
    high=${high:-0}
    med=$(printf "%s\n%s" \
      "$("$TRIVY_PARSER" cves-by-severity "$trivy_json" -s MEDIUM)" \
      "$("$GRYPE_PARSER" cves-by-severity "$grype_json" -s Medium)" | sort -u | grep -c . || true)
    med=${med:-0}
    low=$(printf "%s\n%s" \
      "$("$TRIVY_PARSER" cves-by-severity "$trivy_json" -s LOW)" \
      "$("$GRYPE_PARSER" cves-by-severity "$grype_json" -s Low)" | sort -u | grep -c . || true)
    low=${low:-0}

    total=$((crit + high + med + low))
    digest=$("$TRIVY_PARSER" digest "$trivy_json")
    image_ref=$("$TRIVY_PARSER" image "$trivy_json")

    # Store data
    CONTAINERS+=("$name|$digest|$image_ref|$crit|$high|$med|$low|$total|$combined_unique|$t_total|$t_unique|$g_total|$g_unique")
    TOTAL_CRIT=$((TOTAL_CRIT + crit)); TOTAL_HIGH=$((TOTAL_HIGH + high))
    TOTAL_MED=$((TOTAL_MED + med)); TOTAL_LOW=$((TOTAL_LOW + low))
    SCANNED=$((SCANNED + 1))
    echo "  ✅ $name: $total vulns ($crit crit, $high high, $med med, $low low)"
  else
    CONTAINERS+=("$name|unknown|unknown|0|0|0|0|0|0|0|0|0|0|failed")
    FAILED=$((FAILED + 1))
    echo "  ❌ $name: Build failed"
  fi
done

TOTAL=$((TOTAL_CRIT + TOTAL_HIGH + TOTAL_MED + TOTAL_LOW))
UNIQUE=$(echo "$ALL_CVES" | sort -u | grep -c . || true)
UNIQUE=${UNIQUE:-0}

# Build output targets
OUTPUT_TARGETS=("scanner-summaries/container.md")
[ -n "${GITHUB_STEP_SUMMARY:-}" ] && OUTPUT_TARGETS+=("$GITHUB_STEP_SUMMARY")

# Generate reports
for output in "${OUTPUT_TARGETS[@]}"; do
  if [[ "$output" == *"container.md" ]]; then
    echo "<details><summary>🐳 Container Security</summary>" >> "$output"
    echo -e "\n**Status:** ✅ Completed\n" >> "$output"
  else
    echo -e "## 🐳 Container Security Scan Summary\n" >> "$output"
  fi

  # Summary table
  cat >> "$output" << EOF
### 📊 Combined Findings Summary (Deduplicated)

| 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | 📦 Total | 🔢 Unique |
|-------------|---------|-----------|---------|----------|----------|
| **$TOTAL_CRIT** | **$TOTAL_HIGH** | **$TOTAL_MED** | **$TOTAL_LOW** | **$TOTAL** | **$UNIQUE** |

**Scanned:** $SCANNED containers | **Build Failures:** $FAILED

EOF

  # Container breakdown (only for multiple containers)
  if [ "$SCANNED" -ne 1 ]; then
    echo "### 📦 Container Breakdown" >> "$output"
    echo -e "\n| Container | Image | 🚨 Crit | ⚠️ High | 🟡 Med | 🔵 Low | Total | Unique | Status |" >> "$output"
    echo "|-----------|-------|---------|---------|--------|--------|-------|--------|--------|" >> "$output"
    for data in "${CONTAINERS[@]}"; do
      IFS='|' read -r n d img c h m l t u _ _ _ _ st <<< "$data"
      if [ "${st:-}" = "failed" ]; then
        echo "| $n | - | - | - | - | - | - | - | ❌ Failed |" >> "$output"
      else
        echo "| $n | \`${img}\` | $c | $h | $m | $l | $t | $u | ✅ |" >> "$output"
      fi
    done
    echo "" >> "$output"
  fi

  # Detailed findings
  echo -e "### 🔍 Detailed Findings by Container\n" >> "$output"
  for data in "${CONTAINERS[@]}"; do
    IFS='|' read -r name digest image_ref crit high med low total unique t_total t_unique g_total g_unique status <<< "$data"

    if [ "${status:-}" = "failed" ]; then
      echo "<details><summary>❌ <strong>$name</strong> - Build Failed</summary>" >> "$output"
      echo -e "\n**Status:** Build failed\n</details>\n" >> "$output"
      continue
    fi

    # Determine emoji
    if [ "$crit" -gt 0 ]; then emoji="🚨"
    elif [ "$high" -gt 0 ]; then emoji="⚠️"
    elif [ "$total" -gt 0 ]; then emoji="🟡"
    else emoji="✅"; fi

    cat >> "$output" << EOF
<details>
<summary>$emoji <strong>$name</strong> - $total vulnerabilities ($unique unique)</summary>

**Image:** \`$image_ref\`
**Digest:** \`@$digest\`

#### Combined (Deduplicated)

| 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | Total | Unique |
|-------------|---------|-----------|---------|-------|--------|
| $crit | $high | $med | $low | $total | $unique |

<details open>
<summary>🔷 Trivy Scanner ($t_total findings, $t_unique unique)</summary>

EOF
    trivy_json="container-scan-results-${name}/trivy-${name}-results.json"
    if [ "$t_total" -eq 0 ]; then
      echo "✅ No vulnerabilities detected by Trivy" >> "$output"
    elif [ -f "$trivy_json" ]; then
      echo "| CVE | Severity | Package | Version | Fixed |" >> "$output"
      echo "|-----|----------|---------|---------|-------|" >> "$output"
      "$TRIVY_PARSER" table "$trivy_json" -l 50 >> "$output"
      [ "$t_total" -gt 50 ] && echo -e "\n_...and $((t_total - 50)) more_" >> "$output"
    fi
    echo -e "\n</details>\n" >> "$output"

    echo "<details open>" >> "$output"
    echo "<summary>⚓ Grype Scanner ($g_total findings, $g_unique unique)</summary>" >> "$output"
    echo "" >> "$output"
    grype_json="container-scan-results-${name}/grype-${name}-results.json"
    if [ "$g_total" -eq 0 ]; then
      echo "✅ No vulnerabilities detected by Grype" >> "$output"
    elif [ -f "$grype_json" ]; then
      echo "| CVE | Severity | Package | Version | Fixed |" >> "$output"
      echo "|-----|----------|---------|---------|-------|" >> "$output"
      "$GRYPE_PARSER" table "$grype_json" -l 50 >> "$output"
      [ "$g_total" -gt 50 ] && echo -e "\n_...and $((g_total - 50)) more_" >> "$output"
    fi
    echo -e "\n</details>\n\n</details>\n" >> "$output"
  done

  # Artifact link
  if [ -n "${GITHUB_REPOSITORY:-}" ] && [ -n "${GITHUB_RUN_ID:-}" ]; then
    echo "**📁 Artifacts:** [Container Scan Reports](${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}#artifacts)" >> "$output"
  fi

  [[ "$output" == *"container.md" ]] && echo -e "\n</details>" >> "$output"
done

echo "✅ Reports generated"
