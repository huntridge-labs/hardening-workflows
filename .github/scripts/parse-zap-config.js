#!/usr/bin/env node

/**
 * ZAP DAST Config Parser
 * Parses YAML, JSON, or JS config files and validates them against the JSON schema
 * Outputs matrix-compatible JSON for GitHub Actions
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const Ajv = require('ajv');
const addFormats = require('ajv-formats');

// Configuration from environment
const CONFIG_FILE = process.env.CONFIG_FILE || 'examples/zap-config.example.yml';
const SCHEMA_FILE = process.env.SCHEMA_FILE || '.hardening-workflows/.github/schemas/zap-config.schema.json';

/**
 * Expand environment variables in a string
 * Supports ${VAR_NAME} syntax
 */
function expandEnvVars(str, preserveSecrets = false) {
  if (typeof str !== 'string') return str;
  return str.replace(/\$\{([^}]+)\}/g, (match, varName) => {
    if (preserveSecrets) {
      return varName;
    }
    return process.env[varName] || match;
  });
}

/**
 * Recursively expand environment variables in an object
 * Skip auth_secret and password_secret fields (those are secret names, not values)
 */
function expandEnvVarsInObject(obj, skipSecretFields = true) {
  if (typeof obj === 'string') {
    return expandEnvVars(obj, false);
  } else if (Array.isArray(obj)) {
    return obj.map(item => expandEnvVarsInObject(item, skipSecretFields));
  } else if (obj !== null && typeof obj === 'object') {
    const result = {};
    for (const [key, value] of Object.entries(obj)) {
      // Don't expand secret field names - they're references, not values
      if (skipSecretFields && (key === 'auth_secret' || key === 'header_secret')) {
        result[key] = value;
      } else {
        result[key] = expandEnvVarsInObject(value, skipSecretFields);
      }
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
  const ajv = new Ajv({ allErrors: true, strict: false });
  addFormats(ajv);
  const validate = ajv.compile(schema);
  const valid = validate(config);

  if (!valid) {
    const errors = validate.errors
      .map(err => `  - ${err.instancePath} ${err.message}`)
      .join('\n');
    throw new Error(`Config validation failed:\n${errors}`);
  }

  // Enforce scan name uniqueness
  if (config.scans && Array.isArray(config.scans)) {
    const names = config.scans.map(s => s.name);
    const duplicates = names.filter((name, index) => names.indexOf(name) !== index);

    if (duplicates.length > 0) {
      const uniqueDuplicates = [...new Set(duplicates)];
      throw new Error(`Config validation failed:\n  - scans: Duplicate scan names found: ${uniqueDuplicates.join(', ')}. Each scan must have a unique name.`);
    }
  }

  return true;
}

/**
 * Build container image reference from structured format
 */
function buildImageReference(image) {
  if (typeof image === 'string') {
    return image;
  }

  if (typeof image === 'object' && image !== null) {
    const registry = image.registry || '';
    const repository = image.repository ? `${image.repository}/` : '';
    const name = image.name;
    const tag = image.tag || 'latest';
    const digest = image.digest ? `@${image.digest}` : '';

    let reference = '';
    if (registry) {
      reference = `${registry}/${repository}${name}:${tag}${digest}`;
    } else {
      reference = `${repository}${name}:${tag}${digest}`;
    }

    // Clean up double slashes
    reference = reference.replace(/([^:]\/)\/+/g, '$1');
    return reference;
  }

  return image;
}

/**
 * Convert ports to normalized array format
 */
function normalizePorts(ports) {
  if (!ports) return ['8080:8080'];
  if (typeof ports === 'string') {
    return ports.split(',').map(p => p.trim()).filter(p => p);
  }
  if (Array.isArray(ports)) {
    return ports.map(p => p.toString().trim()).filter(p => p);
  }
  return ['8080:8080'];
}

/**
 * Generate matrix from validated config
 * Creates one matrix entry per scan
 */
function generateMatrix(config) {
  const matrix = { include: [] };
  const target = config.target || {};
  const defaults = config.defaults || {};

  // Build shared target configuration
  const sharedTarget = {
    mode: target.mode || 'url',
    image: target.image ? buildImageReference(target.image) : '',
    ports: normalizePorts(target.ports).join(','),
    build_context: target.build?.context || '',
    build_dockerfile: target.build?.dockerfile || '',
    build_tag: target.build?.tag || '',
    compose_file: target.compose_file || 'docker-compose.yml',
    compose_build: target.compose_build !== false,
    registry_host: target.registry?.host || '',
    registry_username: target.registry?.username || '',
    registry_auth_secret: target.registry?.auth_secret || '',
    healthcheck_url: target.healthcheck_url || ''
  };

  // Generate matrix entries for each scan
  config.scans.forEach(scan => {
    const entry = {
      // Scan identification
      name: scan.name,
      scan_type: scan.type,

      // Scan-specific settings
      target_url: scan.target_url || '',
      api_spec: scan.api_spec || '',
      healthcheck_url: scan.healthcheck_url || sharedTarget.healthcheck_url,
      max_duration_minutes: scan.max_duration_minutes || defaults.max_duration_minutes || 10,
      rules_file: scan.rules_file || '',
      context_file: scan.context_file || '',
      cmd_options: scan.cmd_options || '',

      // Failure handling
      fail_on_severity: scan.fail_on_severity || defaults.fail_on_severity || 'none',
      allow_failure: scan.allow_failure !== undefined ? scan.allow_failure : (defaults.allow_failure || false),

      // Authentication (header-based auth supported by ZAP actions)
      // ZAP env vars: ZAP_AUTH_HEADER, ZAP_AUTH_HEADER_VALUE, ZAP_AUTH_HEADER_SITE
      auth_header_name: scan.auth?.header_name || '',
      auth_header_value: scan.auth?.header_value || '',
      auth_header_secret: scan.auth?.header_secret || '',
      auth_header_site: scan.auth?.site || '',

      // Shared target settings (copied to each matrix entry)
      ...sharedTarget
    };

    matrix.include.push(entry);
  });

  return matrix;
}

/**
 * Generate shared outputs for target configuration
 */
function generateTargetOutputs(config) {
  const target = config.target || {};

  return {
    mode: target.mode || 'url',
    image: target.image ? buildImageReference(target.image) : '',
    ports: normalizePorts(target.ports).join(','),
    build_context: target.build?.context || '',
    build_dockerfile: target.build?.dockerfile || '',
    build_tag: target.build?.tag || '',
    compose_file: target.compose_file || 'docker-compose.yml',
    compose_build: target.compose_build !== false ? 'true' : 'false',
    registry_host: target.registry?.host || '',
    registry_username: target.registry?.username || '',
    registry_auth_secret: target.registry?.auth_secret || '',
    healthcheck_url: target.healthcheck_url || '',
    post_pr_comment: config.post_pr_comment === true ? 'true' : 'false',
    enable_code_security: config.enable_code_security === true ? 'true' : 'false'
  };
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
    console.log('Environment variables expanded');

    console.log(`Loading schema from: ${SCHEMA_FILE}`);
    const schema = JSON.parse(fs.readFileSync(SCHEMA_FILE, 'utf8'));

    console.log('Validating config against schema...');
    validateConfig(config, schema);
    console.log('Config validation passed');

    console.log('Generating matrix...');
    const matrix = generateMatrix(config);
    console.log(`Generated ${matrix.include.length} matrix entries`);

    console.log('Generating target outputs...');
    const targetOutputs = generateTargetOutputs(config);

    // Output for GitHub Actions
    const matrixJson = JSON.stringify(matrix);
    console.log('\nMatrix JSON:');
    console.log(matrixJson);

    if (process.env.GITHUB_OUTPUT) {
      const outputs = [
        `matrix=${matrixJson}`,
        `has_scans=${matrix.include.length > 0 ? 'true' : 'false'}`,
        `scan_count=${matrix.include.length}`,
        ...Object.entries(targetOutputs).map(([key, value]) => `target_${key}=${value}`)
      ];

      outputs.forEach(output => {
        fs.appendFileSync(process.env.GITHUB_OUTPUT, `${output}\n`);
      });

      console.log('\nOutputs set for GitHub Actions');
    }

    // Print summary
    console.log('\n--- Configuration Summary ---');
    console.log(`Target mode: ${targetOutputs.mode}`);
    if (targetOutputs.image) console.log(`Target image: ${targetOutputs.image}`);
    console.log(`Scans configured: ${matrix.include.length}`);
    matrix.include.forEach(scan => {
      const target = scan.scan_type === 'api' ? scan.api_spec : scan.target_url;
      console.log(`  - ${scan.name}: ${scan.scan_type} scan -> ${target}`);
    });

    process.exit(0);
  } catch (error) {
    console.error(`\nError: ${error.message}`);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { loadConfig, validateConfig, generateMatrix, buildImageReference };
