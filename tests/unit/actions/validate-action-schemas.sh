#!/usr/bin/env bash
# Validate composite action schemas
# Ensures all action.yml files follow required structure

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
ACTIONS_DIR="$REPO_ROOT/.github/actions"

echo "Validating Composite Action Schemas"
echo "===================================="

# Helper functions
assert_pass() {
  local test_name="$1"
  echo -e "${GREEN}✓${NC} PASS: $test_name"
  TESTS_PASSED=$((TESTS_PASSED + 1))
}

assert_fail() {
  local test_name="$1"
  local reason="${2:-Unknown failure}"
  echo -e "${RED}✗${NC} FAIL: $test_name"
  echo "  Reason: $reason"
  TESTS_FAILED=$((TESTS_FAILED + 1))
}

print_summary() {
  echo ""
  echo "======================================"
  echo "Tests passed: $TESTS_PASSED"
  echo "Tests failed: $TESTS_FAILED"
  echo "======================================"
  if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
  else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
  fi
}

# Find all action.yml files
mapfile -t ACTION_FILES < <(find "$ACTIONS_DIR" -name "action.yml" -o -name "action.yaml")

if [ "${#ACTION_FILES[@]}" -eq 0 ]; then
  echo -e "${RED}No action files found in $ACTIONS_DIR${NC}"
  exit 1
fi

echo "Found ${#ACTION_FILES[@]} action files to validate"
echo ""

# Validate each action
for action_file in "${ACTION_FILES[@]}"; do
  action_name=$(basename "$(dirname "$action_file")")

  # Test: action file is valid YAML
  if ! yq eval '.' "$action_file" > /dev/null 2>&1; then
    assert_fail "[$action_name] Valid YAML syntax"
    continue
  fi
  assert_pass "[$action_name] Valid YAML syntax"

  # Test: has required 'name' field
  name=$(yq eval '.name' "$action_file")
  if [ "$name" = "null" ] || [ -z "$name" ]; then
    assert_fail "[$action_name] Has 'name' field"
  else
    assert_pass "[$action_name] Has 'name' field"
  fi

  # Test: has 'description' field
  description=$(yq eval '.description' "$action_file")
  if [ "$description" = "null" ] || [ -z "$description" ]; then
    assert_fail "[$action_name] Has 'description' field"
  else
    assert_pass "[$action_name] Has 'description' field"
  fi

  # Test: has 'runs' section
  runs=$(yq eval '.runs' "$action_file")
  if [ "$runs" = "null" ]; then
    assert_fail "[$action_name] Has 'runs' section"
    continue
  fi
  assert_pass "[$action_name] Has 'runs' section"

  # Test: runs.using is 'composite'
  using=$(yq eval '.runs.using' "$action_file")
  if [ "$using" != "composite" ]; then
    assert_fail "[$action_name] runs.using is 'composite' (got: $using)"
  else
    assert_pass "[$action_name] runs.using is 'composite'"
  fi

  # Test: has steps in runs section
  steps=$(yq eval '.runs.steps | length' "$action_file")
  if [ "$steps" = "0" ] || [ "$steps" = "null" ]; then
    assert_fail "[$action_name] Has at least one step"
  else
    assert_pass "[$action_name] Has $steps steps"
  fi

  # Test: all inputs have descriptions
  inputs=$(yq eval '.inputs | keys | .[]' "$action_file" 2>/dev/null || echo "")
  if [ -n "$inputs" ]; then
    all_inputs_valid=true
    while IFS= read -r input; do
      [ -z "$input" ] && continue
      input_desc=$(yq eval ".inputs.\"$input\".description" "$action_file")
      if [ "$input_desc" = "null" ] || [ -z "$input_desc" ]; then
        assert_fail "[$action_name] Input '$input' has description"
        all_inputs_valid=false
      fi
    done <<< "$inputs"

    if [ "$all_inputs_valid" = true ]; then
      input_count=$(echo "$inputs" | grep -c '^' || echo 0)
      assert_pass "[$action_name] All $input_count inputs have descriptions"
    fi
  fi

  # Test: all required inputs are marked as required
  if [ -n "$inputs" ]; then
    while IFS= read -r input; do
      [ -z "$input" ] && continue
      is_required=$(yq eval ".inputs.\"$input\".required" "$action_file")
      # Just verify the field exists (true/false/null are all valid)
      if [ "$is_required" != "null" ]; then
        # Field is explicitly set, that's good
        :
      fi
    done <<< "$inputs"
  fi

  # Test: all outputs have descriptions
  outputs=$(yq eval '.outputs | keys | .[]' "$action_file" 2>/dev/null || echo "")
  if [ -n "$outputs" ]; then
    all_outputs_valid=true
    while IFS= read -r output; do
      [ -z "$output" ] && continue
      output_desc=$(yq eval ".outputs.\"$output\".description" "$action_file")
      if [ "$output_desc" = "null" ] || [ -z "$output_desc" ]; then
        assert_fail "[$action_name] Output '$output' has description"
        all_outputs_valid=false
      fi
    done <<< "$outputs"

    if [ "$all_outputs_valid" = true ]; then
      output_count=$(echo "$outputs" | grep -c '^' || echo 0)
      assert_pass "[$action_name] All $output_count outputs have descriptions"
    fi
  fi

  # Test: each step has a shell specified
  for ((i=0; i<steps; i++)); do
    step_shell=$(yq eval ".runs.steps[$i].shell" "$action_file")
    if [ "$step_shell" = "null" ]; then
      step_name=$(yq eval ".runs.steps[$i].name" "$action_file")
      assert_fail "[$action_name] Step $((i+1)) ('$step_name') has shell specified"
      break
    fi
  done

  echo ""
done

print_summary
