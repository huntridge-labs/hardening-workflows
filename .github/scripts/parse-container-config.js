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
 */
function expandEnvVars(str) {
  if (typeof str !== 'string') return str;
  return str.replace(/\$\{([^}]+)\}/g, (match, varName) => {
    return process.env[varName] || match;
  });
}

/**
 * Recursively expand environment variables in an object
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
 */
function generateMatrix(config) {
  const matrix = {
    include: []
  };

  // Generate matrix entries for each container and scanner combination
  config.containers.forEach(container => {
    const scanners = container.scanners || ['trivy']; // Default to trivy if not specified

    scanners.forEach(scanner => {
      const entry = {
        name: container.name,
        scanner: scanner,
        image: container.image,
        fail_on_severity: container.fail_on_severity || 'high',
        enable_code_security: container.enable_code_security !== false,
        post_pr_comment: container.post_pr_comment === true,
        registry_username: container.registry_username || '',
        registry_password: container.registry_password || ''
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
