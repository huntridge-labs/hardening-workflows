#!/usr/bin/env node

/**
 * Container Registry Config Parser
 * Parses YAML, JSON, or JS config files and validates them against the JSON schema
 * Outputs matrix-compatible JSON for GitHub Actions
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const Ajv = require('ajv');

// Configuration
const CONFIG_FILE = process.env.CONFIG_FILE || 'examples/container-config.example.yml';
const SCHEMA_FILE = process.env.SCHEMA_FILE || '.hardening-workflows/.github/schemas/container-config.schema.json'; // Fixed schema path

/**
 * Expand environment variables in a string
 * Supports ${VAR_NAME} syntax
 * @param {string} str - String to expand
 * @param {boolean} preserveSecrets - If true, preserve secret references instead of expanding
 */
function expandEnvVars(str, preserveSecrets = false) {
  if (typeof str !== 'string') return str;
  return str.replace(/\$\{([^}]+)\}/g, (match, varName) => {
    // If preserveSecrets is true, return the variable name instead of the value
    if (preserveSecrets) {
      return varName;
    }
    return process.env[varName] || match;
  });
}

/**
 * Recursively expand environment variables in an object
 * @param {*} obj - Object to expand
 * @param {string} currentKey - Current key being processed (for secret detection)
 */
function expandEnvVarsInObject(obj, currentKey = '') {
  // Secret-related keys that should preserve variable names in matrix output
  const secretKeys = ['registry_password', 'registry_token', 'password', 'token', 'secret', 'key'];
  const isSecretField = secretKeys.some(k => currentKey.toLowerCase().includes(k));

  if (typeof obj === 'string') {
    return expandEnvVars(obj, isSecretField);
  } else if (Array.isArray(obj)) {
    return obj.map(item => expandEnvVarsInObject(item, currentKey));
  } else if (obj !== null && typeof obj === 'object') {
    const result = {};
    for (const [key, value] of Object.entries(obj)) {
      result[key] = expandEnvVarsInObject(value, key);
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
      // Clear require cache to allow dynamic reloading
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

  return true;
}

/**
 * Generate matrix from validated config
 * Creates one matrix entry per container (scanners as comma-separated string)
 *
 * NOTE: registry_password contains the SECRET NAME (e.g., "DOCKERHUB_TOKEN"),
 * not the actual secret value. Since container-scan-from-config.yml is designed
 * to be copied and customized, users can wire up per-registry secrets by:
 * 1. Adding secrets to the env block in parse-config job
 * 2. Referencing them in config: registry_password: ${DOCKERHUB_TOKEN}
 * 3. Modifying their workflow copy to pass the appropriate secrets
 */
function generateMatrix(config) {
  const matrix = {
    include: []
  };

  // Generate one matrix entry per container with scanners as comma-separated string
  config.containers.forEach(container => {
    const scanners = container.scanners || ['trivy']; // Default to trivy if not specified

    const entry = {
      name: container.name,
      scanners: scanners.join(','),  // Convert to comma-separated string for container-scan.yml
      image: container.image,
      fail_on_severity: container.fail_on_severity || 'high',
      enable_code_security: container.enable_code_security !== false,
      post_pr_comment: container.post_pr_comment === true,
      registry_username: container.registry_username || '',
      // Contains the SECRET NAME from config (e.g., "DOCKERHUB_TOKEN"), not the value
      registry_password: container.registry_password || ''
    };

    matrix.include.push(entry);
  });

  return matrix;
}

/**
 * Main execution
 */
function main() {
  try {
    console.log(`Loading config from: ${CONFIG_FILE}`);
    let config = loadConfig(CONFIG_FILE);

    console.log('Expanding environment variables...');
    config = expandEnvVarsInObject(config);
    console.log('✓ Environment variables expanded');

    console.log(`Loading schema from: ${SCHEMA_FILE}`);
    const schema = JSON.parse(fs.readFileSync(SCHEMA_FILE, 'utf8'));

    console.log('Validating config against schema...');
    validateConfig(config, schema);
    console.log('✓ Config validation passed');

    console.log('Generating matrix...');
    const matrix = generateMatrix(config);
    console.log(`✓ Generated ${matrix.include.length} matrix entries`);

    // Output matrix for GitHub Actions
    const matrixJson = JSON.stringify(matrix);
    console.log('\nMatrix JSON:');
    console.log(matrixJson);

    // Set GitHub Actions output if running in GHA
    if (process.env.GITHUB_OUTPUT) {
      fs.appendFileSync(process.env.GITHUB_OUTPUT, `matrix=${matrixJson}\n`);
      console.log('\n✓ Matrix output set for GitHub Actions');
    }

    process.exit(0);
  } catch (error) {
    console.error(`\n❌ Error: ${error.message}`);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { loadConfig, validateConfig, generateMatrix };
