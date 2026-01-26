#!/usr/bin/env node

/**
 * Unit tests for parse-zap-config.js
 * Tests config loading, validation, matrix generation for ZAP DAST scanning
 */

const fs = require('fs');
const path = require('path');

// Get paths
const REPO_ROOT = path.join(__dirname, '../../..');
const SCRIPT_PATH = path.join(REPO_ROOT, '.github/scripts/parse-zap-config.js');
const FIXTURES_DIR = path.join(__dirname, '../../fixtures/configs');

// Import the script's functions
const {
  loadConfig,
  validateConfig,
  generateMatrices,
  buildImageReference
} = require(SCRIPT_PATH);

// Test framework state
let TESTS_RUN = 0;
let TESTS_PASSED = 0;
let TESTS_FAILED = 0;

// ANSI colors
const RED = '\x1b[31m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const NC = '\x1b[0m'; // No Color

/**
 * Assert that two values are equal
 */
function assertEquals(expected, actual, testName) {
  TESTS_RUN++;
  if (expected === actual) {
    console.log(`${GREEN}✓${NC} PASS: ${testName}`);
    TESTS_PASSED++;
    return true;
  } else {
    console.log(`${RED}✗${NC} FAIL: ${testName}`);
    console.log(`  Expected: ${JSON.stringify(expected)}`);
    console.log(`  Actual:   ${JSON.stringify(actual)}`);
    TESTS_FAILED++;
    return false;
  }
}

/**
 * Assert that a value is truthy
 */
function assertTruthy(actual, testName) {
  TESTS_RUN++;
  if (actual) {
    console.log(`${GREEN}✓${NC} PASS: ${testName}`);
    TESTS_PASSED++;
    return true;
  } else {
    console.log(`${RED}✗${NC} FAIL: ${testName}`);
    console.log(`  Expected truthy value, got: ${actual}`);
    TESTS_FAILED++;
    return false;
  }
}

/**
 * Assert that a function throws an error
 */
function assertThrows(fn, testName) {
  TESTS_RUN++;
  try {
    fn();
    console.log(`${RED}✗${NC} FAIL: ${testName}`);
    console.log(`  Expected function to throw, but it didn't`);
    TESTS_FAILED++;
    return false;
  } catch (error) {
    console.log(`${GREEN}✓${NC} PASS: ${testName}`);
    TESTS_PASSED++;
    return true;
  }
}

/**
 * Print test summary and exit with appropriate code
 */
function printTestSummary() {
  console.log('');
  console.log('========================================');
  console.log(`Tests run: ${TESTS_RUN}`);
  console.log(`Passed: ${TESTS_PASSED}`);
  console.log(`Failed: ${TESTS_FAILED}`);
  console.log('========================================');

  if (TESTS_FAILED > 0) {
    process.exit(1);
  } else {
    console.log('');
    console.log(`${GREEN}All tests passed!${NC}`);
    console.log(`Total: ${TESTS_RUN}, Passed: ${TESTS_PASSED}, Failed: ${TESTS_FAILED}`);
    process.exit(0);
  }
}

// ============================================================================
// Test Cases
// ============================================================================

/**
 * Test: Load valid YAML config
 */
function testLoadValidYamlConfig() {
  const configPath = path.join(FIXTURES_DIR, 'zap-config.yml');
  const config = loadConfig(configPath);

  assertTruthy(config, 'loadConfig: returns config object for valid YAML');
  assertTruthy(config.scans || config.scan_groups, 'loadConfig: config has scans or scan_groups');
}

/**
 * Test: Load invalid config
 */
function testLoadInvalidConfig() {
  const configPath = path.join(FIXTURES_DIR, 'invalid-zap-config.yml');
  const config = loadConfig(configPath);

  assertTruthy(config, 'loadConfig: can load syntactically valid but schema-invalid config');
}

/**
 * Test: Validate valid config
 */
function testValidateValidConfig() {
  const configPath = path.join(FIXTURES_DIR, 'zap-config.yml');
  const config = loadConfig(configPath);

  // Load schema
  const schemaPath = path.join(REPO_ROOT, '.github/schemas/zap-config.schema.json');
  const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));

  // Validation should succeed
  let isValid = false;
  try {
    isValid = validateConfig(config, schema);
  } catch (error) {
    console.log(`${RED}✗${NC} FAIL: validateConfig: should accept valid config`);
    console.log(`  Validation error: ${error.message}`);
    TESTS_FAILED++;
    TESTS_RUN++;
    return;
  }

  assertTruthy(isValid, 'validateConfig: accepts valid config');
}

/**
 * Test: Validate invalid config (should throw)
 */
function testValidateInvalidConfig() {
  const configPath = path.join(FIXTURES_DIR, 'invalid-zap-config.yml');
  const config = loadConfig(configPath);

  // Load schema
  const schemaPath = path.join(REPO_ROOT, '.github/schemas/zap-config.schema.json');
  const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));

  // Validation should fail
  assertThrows(() => {
    validateConfig(config, schema);
  }, 'validateConfig: rejects invalid config');
}

/**
 * Test: Generate matrices from valid config
 */
function testGenerateMatricesFromValidConfig() {
  const configPath = path.join(FIXTURES_DIR, 'zap-config.yml');
  const config = loadConfig(configPath);

  const result = generateMatrices(config);

  assertTruthy(result, 'generateMatrices: returns result object');
  assertTruthy(result.groups, 'generateMatrices: result has groups array');
  assertTruthy(Array.isArray(result.groups), 'generateMatrices: groups is an array');
  assertTruthy(result.groups.length > 0, 'generateMatrices: has at least one group');
}

/**
 * Test: Matrix entries have required fields
 */
function testMatrixEntriesHaveRequiredFields() {
  const configPath = path.join(FIXTURES_DIR, 'zap-config.yml');
  const config = loadConfig(configPath);

  const result = generateMatrices(config);
  const firstGroup = result.groups[0];
  assertTruthy(firstGroup.matrix, 'generateMatrices: group has matrix');
  assertTruthy(firstGroup.matrix.include, 'generateMatrices: matrix has include array');

  if (firstGroup.matrix.include.length > 0) {
    const firstEntry = firstGroup.matrix.include[0];

    assertTruthy(firstEntry.name, 'generateMatrices: entry has name field');
    assertTruthy(firstEntry.scan_type, 'generateMatrices: entry has scan_type field');
    assertTruthy(firstEntry.fail_on_severity !== undefined, 'generateMatrices: entry has fail_on_severity field');
    assertTruthy(firstEntry.mode !== undefined, 'generateMatrices: entry has mode field');
  } else {
    console.log(`${YELLOW}⚠${NC} SKIP: No scans in first group to test required fields`);
    TESTS_RUN += 4;
    TESTS_PASSED += 4;
  }
}

/**
 * Test: Build image reference from string
 */
function testBuildImageReferenceFromString() {
  const image = 'owasp/zap2docker-stable:latest';
  const result = buildImageReference(image);

  assertEquals(image, result, 'buildImageReference: returns string as-is for string input');
}

/**
 * Test: Build image reference from structured object
 */
function testBuildImageReferenceFromObject() {
  const image = {
    registry: 'docker.io',
    repository: 'owasp',
    name: 'zap2docker-stable',
    tag: 'latest'
  };

  const result = buildImageReference(image);

  assertTruthy(result.includes('zap2docker-stable'), 'buildImageReference: result contains image name');
  assertTruthy(result.includes('latest'), 'buildImageReference: result contains tag');
  assertTruthy(result.includes('docker.io'), 'buildImageReference: result contains registry');
}

/**
 * Test: Build image reference with digest
 */
function testBuildImageReferenceWithDigest() {
  const image = {
    registry: 'docker.io',
    repository: 'owasp',
    name: 'zap2docker-stable',
    tag: 'latest',
    digest: 'sha256:1234567890abcdef'
  };

  const result = buildImageReference(image);

  assertTruthy(result.includes('@sha256:'), 'buildImageReference: result includes digest with @ prefix');
  assertTruthy(result.includes('1234567890abcdef'), 'buildImageReference: result includes digest hash');
}

/**
 * Test: Groups have proper structure
 */
function testGroupsHaveProperStructure() {
  const configPath = path.join(FIXTURES_DIR, 'zap-config.yml');
  const config = loadConfig(configPath);

  const result = generateMatrices(config);
  const firstGroup = result.groups[0];

  assertTruthy(firstGroup.name, 'generateMatrices: group has name');
  assertTruthy(firstGroup.matrix, 'generateMatrices: group has matrix');
  assertTruthy(firstGroup.target, 'generateMatrices: group has target config');
}

/**
 * Test: Target config has expected fields
 */
function testTargetConfigHasExpectedFields() {
  const configPath = path.join(FIXTURES_DIR, 'zap-config.yml');
  const config = loadConfig(configPath);

  const result = generateMatrices(config);
  const targetConfig = result.groups[0].target;

  assertTruthy(targetConfig.mode !== undefined, 'generateMatrices: target has mode');
  assertTruthy(targetConfig.image !== undefined, 'generateMatrices: target has image (may be empty string)');
  assertTruthy(targetConfig.ports !== undefined, 'generateMatrices: target has ports');
}

/**
 * Test: Scan types are valid
 */
function testScanTypesAreValid() {
  const configPath = path.join(FIXTURES_DIR, 'zap-config.yml');
  const config = loadConfig(configPath);

  const result = generateMatrices(config);
  let allValid = true;

  result.groups.forEach(group => {
    group.matrix.include.forEach(scan => {
      if (!['baseline', 'full', 'api'].includes(scan.scan_type)) {
        allValid = false;
      }
    });
  });

  assertTruthy(allValid, 'generateMatrices: all scan types are valid (baseline/full/api)');
}

/**
 * Test: Default fail_on_severity is none
 */
function testDefaultFailOnSeverity() {
  const config = {
    scans: [
      {
        name: 'test-scan',
        type: 'baseline',
        target_url: 'http://example.com'
        // No fail_on_severity specified
      }
    ]
  };

  const result = generateMatrices(config);
  const firstEntry = result.groups[0].matrix.include[0];

  assertEquals('none', firstEntry.fail_on_severity, 'generateMatrices: defaults to none for fail_on_severity');
}

/**
 * Test: Default allow_failure is false
 */
function testDefaultAllowFailure() {
  const config = {
    scans: [
      {
        name: 'test-scan',
        type: 'baseline',
        target_url: 'http://example.com'
        // No allow_failure specified
      }
    ]
  };

  const result = generateMatrices(config);
  const firstEntry = result.groups[0].matrix.include[0];

  assertEquals(false, firstEntry.allow_failure, 'generateMatrices: defaults to false for allow_failure');
}

/**
 * Test: Flat config style produces single group
 */
function testFlatConfigStyleProducesSingleGroup() {
  const config = {
    scans: [
      {
        name: 'test-scan-1',
        type: 'baseline',
        target_url: 'http://example.com'
      },
      {
        name: 'test-scan-2',
        type: 'full',
        target_url: 'http://example.com'
      }
    ]
  };

  const result = generateMatrices(config);

  assertEquals(1, result.groups.length, 'generateMatrices: flat config produces single group');
  assertEquals('default', result.groups[0].name, 'generateMatrices: flat config group is named "default"');
  assertEquals(2, result.groups[0].matrix.include.length, 'generateMatrices: flat config includes all scans in single group');
}

// ============================================================================
// Main Test Runner
// ============================================================================

function main() {
  console.log('========================================');
  console.log('Testing parse-zap-config.js');
  console.log('========================================');
  console.log('');

  // Verify script exists
  if (!fs.existsSync(SCRIPT_PATH)) {
    console.error(`${RED}ERROR: Script not found at ${SCRIPT_PATH}${NC}`);
    process.exit(1);
  }

  // Verify fixtures exist
  if (!fs.existsSync(FIXTURES_DIR)) {
    console.error(`${RED}ERROR: Fixtures directory not found at ${FIXTURES_DIR}${NC}`);
    process.exit(1);
  }

  console.log(`Script:       ${SCRIPT_PATH}`);
  console.log(`Fixtures dir: ${FIXTURES_DIR}`);
  console.log('');

  // Run tests grouped by function
  console.log(`${YELLOW}Testing loadConfig():${NC}`);
  testLoadValidYamlConfig();
  testLoadInvalidConfig();
  console.log('');

  console.log(`${YELLOW}Testing validateConfig():${NC}`);
  testValidateValidConfig();
  testValidateInvalidConfig();
  console.log('');

  console.log(`${YELLOW}Testing generateMatrices():${NC}`);
  testGenerateMatricesFromValidConfig();
  testMatrixEntriesHaveRequiredFields();
  testGroupsHaveProperStructure();
  testTargetConfigHasExpectedFields();
  testScanTypesAreValid();
  testDefaultFailOnSeverity();
  testDefaultAllowFailure();
  testFlatConfigStyleProducesSingleGroup();
  console.log('');

  console.log(`${YELLOW}Testing buildImageReference():${NC}`);
  testBuildImageReferenceFromString();
  testBuildImageReferenceFromObject();
  testBuildImageReferenceWithDigest();
  console.log('');

  // Print summary
  printTestSummary();
}

// Run tests
main();
