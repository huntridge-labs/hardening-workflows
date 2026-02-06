#!/usr/bin/env bash
# Parse Grype container scan JSON results
# Usage: parse-grype-results.sh <command> <json_file> [options]
#
# Commands:
#   counts              - Output "crit high med low" counts
#   total               - Output total vulnerability count
#   unique              - Output unique CVE count
#   unique-by-severity  - Output unique CVEs by severity: "crit high med low"
#   cves                - Output all CVE IDs (one per line)
#   cves-by-severity    - Output CVE IDs for a specific severity (requires -s)
#   table               - Output markdown table of vulnerabilities
#
# Options:
#   -s, --severity SEV  - Filter by severity (Critical, High, Medium, Low)
#   -l, --limit N       - Limit output rows (default: 50 for table)
#   -h, --help          - Show this help message

set -euo pipefail

show_help() {
    sed -n '2,15p' "$0" | sed 's/^# \?//'
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
        [.matches[]?] |
        group_by(.vulnerability.severity) |
        map({key: .[0].vulnerability.severity, value: length}) |
        from_entries |
        "\(.Critical // 0) \(.High // 0) \(.Medium // 0) \(.Low // 0)"
    ' "$file" 2>/dev/null || echo "0 0 0 0"
}

# Get total vulnerability count
get_total() {
    local file="$1"
    if ! validate_file "$file"; then
        echo "0"
        return
    fi
    jq '[.matches[]?] | length' "$file" 2>/dev/null || echo "0"
}

# Get unique CVE count
get_unique() {
    local file="$1"
    if ! validate_file "$file"; then
        echo "0"
        return
    fi
    jq -r '[.matches[]?.vulnerability.id] | unique | length' "$file" 2>/dev/null || echo "0"
}

# Get unique CVE counts by severity: "crit high med low"
get_unique_by_severity() {
    local file="$1"
    if ! validate_file "$file"; then
        echo "0 0 0 0"
        return
    fi
    jq -r '
        [.matches[]? | {id: .vulnerability.id, sev: .vulnerability.severity}] |
        group_by(.sev) |
        map({key: .[0].sev, value: ([.[].id] | unique | length)}) |
        from_entries |
        "\(.Critical // 0) \(.High // 0) \(.Medium // 0) \(.Low // 0)"
    ' "$file" 2>/dev/null || echo "0 0 0 0"
}

# Get all CVE IDs (one per line, unique)
get_cves() {
    local file="$1"
    if ! validate_file "$file"; then
        return
    fi
    jq -r '[.matches[]?.vulnerability.id] | unique | .[]' "$file" 2>/dev/null || true
}

# Get CVE IDs for a specific severity
get_cves_by_severity() {
    local file="$1"
    local severity="$2"
    if ! validate_file "$file"; then
        return
    fi
    jq -r --arg sev "$severity" '
        [.matches[]? | select(.vulnerability.severity == $sev) | .vulnerability.id] | unique | .[]
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
        [.matches[]?] |
        sort_by(
            if .vulnerability.severity == "Critical" then 0
            elif .vulnerability.severity == "High" then 1
            elif .vulnerability.severity == "Medium" then 2
            else 3 end
        ) |
        .[:$limit] |
        .[] |
        "| \(.vulnerability.id // "N/A") | \(
            if .vulnerability.severity == "Critical" then "🚨 CRITICAL"
            elif .vulnerability.severity == "High" then "⚠️ HIGH"
            elif .vulnerability.severity == "Medium" then "🟡 MEDIUM"
            else "🔵 LOW" end
        ) | \(.artifact.name // "N/A") | \(.artifact.version // "N/A") | \(.vulnerability.fix.versions[0] // "N/A") |"
    ' "$file" 2>/dev/null || echo "| Error parsing | - | - | - | - |"
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
