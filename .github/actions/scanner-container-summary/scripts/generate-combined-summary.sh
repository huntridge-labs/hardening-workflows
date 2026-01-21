#!/usr/bin/env bash
# Generate combined container security summary from parallel matrixed scan results
# This script expects artifacts in the format: container-scan-results-{name}/
# with files like: trivy-{name}-results.json, grype-{name}-results.json
#
# Environment variables:
#   TRIVY_PARSER   - Path to trivy parser script (required)
#   GRYPE_PARSER   - Path to grype parser script (required)
#   GITHUB_STEP_SUMMARY - Path to step summary file (optional)
#   GITHUB_OUTPUT       - Path to outputs file (optional)
#   GITHUB_REPOSITORY   - Repository name for links (optional)
#   GITHUB_RUN_ID       - Run ID for artifact links (optional)

set -euo pipefail

# Ensure required env vars
: "${TRIVY_PARSER:?TRIVY_PARSER must be set}"
: "${GRYPE_PARSER:?GRYPE_PARSER must be set}"

mkdir -p scanner-summaries
shopt -s nullglob

echo "📊 Generating combined container security summary..."

# Reorganize artifacts from matrixed jobs
# Matrixed artifacts come as: container-scan-results-{name}/ (one per scanner)
# We need to merge scanner results for the same container

echo "🔄 Organizing artifacts from matrix jobs..."

# First, find all artifact directories and map to base container names
declare -A CONTAINER_TO_TRIVY
declare -A CONTAINER_TO_GRYPE
declare -A CONTAINER_TO_STATUS
declare -A CONTAINER_NAMES

# Check if any artifact directories exist
found_dirs=0
for dir in container-scan-results-*/; do
  [ -d "$dir" ] || continue
  found_dirs=$((found_dirs + 1))

  # Extract name from directory (e.g., alpine-pinned-grype-30524246)
  base="${dir%/}"
  artifact_name="${base#container-scan-results-}"
  echo "  Found artifact: $artifact_name"

  # Skip SBOM-only directories
  [[ "$artifact_name" == sbom-* ]] && continue

  # Look for nested container-scan-results-* directory
  for nested in "$base"/container-scan-results-*/; do
    if [ -d "$nested" ]; then
      # Extract base container name from nested dir
      inner_name="${nested%/}"
      inner_name="${inner_name##*/}"
      container_base="${inner_name#container-scan-results-}"
      echo "    -> base container: $container_base"

      # Check for scan results and map them
      trivy_file="${nested}trivy-${container_base}-results.json"
      grype_file="${nested}grype-${container_base}-results.json"
      status_file="${nested}scan-status.json"

      if [ -f "$trivy_file" ]; then
        CONTAINER_TO_TRIVY["$container_base"]="$trivy_file"
        echo "    -> found trivy: $trivy_file"
      fi
      if [ -f "$grype_file" ]; then
        CONTAINER_TO_GRYPE["$container_base"]="$grype_file"
        echo "    -> found grype: $grype_file"
      fi
      # Mark this container as seen
      CONTAINER_NAMES["$container_base"]=1

      # Check for failure marker - only from trivy/grype artifacts, not syft
      # (syft artifacts create scan-status.json because they don't produce vuln results)
      if [ -f "$status_file" ]; then
        # Only use status if this artifact was supposed to produce trivy/grype results
        # Skip if artifact name contains "syft"
        if [[ "$artifact_name" != *-syft-* ]]; then
          # Only set status if we don't already have scan results for this container
          if [ -z "${CONTAINER_TO_TRIVY[$container_base]:-}" ] && [ -z "${CONTAINER_TO_GRYPE[$container_base]:-}" ]; then
            CONTAINER_TO_STATUS["$container_base"]="$status_file"
            echo "    -> found status: $status_file"
          fi
        fi
      fi
      break
    fi
  done

  # Also check if files are directly in the artifact dir (legacy format)
  if [ -z "${CONTAINER_NAMES[$artifact_name]:-}" ]; then
    trivy_file="$base/trivy-${artifact_name}-results.json"
    grype_file="$base/grype-${artifact_name}-results.json"
    status_file="$base/scan-status.json"

    if [ -f "$trivy_file" ]; then
      CONTAINER_TO_TRIVY["$artifact_name"]="$trivy_file"
      CONTAINER_NAMES["$artifact_name"]=1
    fi
    if [ -f "$grype_file" ]; then
      CONTAINER_TO_GRYPE["$artifact_name"]="$grype_file"
      CONTAINER_NAMES["$artifact_name"]=1
    fi
    # Only use status file if this is not a syft artifact and we don't have scan results
    if [ -f "$status_file" ] && [[ "$artifact_name" != *-syft-* ]]; then
      if [ -z "${CONTAINER_TO_TRIVY[$artifact_name]:-}" ] && [ -z "${CONTAINER_TO_GRYPE[$artifact_name]:-}" ]; then
        CONTAINER_TO_STATUS["$artifact_name"]="$status_file"
        CONTAINER_NAMES["$artifact_name"]=1
      fi
    fi
  fi
done

if [ "$found_dirs" -eq 0 ] || [ ${#CONTAINER_NAMES[@]} -eq 0 ]; then
  echo "⏭️ No container scan results found"
  echo "<details><summary>🐳 Container Security</summary>" > scanner-summaries/container.md
  echo -e "\n**Status:** ⏭️ Skipped - No scan results found\n</details>" >> scanner-summaries/container.md

  if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
    echo -e "## 🐳 Container Security Scan Summary\n\n**Status:** ⏭️ No containers scanned" >> "$GITHUB_STEP_SUMMARY"
  fi

  # Set outputs
  if [ -n "${GITHUB_OUTPUT:-}" ]; then
    echo "total_vulns=0" >> "$GITHUB_OUTPUT"
    echo "critical=0" >> "$GITHUB_OUTPUT"
    echo "high=0" >> "$GITHUB_OUTPUT"
    echo "containers_scanned=0" >> "$GITHUB_OUTPUT"
  fi

  exit 0
fi

# Initialize counters
TOTAL_CRIT=0; TOTAL_HIGH=0; TOTAL_MED=0; TOTAL_LOW=0
SCANNED=0; FAILED=0
declare -a CONTAINERS=()
ALL_CVES=""

echo ""
echo "📊 Processing ${#CONTAINER_NAMES[@]} unique containers..."

# Process each unique container using the mapped results
for name in "${!CONTAINER_NAMES[@]}"; do
  echo "  Processing: $name"

  trivy_json="${CONTAINER_TO_TRIVY[$name]:-}"
  grype_json="${CONTAINER_TO_GRYPE[$name]:-}"
  status_json="${CONTAINER_TO_STATUS[$name]:-}"

  echo "    trivy: ${trivy_json:-not found}"
  echo "    grype: ${grype_json:-not found}"

  # Check for scan failure marker
  if [ -n "$status_json" ] && [ -f "$status_json" ]; then
    error_msg=$(jq -r '.error // "Scan failed"' "$status_json" 2>/dev/null || echo "Scan failed")
    CONTAINERS+=("$name|unknown|unknown|0|0|0|0|0|0|0|0|0|0|failed|$error_msg")
    FAILED=$((FAILED + 1))
    echo "    ❌ $name: $error_msg"
    continue
  fi

  if [ -n "$trivy_json" ] || [ -n "$grype_json" ]; then
    # Get counts from each scanner
    if [ -n "$trivy_json" ] && [ -f "$trivy_json" ]; then
      read t_crit t_high t_med t_low <<< "$("$TRIVY_PARSER" counts "$trivy_json")"
      t_total=$("$TRIVY_PARSER" total "$trivy_json")
      t_unique=$("$TRIVY_PARSER" unique "$trivy_json")
      trivy_cves=$("$TRIVY_PARSER" cves "$trivy_json")
    else
      t_crit=0; t_high=0; t_med=0; t_low=0; t_total=0; t_unique=0; trivy_cves=""
    fi

    if [ -n "$grype_json" ] && [ -f "$grype_json" ]; then
      read g_crit g_high g_med g_low <<< "$("$GRYPE_PARSER" counts "$grype_json")"
      g_total=$("$GRYPE_PARSER" total "$grype_json")
      g_unique=$("$GRYPE_PARSER" unique "$grype_json")
      grype_cves=$("$GRYPE_PARSER" cves "$grype_json")
    else
      g_crit=0; g_high=0; g_med=0; g_low=0; g_total=0; g_unique=0; grype_cves=""
    fi

    # Combine CVEs and deduplicate
    combined_cves=$(printf "%s\n%s" "$trivy_cves" "$grype_cves" | sort -u | grep -v '^$' || true)
    combined_unique=$(echo "$combined_cves" | grep -c . || true)
    combined_unique=${combined_unique:-0}
    ALL_CVES=$(printf "%s\n%s" "$ALL_CVES" "$combined_cves")

    # Get deduplicated counts by severity (only call parser if file exists)
    trivy_crit="" grype_crit=""
    trivy_high="" grype_high=""
    trivy_med="" grype_med=""
    trivy_low="" grype_low=""

    if [ -n "$trivy_json" ] && [ -f "$trivy_json" ]; then
      trivy_crit=$("$TRIVY_PARSER" cves-by-severity "$trivy_json" -s CRITICAL 2>/dev/null || true)
      trivy_high=$("$TRIVY_PARSER" cves-by-severity "$trivy_json" -s HIGH 2>/dev/null || true)
      trivy_med=$("$TRIVY_PARSER" cves-by-severity "$trivy_json" -s MEDIUM 2>/dev/null || true)
      trivy_low=$("$TRIVY_PARSER" cves-by-severity "$trivy_json" -s LOW 2>/dev/null || true)
    fi

    if [ -n "$grype_json" ] && [ -f "$grype_json" ]; then
      grype_crit=$("$GRYPE_PARSER" cves-by-severity "$grype_json" -s Critical 2>/dev/null || true)
      grype_high=$("$GRYPE_PARSER" cves-by-severity "$grype_json" -s High 2>/dev/null || true)
      grype_med=$("$GRYPE_PARSER" cves-by-severity "$grype_json" -s Medium 2>/dev/null || true)
      grype_low=$("$GRYPE_PARSER" cves-by-severity "$grype_json" -s Low 2>/dev/null || true)
    fi

    crit=$(printf "%s\n%s" "$trivy_crit" "$grype_crit" | sort -u | grep -c . || true)
    crit=${crit:-0}
    high=$(printf "%s\n%s" "$trivy_high" "$grype_high" | sort -u | grep -c . || true)
    high=${high:-0}
    med=$(printf "%s\n%s" "$trivy_med" "$grype_med" | sort -u | grep -c . || true)
    med=${med:-0}
    low=$(printf "%s\n%s" "$trivy_low" "$grype_low" | sort -u | grep -c . || true)
    low=${low:-0}

    total=$((crit + high + med + low))

    # Get image metadata
    if [ -n "$trivy_json" ] && [ -f "$trivy_json" ]; then
      digest=$("$TRIVY_PARSER" digest "$trivy_json")
      image_ref=$("$TRIVY_PARSER" image "$trivy_json")
    elif [ -n "$grype_json" ] && [ -f "$grype_json" ]; then
      # Try grype for metadata if trivy not available
      digest=$("$GRYPE_PARSER" digest "$grype_json" 2>/dev/null || echo "unknown")
      image_ref=$("$GRYPE_PARSER" image "$grype_json" 2>/dev/null || echo "unknown")
    else
      digest="unknown"
      image_ref="unknown"
    fi

    # Store data
    CONTAINERS+=("$name|$digest|$image_ref|$crit|$high|$med|$low|$total|$combined_unique|$t_total|$t_unique|$g_total|$g_unique|success|")
    TOTAL_CRIT=$((TOTAL_CRIT + crit)); TOTAL_HIGH=$((TOTAL_HIGH + high))
    TOTAL_MED=$((TOTAL_MED + med)); TOTAL_LOW=$((TOTAL_LOW + low))
    SCANNED=$((SCANNED + 1))
    echo "    ✅ $name: $total vulns ($crit crit, $high high, $med med, $low low)"
  else
    CONTAINERS+=("$name|unknown|unknown|0|0|0|0|0|0|0|0|0|0|failed|No scan results found")
    FAILED=$((FAILED + 1))
    echo "    ❌ $name: No scan results found"
  fi
done

TOTAL=$((TOTAL_CRIT + TOTAL_HIGH + TOTAL_MED + TOTAL_LOW))
UNIQUE=$(echo "$ALL_CVES" | sort -u | grep -c . || true)
UNIQUE=${UNIQUE:-0}

# Set GitHub outputs
if [ -n "${GITHUB_OUTPUT:-}" ]; then
  echo "total_vulns=$UNIQUE" >> "$GITHUB_OUTPUT"
  echo "critical=$TOTAL_CRIT" >> "$GITHUB_OUTPUT"
  echo "high=$TOTAL_HIGH" >> "$GITHUB_OUTPUT"
  echo "containers_scanned=$SCANNED" >> "$GITHUB_OUTPUT"
fi

# Build output targets
OUTPUT_TARGETS=("scanner-summaries/container.md")
[ -n "${GITHUB_STEP_SUMMARY:-}" ] && OUTPUT_TARGETS+=("$GITHUB_STEP_SUMMARY")

# Generate reports
for output in "${OUTPUT_TARGETS[@]}"; do
  if [[ "$output" == *"container.md" ]]; then
    echo "<details><summary>🐳 Container Security (Parallel Scan)</summary>" >> "$output"
    echo -e "\n**Status:** ✅ Completed\n" >> "$output"
  else
    echo -e "## 🐳 Container Security Scan Summary (Parallel)\n" >> "$output"
  fi

  # Summary table
  cat >> "$output" << EOF
### 📊 Combined Findings Summary (Deduplicated Across Scanners)

| 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | 📦 Total | 🔢 Unique CVEs |
|-------------|---------|-----------|---------|----------|----------------|
| **$TOTAL_CRIT** | **$TOTAL_HIGH** | **$TOTAL_MED** | **$TOTAL_LOW** | **$TOTAL** | **$UNIQUE** |

**Scanned:** $SCANNED containers | **Failed:** $FAILED

EOF

  # Container breakdown
  if [ "$SCANNED" -gt 1 ] || [ "$FAILED" -gt 0 ]; then
    echo "### 📦 Container Breakdown" >> "$output"
    echo -e "\n| Container | Image | 🚨 Crit | ⚠️ High | 🟡 Med | 🔵 Low | Total | Unique | Status |" >> "$output"
    echo "|-----------|-------|---------|---------|--------|--------|-------|--------|--------|" >> "$output"
    for data in "${CONTAINERS[@]}"; do
      IFS='|' read -r n d img c h m l t u _ _ _ _ st err <<< "$data"
      if [ "${st:-}" = "failed" ]; then
        echo "| $n | - | - | - | - | - | - | - | ❌ ${err:-Failed} |" >> "$output"
      else
        echo "| $n | \`${img}\` | $c | $h | $m | $l | $t | $u | ✅ |" >> "$output"
      fi
    done
    echo "" >> "$output"
  fi

  # Detailed findings
  echo -e "### 🔍 Detailed Findings by Container\n" >> "$output"
  for data in "${CONTAINERS[@]}"; do
    IFS='|' read -r name digest image_ref crit high med low total unique t_total t_unique g_total g_unique status error_msg <<< "$data"

    if [ "${status:-}" = "failed" ]; then
      echo "<details><summary>❌ <strong>$name</strong> - Scan Failed</summary>" >> "$output"
      echo -e "\n**Error:** ${error_msg:-No scan results found}\n</details>\n" >> "$output"
      continue
    fi

    # Determine emoji
    if [ "$crit" -gt 0 ]; then emoji="🚨"
    elif [ "$high" -gt 0 ]; then emoji="⚠️"
    elif [ "$total" -gt 0 ]; then emoji="🟡"
    else emoji="✅"; fi

    cat >> "$output" << EOF
<details>
<summary>$emoji <strong>$name</strong> - $total vulnerabilities ($unique unique CVEs)</summary>

**Image:** \`$image_ref\`
**Digest:** \`@$digest\`

#### Combined (Deduplicated)

| 🚨 Critical | ⚠️ High | 🟡 Medium | 🔵 Low | Total | Unique |
|-------------|---------|-----------|---------|-------|--------|
| $crit | $high | $med | $low | $total | $unique |

EOF

    # Trivy details - use mapped paths from discovery
    trivy_json="${CONTAINER_TO_TRIVY[$name]:-}"

    echo "<details>" >> "$output"
    echo "<summary>🔷 Trivy Scanner ($t_total findings, $t_unique unique)</summary>" >> "$output"
    echo "" >> "$output"

    if [ "$t_total" -eq 0 ]; then
      echo "✅ No vulnerabilities detected by Trivy" >> "$output"
    elif [ -n "$trivy_json" ] && [ -f "$trivy_json" ]; then
      echo "| CVE | Severity | Package | Version | Fixed |" >> "$output"
      echo "|-----|----------|---------|---------|-------|" >> "$output"
      "$TRIVY_PARSER" table "$trivy_json" -l 30 >> "$output" 2>/dev/null || echo "Error parsing results" >> "$output"
      [ "$t_total" -gt 30 ] && echo -e "\n_...and $((t_total - 30)) more_" >> "$output"
    else
      echo "ℹ️ Trivy scanner was not run for this container" >> "$output"
    fi
    echo -e "\n</details>\n" >> "$output"

    # Grype details - use mapped paths from discovery
    grype_json="${CONTAINER_TO_GRYPE[$name]:-}"

    echo "<details>" >> "$output"
    echo "<summary>⚓ Grype Scanner ($g_total findings, $g_unique unique)</summary>" >> "$output"
    echo "" >> "$output"

    if [ "$g_total" -eq 0 ]; then
      echo "✅ No vulnerabilities detected by Grype" >> "$output"
    elif [ -n "$grype_json" ] && [ -f "$grype_json" ]; then
      echo "| CVE | Severity | Package | Version | Fixed |" >> "$output"
      echo "|-----|----------|---------|---------|-------|" >> "$output"
      "$GRYPE_PARSER" table "$grype_json" -l 30 >> "$output" 2>/dev/null || echo "Error parsing results" >> "$output"
      [ "$g_total" -gt 30 ] && echo -e "\n_...and $((g_total - 30)) more_" >> "$output"
    else
      echo "ℹ️ Grype scanner was not run for this container" >> "$output"
    fi
    echo -e "\n</details>\n\n</details>\n" >> "$output"
  done

  # Artifact link
  if [ -n "${GITHUB_REPOSITORY:-}" ] && [ -n "${GITHUB_RUN_ID:-}" ]; then
    echo "**📁 Artifacts:** [Container Scan Reports](https://github.com/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}#artifacts)" >> "$output"
  fi

  [[ "$output" == *"container.md" ]] && echo -e "\n</details>" >> "$output"
done

echo "✅ Combined summary generated for $SCANNED containers"
