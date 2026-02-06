#!/usr/bin/env bash
# Parse Trivy container scan JSON results
# Usage: parse-trivy-results.sh <command> <json_file> [options]
#
# Commands:
#   counts              - Output "crit high med low" counts
#   total               - Output total vulnerability count
#   unique              - Output unique CVE count
#   unique-by-severity  - Output unique CVEs by severity: "crit high med low"
#   cves                - Output all CVE IDs (one per line)
#   cves-by-severity    - Output CVE IDs for a specific severity (requires -s)
#   table               - Output markdown table of vulnerabilities
#   digest              - Output image digest from metadata
#   image               - Output image:tag reference from metadata
#
# Options:
#   -s, --severity SEV  - Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
#   -l, --limit N       - Limit output rows (default: 50 for table)
#   -h, --help          - Show this help message

set -euo pipefail

show_help() {
    sed -n '2,16p' "$0" | sed 's/^# \?//'
    exit 0
}

# Check if file exists and is valid JSON
validate_file() {
    local file="$1"
    if [[ ! -f "$file" ]] || [[ ! -s "$file" ]]; then
        return 1
    fi
    return 0
}

# Get vulnerability counts by severity: "crit high med low"
get_counts() {
    local file="$1"
    if ! validate_file "$file"; then
        echo "0 0 0 0"
        return
    fi
    jq -r '
        [.Results[]?.Vulnerabilities[]?] |
        group_by(.Severity) |
        map({key: .[0].Severity, value: length}) |
        from_entries |
        "\(.CRITICAL // 0) \(.HIGH // 0) \(.MEDIUM // 0) \(.LOW // 0)"
    ' "$file" 2>/dev/null || echo "0 0 0 0"
}

# Get total vulnerability count
get_total() {
    local file="$1"
    if ! validate_file "$file"; then
        echo "0"
        return
    fi
    jq '[.Results[]?.Vulnerabilities[]?] | length' "$file" 2>/dev/null || echo "0"
}

# Get unique CVE count
get_unique() {
    local file="$1"
    if ! validate_file "$file"; then
        echo "0"
        return
    fi
    jq -r '[.Results[]?.Vulnerabilities[]?.VulnerabilityID] | unique | length' "$file" 2>/dev/null || echo "0"
}

# Get unique CVE counts by severity: "crit high med low"
get_unique_by_severity() {
    local file="$1"
    if ! validate_file "$file"; then
        echo "0 0 0 0"
        return
    fi
    jq -r '
        .Results[]?.Vulnerabilities[]? | {id: .VulnerabilityID, sev: .Severity}
    ' "$file" 2>/dev/null | jq -rs '
        group_by(.sev) |
        map({key: .[0].sev, value: ([.[].id] | unique | length)}) |
        from_entries |
        "\(.CRITICAL // 0) \(.HIGH // 0) \(.MEDIUM // 0) \(.LOW // 0)"
    ' || echo "0 0 0 0"
}

# Get all CVE IDs (one per line, unique)
get_cves() {
    local file="$1"
    if ! validate_file "$file"; then
        return
    fi
    jq -r '[.Results[]?.Vulnerabilities[]?.VulnerabilityID] | unique | .[]' "$file" 2>/dev/null || true
}

# Get CVE IDs for a specific severity
get_cves_by_severity() {
    local file="$1"
    local severity="$2"
    if ! validate_file "$file"; then
        return
    fi
    jq -r --arg sev "$severity" '
        [.Results[]?.Vulnerabilities[]? | select(.Severity == $sev) | .VulnerabilityID] | unique | .[]
    ' "$file" 2>/dev/null || true
}

# Generate markdown table of vulnerabilities
get_table() {
    local file="$1"
    local limit="${2:-50}"
    if ! validate_file "$file"; then
        echo "| No data | - | - | - | - |"
        return
    fi
    jq -r --argjson limit "$limit" '
        [.Results[]?.Vulnerabilities[]?] |
        sort_by(
            if .Severity == "CRITICAL" then 0
            elif .Severity == "HIGH" then 1
            elif .Severity == "MEDIUM" then 2
            else 3 end
        ) |
        .[:$limit] |
        .[] |
        "| \(.VulnerabilityID // "N/A") | \(
            if .Severity == "CRITICAL" then "🚨 CRITICAL"
            elif .Severity == "HIGH" then "⚠️ HIGH"
            elif .Severity == "MEDIUM" then "🟡 MEDIUM"
            else "🔵 LOW" end
        ) | \(.PkgName // "N/A") | \(.InstalledVersion // "N/A") | \(.FixedVersion // "N/A") |"
    ' "$file" 2>/dev/null || echo "| Error parsing | - | - | - | - |"
}

# Get image digest from metadata
get_digest() {
    local file="$1"
    if ! validate_file "$file"; then
        echo "unknown"
        return
    fi
    local digest
    digest=$(jq -r '.Metadata.RepoDigests[0] // .Metadata.ImageID // "unknown"' "$file" 2>/dev/null || echo "unknown")
    # Clean up and extract just the digest part
    digest=$(echo "$digest" | tr -d '\n\r|' | head -c 100)
    if [[ "$digest" == *"@"* ]]; then
        digest="${digest##*@}"
    fi
    echo "$digest"
}

# Get image:tag reference from metadata
get_image_ref() {
    local file="$1"
    if ! validate_file "$file"; then
        echo "unknown"
        return
    fi
    local image_ref
    # Try RepoTags first, then fall back to RepoDigests
    image_ref=$(jq -r '.Metadata.RepoTags[0] // .Metadata.RepoDigests[0] // "unknown"' "$file" 2>/dev/null || echo "unknown")
    # Clean up and extract just the image:tag part (remove digest if present)
    image_ref=$(echo "$image_ref" | tr -d '\n\r|')
    if [[ "$image_ref" == *"@"* ]]; then
        image_ref="${image_ref%%@*}"
    fi
    echo "$image_ref"
}

# Main
main() {
    local command="${1:-}"
    local file="${2:-}"
    local severity=""
    local limit="50"

    # Parse options
    shift 2 2>/dev/null || true
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -s|--severity)
                severity="$2"
                shift 2
                ;;
            -l|--limit)
                limit="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                ;;
            *)
                shift
                ;;
        esac
    done

    case "$command" in
        counts)
            get_counts "$file"
            ;;
        total)
            get_total "$file"
            ;;
        unique)
            get_unique "$file"
            ;;
        unique-by-severity)
            get_unique_by_severity "$file"
            ;;
        cves)
            get_cves "$file"
            ;;
        cves-by-severity)
            if [[ -z "$severity" ]]; then
                echo "Error: -s/--severity required for cves-by-severity" >&2
                exit 1
            fi
            get_cves_by_severity "$file" "$severity"
            ;;
        table)
            get_table "$file" "$limit"
            ;;
        digest)
            get_digest "$file"
            ;;
        image)
            get_image_ref "$file"
            ;;
        -h|--help|help)
            show_help
            ;;
        *)
            echo "Error: Unknown command '$command'" >&2
            echo "Run with --help for usage" >&2
            exit 1
            ;;
    esac
}

main "$@"
