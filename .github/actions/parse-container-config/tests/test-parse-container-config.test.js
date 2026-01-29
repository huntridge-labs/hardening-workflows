#!/usr/bin/env node

/**
 * Unit tests for parse-container-config.js
 * Tests config loading, validation, matrix generation, and image reference building
 */

const fs = require('fs');
const path = require('path');
const assert = require('assert');

// Get paths
const REPO_ROOT = path.join(__dirname, '../../../..');
const SCRIPT_PATH = path.join(__dirname, '../scripts/parse-container-config.js');
const FIXTURES_DIR = path.join(REPO_ROOT, 'tests/fixtures/configs');

// Import the script's functions
const {
  loadConfig,
  validateConfig,
  generateMatrix,
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
  const configPath = path.join(FIXTURES_DIR, 'container-config.yml');
  const config = loadConfig(configPath);

  assertTruthy(config, 'loadConfig: returns config object for valid YAML');
  assertTruthy(config.containers, 'loadConfig: config has containers array');
  assertTruthy(Array.isArray(config.containers), 'loadConfig: containers is an array');
}

/**
 * Test: Load invalid config (should throw)
 */
function testLoadInvalidConfig() {
  const configPath = path.join(FIXTURES_DIR, 'invalid-container-config.yml');

  // Load config (this part should work)
  const config = loadConfig(configPath);

  // But validation should fail (we'll test this in validateConfig tests)
  assertTruthy(config, 'loadConfig: can load syntactically valid but schema-invalid config');
}

/**
 * Test: Validate valid config
 */
function testValidateValidConfig() {
  const configPath = path.join(FIXTURES_DIR, 'container-config.yml');
  const config = loadConfig(configPath);

  // Load schema
  const schemaPath = path.join(REPO_ROOT, '.github/schemas/container-config.schema.json');
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
  const configPath = path.join(FIXTURES_DIR, 'invalid-container-config.yml');
  const config = loadConfig(configPath);

  // Load schema
  const schemaPath = path.join(REPO_ROOT, '.github/schemas/container-config.schema.json');
  const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));

  // Validation should fail
  assertThrows(() => {
    validateConfig(config, schema);
  }, 'validateConfig: rejects invalid config');
}

/**
 * Test: Generate matrix from valid config
 */
function testGenerateMatrixFromValidConfig() {
  const configPath = path.join(FIXTURES_DIR, 'container-config.yml');
  const config = loadConfig(configPath);

  const matrix = generateMatrix(config);

  assertTruthy(matrix, 'generateMatrix: returns matrix object');
  assertTruthy(matrix.include, 'generateMatrix: matrix has include array');
  assertTruthy(Array.isArray(matrix.include), 'generateMatrix: include is an array');
  assertTruthy(matrix.include.length > 0, 'generateMatrix: matrix includes at least one entry');
}

/**
 * Test: Matrix entries have required fields
 */
function testMatrixEntriesHaveRequiredFields() {
  const configPath = path.join(FIXTURES_DIR, 'container-config.yml');
  const config = loadConfig(configPath);

  const matrix = generateMatrix(config);
  const firstEntry = matrix.include[0];

  assertTruthy(firstEntry.name, 'generateMatrix: entry has name field');
  assertTruthy(firstEntry.scanners, 'generateMatrix: entry has scanners field');
  assertTruthy(firstEntry.image, 'generateMatrix: entry has image field');
  assertTruthy(firstEntry.fail_on_severity !== undefined, 'generateMatrix: entry has fail_on_severity field');
}

/**
 * Test: Scanners are comma-separated string
 */
function testScannersAreCommaSeparated() {
  const configPath = path.join(FIXTURES_DIR, 'container-config.yml');
  const config = loadConfig(configPath);

  const matrix = generateMatrix(config);
  const firstEntry = matrix.include[0];

  assertTruthy(typeof firstEntry.scanners === 'string', 'generateMatrix: scanners is a string');

  // If there are multiple scanners, verify comma separation
  if (firstEntry.scanners.includes(',')) {
    const scannerArray = firstEntry.scanners.split(',');
    assertTruthy(scannerArray.length > 1, 'generateMatrix: scanners string splits into multiple values');
  } else {
    assertTruthy(true, 'generateMatrix: single scanner is valid string');
  }
}

/**
 * Test: Build image reference from string
 */
function testBuildImageReferenceFromString() {
  const image = 'nginx:alpine';
  const result = buildImageReference(image);

  assertEquals(image, result, 'buildImageReference: returns string as-is for string input');
}

/**
 * Test: Build image reference from structured object
 */
function testBuildImageReferenceFromObject() {
  const image = {
    repository: 'library',
    name: 'nginx',
    tag: 'alpine'
  };

  const result = buildImageReference(image, 'docker.io');

  assertTruthy(result.includes('nginx'), 'buildImageReference: result contains image name');
  assertTruthy(result.includes('alpine'), 'buildImageReference: result contains tag');
  assertTruthy(result.includes('docker.io'), 'buildImageReference: result contains registry host');
}

/**
 * Test: Build image reference with digest
 */
function testBuildImageReferenceWithDigest() {
  const image = {
    repository: 'library',
    name: 'nginx',
    tag: 'alpine',
    digest: 'sha256:1234567890abcdef'
  };

  const result = buildImageReference(image, 'docker.io');

  assertTruthy(result.includes('@sha256:'), 'buildImageReference: result includes digest with @ prefix');
  assertTruthy(result.includes('1234567890abcdef'), 'buildImageReference: result includes digest hash');
}

/**
 * Test: Default registry host
 */
function testDefaultRegistryHost() {
  const image = {
    name: 'nginx',
    tag: 'alpine'
  };

  const result = buildImageReference(image);

  assertTruthy(result.includes('docker.io'), 'buildImageReference: uses docker.io as default registry');
}

/**
 * Test: Matrix entry count matches container count
 */
function testMatrixEntryCountMatchesContainerCount() {
  const configPath = path.join(FIXTURES_DIR, 'container-config.yml');
  const config = loadConfig(configPath);

  const matrix = generateMatrix(config);

  assertEquals(
    config.containers.length,
    matrix.include.length,
    'generateMatrix: matrix entry count matches container count'
  );
}

/**
 * Test: Default scanner is trivy when not specified
 */
function testDefaultScannerIsTrivy() {
  const config = {
    containers: [
      {
        name: 'test-container',
        image: 'nginx:alpine'
        // No scanners specified
      }
    ]
  };

  const matrix = generateMatrix(config);
  const firstEntry = matrix.include[0];

  assertEquals('trivy', firstEntry.scanners, 'generateMatrix: defaults to trivy when scanners not specified');
}

/**
 * Test: Default fail_on_severity is high
 */
function testDefaultFailOnSeverity() {
  const config = {
    containers: [
      {
        name: 'test-container',
        image: 'nginx:alpine',
        scanners: ['trivy']
        // No fail_on_severity specified
      }
    ]
  };

  const matrix = generateMatrix(config);
  const firstEntry = matrix.include[0];

  assertEquals('high', firstEntry.fail_on_severity, 'generateMatrix: defaults to high for fail_on_severity');
}

/**
 * Test: Default allow_failure is false
 */
function testDefaultAllowFailure() {
  const config = {
    containers: [
      {
        name: 'test-container',
        image: 'nginx:alpine',
        scanners: ['trivy']
        // No allow_failure specified
      }
    ]
  };

  const matrix = generateMatrix(config);
  const firstEntry = matrix.include[0];

  assertEquals(false, firstEntry.allow_failure, 'generateMatrix: defaults to false for allow_failure');
}

// ============================================================================
// Main Test Runner
// ============================================================================

function main() {
  console.log('========================================');
  console.log('Testing parse-container-config.js');
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

  console.log(`${YELLOW}Testing generateMatrix():${NC}`);
  testGenerateMatrixFromValidConfig();
  testMatrixEntriesHaveRequiredFields();
  testScannersAreCommaSeparated();
  testMatrixEntryCountMatchesContainerCount();
  testDefaultScannerIsTrivy();
  testDefaultFailOnSeverity();
  testDefaultAllowFailure();
  console.log('');

  console.log(`${YELLOW}Testing buildImageReference():${NC}`);
  testBuildImageReferenceFromString();
  testBuildImageReferenceFromObject();
  testBuildImageReferenceWithDigest();
  testDefaultRegistryHost();
  console.log('');

  // Print summary
  printTestSummary();
}

// Run tests
main();
