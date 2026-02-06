#!/usr/bin/env node

/**
 * Container Registry Config Parser (Composite Action Version)
 * Parses YAML, JSON, or JS config files and validates them against the JSON schema
 * Outputs matrix-compatible JSON for GitHub Actions
 *
 * Environment variables:
 *   CONFIG_FILE  - Path to config file (required)
 *   SCHEMA_FILE  - Path to JSON schema (required)
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const Ajv = require('ajv');

// Configuration from environment (only validate when running as main script)
const CONFIG_FILE = process.env.CONFIG_FILE;
const SCHEMA_FILE = process.env.SCHEMA_FILE;

/**
 * Expand environment variables in a string
 * Supports ${VAR_NAME} syntax
 * @param {string} str - String to expand
 */
function expandEnvVars(str) {
  if (typeof str !== 'string') return str;
  return str.replace(/\$\{([^}]+)\}/g, (match, varName) => {
    return process.env[varName] || match;
  });
}

/**
 * Recursively expand environment variables in an object
 * @param {*} obj - Object to expand
 */
function expandEnvVarsInObject(obj) {
  if (typeof obj === 'string') {
    return expandEnvVars(obj);
  } else if (Array.isArray(obj)) {
    return obj.map(item => expandEnvVarsInObject(item));
  } else if (obj !== null && typeof obj === 'object') {
    const result = {};
    for (const [key, value] of Object.entries(obj)) {
      result[key] = expandEnvVarsInObject(value);
    }
    return result;
  }
  return obj;
}

/**
 * Load config file based on extension
 */
function loadConfig(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const content = fs.readFileSync(filePath, 'utf8');

  switch (ext) {
    case '.yml':
    case '.yaml':
      return yaml.load(content);
    case '.json':
      return JSON.parse(content);
    case '.js':
      delete require.cache[require.resolve(path.resolve(filePath))];
      return require(path.resolve(filePath));
    default:
      throw new Error(`Unsupported config file type: ${ext}. Use .yml, .yaml, .json, or .js`);
  }
}

/**
 * Validate config against JSON schema
 */
function validateConfig(config, schema) {
  const ajv = new Ajv({ allErrors: true });
  const validate = ajv.compile(schema);
  const valid = validate(config);

  if (!valid) {
    const errors = validate.errors
      .map(err => `  - ${err.instancePath} ${err.message}`)
      .join('\n');
    throw new Error(`Config validation failed:\n${errors}`);
  }

  // Enforce container name uniqueness
  if (config.containers && Array.isArray(config.containers)) {
    const names = config.containers.map(c => c.name);
    const duplicates = names.filter((name, index) => names.indexOf(name) !== index);

    if (duplicates.length > 0) {
      const uniqueDuplicates = [...new Set(duplicates)];
      throw new Error(`Config validation failed:\n  - containers: Duplicate container names found: ${uniqueDuplicates.join(', ')}. Each container must have a unique name.`);
    }
  }

  return true;
}

/**
 * Convert structured image format to string
 * Supports both simple string format and structured object format
 *
 * @param {string|object} image - Image reference in string or structured format
 * @param {string} registryHost - Registry host from registry.host field
 * @returns {string} Full image reference string
 */
function buildImageReference(image, registryHost = 'docker.io') {
  // If image is already a string, return as-is
  if (typeof image === 'string') {
    return image;
  }

  // If image is a structured object, build the reference
  if (typeof image === 'object' && image !== null) {
    const registry = registryHost || 'docker.io';
    const repository = image.repository ? `${image.repository}/` : '';
    const name = image.name;
    const tag = image.tag || 'latest';
    const digest = image.digest ? `@${image.digest}` : '';

    // Construct: registry/repository/name:tag@digest
    let reference = `${registry}/${repository}${name}:${tag}${digest}`;

    // Clean up double slashes
    reference = reference.replace(/([^:]\/)\/+/g, '$1');

    return reference;
  }

  return image;
}

/**
 * Generate matrix from validated config
 * Creates one matrix entry per container (scanners run sequentially)
 *
 * NOTE: registry.auth_secret contains the NAME of the GitHub secret
 * The caller workflow resolves it via: secrets[matrix.registry_auth_secret]
 */
function generateMatrix(config) {
  const matrix = {
    include: []
  };

  config.containers.forEach(container => {
    const scanners = container.scanners || ['trivy'];
    const imageRef = buildImageReference(container.image, container.registry?.host);

    const entry = {
      name: container.name,
      scanners: scanners.join(','),
      image: imageRef,
      fail_on_severity: container.fail_on_severity || 'high',
      allow_failure: container.allow_failure !== undefined ? container.allow_failure : false,
      enable_code_security: container.enable_code_security === true,
      post_pr_comment: container.post_pr_comment === true,
      registry_username: container.registry?.username || '',
      registry_auth_secret: container.registry?.auth_secret || ''
    };

    matrix.include.push(entry);
  });

  return matrix;
}

/**
 * Generate scan matrix from validated config
 * Creates one matrix entry per container+scanner combination (for parallel scanning)
 *
 * Example output:
 * {
 *   "include": [
 *     { "name": "app", "image": "app:1.0", "scanner": "trivy", ... },
 *     { "name": "app", "image": "app:1.0", "scanner": "grype", ... },
 *     { "name": "db", "image": "db:2.0", "scanner": "trivy", ... }
 *   ]
 * }
 */
function generateScanMatrix(config) {
  const matrix = {
    include: []
  };

  config.containers.forEach(container => {
    const scanners = container.scanners || ['trivy'];
    const imageRef = buildImageReference(container.image, container.registry?.host);

    // Create one entry per scanner for this container
    scanners.forEach(scanner => {
      const entry = {
        name: container.name,
        scanner: scanner,
        image: imageRef,
        fail_on_severity: container.fail_on_severity || 'high',
        allow_failure: container.allow_failure !== undefined ? container.allow_failure : false,
        enable_code_security: container.enable_code_security === true,
        registry_username: container.registry?.username || '',
        registry_auth_secret: container.registry?.auth_secret || ''
      };

      matrix.include.push(entry);
    });
  });

  return matrix;
}

/**
 * Main execution
 */
function main() {
  try {
    console.log(`📦 Loading config from: ${CONFIG_FILE}`);
    let config = loadConfig(CONFIG_FILE);

    console.log('🔧 Expanding environment variables...');
    config = expandEnvVarsInObject(config);

    console.log(`📋 Loading schema from: ${SCHEMA_FILE}`);
    const schema = JSON.parse(fs.readFileSync(SCHEMA_FILE, 'utf8'));

    console.log('✓ Validating config against schema...');
    validateConfig(config, schema);
    console.log('✅ Config validation passed');

    console.log('🔄 Generating matrices...');

    // Sequential matrix (one entry per container)
    const matrix = generateMatrix(config);
    console.log(`✅ Generated ${matrix.include.length} container entries (sequential)`);

    // Parallel scan matrix (one entry per container+scanner)
    const scanMatrix = generateScanMatrix(config);
    console.log(`✅ Generated ${scanMatrix.include.length} scan entries (parallel)`);

    // Output matrices for GitHub Actions
    const matrixJson = JSON.stringify(matrix);
    const scanMatrixJson = JSON.stringify(scanMatrix);

    // Log matrix entries for visibility
    console.log('\nSequential matrix (matrix):');
    matrix.include.forEach((entry, i) => {
      console.log(`  [${i + 1}] ${entry.name}: ${entry.image} (scanners: ${entry.scanners})`);
    });

    console.log('\nParallel matrix (scan_matrix):');
    scanMatrix.include.forEach((entry, i) => {
      console.log(`  [${i + 1}] ${entry.name} + ${entry.scanner}: ${entry.image}`);
    });

    // Set GitHub Actions output
    if (process.env.GITHUB_OUTPUT) {
      fs.appendFileSync(process.env.GITHUB_OUTPUT, `matrix=${matrixJson}\n`);
      fs.appendFileSync(process.env.GITHUB_OUTPUT, `scan_matrix=${scanMatrixJson}\n`);
      console.log('\n✅ Matrix outputs set for GitHub Actions');
    } else {
      // Print matrix if not in GitHub Actions (for local testing)
      console.log('\nMatrix JSON:');
      console.log(matrixJson);
      console.log('\nScan Matrix JSON:');
      console.log(scanMatrixJson);
    }

    process.exit(0);
  } catch (error) {
    console.error(`\n❌ Error: ${error.message}`);
    process.exit(1);
  }
}

// Export functions for testing
module.exports = { loadConfig, validateConfig, generateMatrix, buildImageReference };

// Only run main when executed directly, not when imported for testing
if (require.main === module) {
  // Validate required environment variables
  if (!CONFIG_FILE) {
    console.error('❌ Error: CONFIG_FILE environment variable is required');
    process.exit(1);
  }

  if (!SCHEMA_FILE) {
    console.error('❌ Error: SCHEMA_FILE environment variable is required');
    process.exit(1);
  }

  main();
}
