#!/usr/bin/env bash
# Parse ZAP (Zed Attack Proxy) scan JSON results
# Usage: parse-zap-results.sh <command> <json_file> [options]
#
# Commands:
#   counts              - Output "crit high med low" counts (mapped from ZAP severities)
#   counts-with-info     - Output "crit high med low info" counts (mapped from ZAP severities)
#   total               - Output total alert count
#   unique              - Output unique alert count (by pluginid)
#   alerts              - Output all alert names (one per line)
#   table               - Output markdown table of alerts
#   details             - Output detailed nested collapsible sections (requires -s severity -l limit)
#   compact-table       - Output compact table for severity (requires -s severity -l limit)
#   scan-type           - Output scan type metadata if available
#
# Options:
#   -s, --severity SEV  - Filter by severity (Critical, High, Medium, Low)
#   -l, --limit N       - Limit output rows (default: 50 for table)
#   -h, --help          - Show this help message
#
# Note: ZAP severities use 1:1 mapping:
#   ZAP High (riskcode 3)          -> High
#   ZAP Medium (riskcode 2)        -> Medium
#   ZAP Low (riskcode 1)           -> Low
#   ZAP Informational (riskcode 0) -> Informational
# Note: ZAP has no "Critical" level. When fail_on_severity=critical, ZAP High is checked.

set -euo pipefail

show_help() {
    sed -n '2,22p' "$0" | sed 's/^# \?//'
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

# Get alert counts by severity: "crit high med low"
# Uses 1:1 mapping - ZAP has no critical, so critical is always 0
get_counts() {
    local file="$1"
    if ! validate_file "$file"; then
        echo "0 0 0 0"
        return
    fi

    local critical high medium low
    critical=0  # ZAP has no critical severity
    high=$(jq -r '[.site[]?.alerts[]? | select(.riskcode == "3")] | length' "$file" 2>/dev/null || echo "0")
    medium=$(jq -r '[.site[]?.alerts[]? | select(.riskcode == "2")] | length' "$file" 2>/dev/null || echo "0")
    low=$(jq -r '[.site[]?.alerts[]? | select(.riskcode == "1")] | length' "$file" 2>/dev/null || echo "0")
    # Note: riskcode 0 (Informational) is not counted in the standard 4-level output

    echo "$critical $high $medium $low"
}

# Get alert counts including informational: "crit high med low info"
get_counts_with_info() {
    local file="$1"
    if ! validate_file "$file"; then
        echo "0 0 0 0 0"
        return
    fi

    local critical high medium low info
    critical=0  # ZAP has no critical severity
    high=$(jq -r '[.site[]?.alerts[]? | select(.riskcode == "3")] | length' "$file" 2>/dev/null || echo "0")
    medium=$(jq -r '[.site[]?.alerts[]? | select(.riskcode == "2")] | length' "$file" 2>/dev/null || echo "0")
    low=$(jq -r '[.site[]?.alerts[]? | select(.riskcode == "1")] | length' "$file" 2>/dev/null || echo "0")
    info=$(jq -r '[.site[]?.alerts[]? | select(.riskcode == "0")] | length' "$file" 2>/dev/null || echo "0")

    echo "$critical $high $medium $low $info"
}

# Get total alert count
get_total() {
    local file="$1"
    if ! validate_file "$file"; then
        echo "0"
        return
    fi
    jq '[.site[]?.alerts[]?] | length' "$file" 2>/dev/null || echo "0"
}

# Get unique alert count (by pluginid)
get_unique() {
    local file="$1"
    if ! validate_file "$file"; then
        echo "0"
        return
    fi
    jq -r '[.site[]?.alerts[]?.pluginid] | unique | length' "$file" 2>/dev/null || echo "0"
}

# Get all alert names
get_alerts() {
    local file="$1"
    if ! validate_file "$file"; then
        return
    fi
    jq -r '.site[]?.alerts[]?.name' "$file" 2>/dev/null | sort -u
}

# Get alerts by severity (1:1 mapping, critical maps to ZAP High since ZAP has no critical)
get_alerts_by_severity() {
    local file="$1"
    local severity="$2"

    if ! validate_file "$file"; then
        return
    fi

    local riskcode
    case "${severity,,}" in
        critical) riskcode="3" ;;  # ZAP has no critical, use High
        high) riskcode="3" ;;
        medium) riskcode="2" ;;
        low) riskcode="1" ;;
        informational|info) riskcode="0" ;;
        *) echo "Invalid severity: $severity" >&2; return 1 ;;
    esac

    jq -r ".site[]?.alerts[]? | select(.riskcode == \"$riskcode\") | .name" "$file" 2>/dev/null | sort -u
}

# Generate markdown table of alerts
generate_table() {
    local file="$1"
    local limit="${2:-50}"

    if ! validate_file "$file"; then
        return
    fi

    jq -r --argjson limit "$limit" '
        [.site[]?.alerts[]? | {
            name: .name,
            riskcode: (.riskcode | tonumber),
            confidence: .confidence,
            count: (.count // "1"),
            pluginid: .pluginid,
            cweid: .cweid,
            first_url: (.instances[0]?.uri // "N/A")
        }] |
        sort_by(-.riskcode) |
        .[:$limit] |
        .[] |
        # Map severity (1:1 with ZAP levels)
        .severity = (
            if .riskcode == 3 then "⚠️ High"
            elif .riskcode == 2 then "🟡 Medium"
            elif .riskcode == 1 then "🔵 Low"
            elif .riskcode == 0 then "ℹ️ Info"
            else "❓ Unknown" end
        ) |
        .conf = (
            if .confidence == "3" then "High"
            elif .confidence == "2" then "Medium"
            elif .confidence == "1" then "Low"
            else "Unknown" end
        ) |
        "| \(.name) | \(.severity) | \(.conf) | \(.count) | \(.cweid) | \(.first_url) |"
    ' "$file" 2>/dev/null
}

# Get target URL from report
get_target() {
    local file="$1"
    if ! validate_file "$file"; then
        echo "unknown"
        return
    fi
    jq -r '.site[0]."@name" // "unknown"' "$file" 2>/dev/null
}

# Generate detailed vulnerability information for a specific severity
generate_details() {
    local file="$1"
    local severity="$2"
    local limit="${3:-50}"

    if ! validate_file "$file"; then
        return
    fi

    local riskcode
    case "${severity,,}" in
        critical) riskcode="3" ;;  # ZAP has no critical, use High
        high) riskcode="3" ;;
        medium) riskcode="2" ;;
        low) riskcode="1" ;;
        informational|info) riskcode="0" ;;
        *) echo "Invalid severity: $severity" >&2; return 1 ;;
    esac

    jq -r --argjson limit "$limit" --arg riskcode "$riskcode" '
        [.site[]?.alerts[]? | select(.riskcode == $riskcode) | {
            name: .name,
            description: .desc,
            solution: .solution,
            reference: .reference,
            cweid: .cweid,
            wascid: .wascid,
            pluginid: .pluginid,
            instances: [.instances[]? | .uri] | unique | .[0:5]
        }] |
        unique_by(.pluginid) |
        .[:$limit] |
        to_entries[] |
        "<details>\n" +
        "<summary>\(.key + 1). \(.value.name)" +
        (if .value.cweid and .value.cweid != "" then " (CWE-\(.value.cweid))" else "" end) +
        "</summary>\n\n" +
        "**Description:** \(.value.description // "No description available")\n\n" +
        "**Solution:** \(.value.solution // "No solution provided")\n\n" +
        (if (.value.instances | length) > 0 then
            "**Affected URLs:** \(.value.instances | length) location" +
            (if (.value.instances | length) > 1 then "s" else "" end) + "\n" +
            ((.value.instances[] | "- `\(.)`") | @text | . + "\n") +
            "\n"
        else "" end) +
        (if .value.reference and .value.reference != "" then "<details>\n<summary>References</summary>\n\n\(.value.reference)\n\n</details>\n\n" else "" end) +
        "</details>\n\n"
    ' "$file" 2>/dev/null
}

# Generate compact table for a specific severity
generate_compact_table() {
    local file="$1"
    local severity="$2"
    local limit="${3:-50}"

    if ! validate_file "$file"; then
        return
    fi

    local riskcode
    case "${severity,,}" in
        critical) riskcode="3" ;;  # ZAP has no critical, use High
        high) riskcode="3" ;;
        medium) riskcode="2" ;;
        low) riskcode="1" ;;
        informational|info) riskcode="0" ;;
        *) echo "Invalid severity: $severity" >&2; return 1 ;;
    esac

    # Output table header
    echo "| Alert | CWE | Locations | Quick Fix |"
    echo "|-------|-----|-----------|-----------|"

    # Output table rows
    jq -r --argjson limit "$limit" --arg riskcode "$riskcode" '
        [.site[]?.alerts[]? | select(.riskcode == $riskcode) | {
            name: .name,
            solution: .solution,
            cweid: .cweid,
            pluginid: .pluginid,
            count: ([.instances[]?] | length)
        }] |
        unique_by(.pluginid) |
        .[:$limit] |
        .[] |
        # Extract first sentence or up to 80 chars for solution
        .quick_fix = (
            .solution // "No solution provided" |
            gsub("<[^>]*>"; "") |
            split(". ")[0] |
            if length > 80 then .[0:77] + "..." else . end
        ) |
        "| \(.name) | \(.cweid // "N/A") | \(.count) | \(.quick_fix) |"
    ' "$file" 2>/dev/null
}

# Main command dispatcher
main() {
    local cmd="${1:-}"
    local file="${2:-}"

    if [[ "$cmd" == "-h" ]] || [[ "$cmd" == "--help" ]]; then
        show_help
    fi

    if [[ -z "$cmd" ]] || [[ -z "$file" ]]; then
        echo "Error: Missing required arguments" >&2
        show_help
    fi

    shift 2

    # Parse options
    local severity=""
    local limit=50

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
                echo "Unknown option: $1" >&2
                exit 1
                ;;
        esac
    done

    # Execute command
    case "$cmd" in
        counts)
            get_counts "$file"
            ;;
        counts-with-info)
            get_counts_with_info "$file"
            ;;
        total)
            get_total "$file"
            ;;
        unique)
            get_unique "$file"
            ;;
        alerts)
            if [[ -n "$severity" ]]; then
                get_alerts_by_severity "$file" "$severity"
            else
                get_alerts "$file"
            fi
            ;;
        table)
            generate_table "$file" "$limit"
            ;;
        details)
            if [[ -z "$severity" ]]; then
                echo "Error: 'details' command requires -s/--severity option" >&2
                exit 1
            fi
            generate_details "$file" "$severity" "$limit"
            ;;
        compact-table)
            if [[ -z "$severity" ]]; then
                echo "Error: 'compact-table' command requires -s/--severity option" >&2
                exit 1
            fi
            generate_compact_table "$file" "$severity" "$limit"
            ;;
        target)
            get_target "$file"
            ;;
        *)
            echo "Unknown command: $cmd" >&2
            show_help
            ;;
    esac
}

main "$@"
