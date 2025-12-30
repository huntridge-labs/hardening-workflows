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
 */
function expandEnvVarsInObject(obj) {
  if (typeof obj === 'string') {
    return expandEnvVars(obj, false);
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
 * String format: "nginx:alpine"
 * Structured format: { registry: "docker.io", repository: "library", name: "nginx", tag: "alpine", digest: "sha256:..." }
 *
 * @param {string|object} image - Image reference in string or structured format
 * @returns {string} Full image reference string
 */
function buildImageReference(image) {
  // If image is already a string, return as-is
  if (typeof image === 'string') {
    return image;
  }

  // If image is a structured object, build the reference
  if (typeof image === 'object' && image !== null) {
    const registry = image.registry || 'docker.io';
    const repository = image.repository ? `${image.repository}/` : '';
    const name = image.name;
    const tag = image.tag || 'latest';
    const digest = image.digest ? `@${image.digest}` : '';

    // Construct: registry/repository/name:tag@digest
    let reference = `${registry}/${repository}${name}:${tag}${digest}`;

    // Clean up double slashes (for docker.io/library/ cases)
    reference = reference.replace(/([^:]\/)\/+/g, '$1');

    return reference;
  }

  // Fallback to original value if neither string nor object
  return image;
}

/**
 * Generate matrix from validated config
 * Creates one matrix entry per container (scanners as comma-separated string)
 *
 * NOTE: registry.auth_secret contains the NAME of the GitHub repository secret
 * that should be passed to the container-scan workflow. The workflow will use
 * this to dynamically access secrets via: ${{ secrets[matrix.registry_auth_secret] }}
 */
function generateMatrix(config) {
  const matrix = {
    include: []
  };

  // Generate one matrix entry per container with scanners as comma-separated string
  config.containers.forEach(container => {
    const scanners = container.scanners || ['trivy']; // Default to trivy if not specified

    // Convert structured image format to string if needed
    const imageRef = buildImageReference(container.image);

    const entry = {
      name: container.name,
      scanners: scanners.join(','),  // Convert to comma-separated string for container-scan.yml
      image: imageRef,
      fail_on_severity: container.fail_on_severity || 'high',
      allow_failure: container.allow_failure !== undefined ? container.allow_failure : false,
      enable_code_security: container.enable_code_security === true,
      post_pr_comment: container.post_pr_comment === true,
      registry_username: container.registry_username || '',
      // Extract the secret name from registry config (if present)
      registry_auth_secret: container.registry?.auth_secret || ''
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

module.exports = { loadConfig, validateConfig, generateMatrix, buildImageReference };
