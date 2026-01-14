#!/usr/bin/env node

/**
 * ZAP DAST Config Parser
 * Parses YAML, JSON, or JS config files and validates them against the JSON schema
 * Outputs matrix-compatible JSON for GitHub Actions
 *
 * Supports two config styles:
 * 1. Flat: `scans` array with optional root `target`
 * 2. Grouped: `scan_groups` array, each with their own `target` and `scans`
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

  // Enforce scan name uniqueness across all scans
  const allScans = [];
  if (config.scans) {
    allScans.push(...config.scans);
  }
  if (config.scan_groups) {
    config.scan_groups.forEach(group => {
      allScans.push(...group.scans);
    });
  }

  const names = allScans.map(s => s.name);
  const duplicates = names.filter((name, index) => names.indexOf(name) !== index);

  if (duplicates.length > 0) {
    const uniqueDuplicates = [...new Set(duplicates)];
    throw new Error(`Config validation failed:\n  - scans: Duplicate scan names found: ${uniqueDuplicates.join(', ')}. Each scan must have a unique name.`);
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
 * Build target configuration object
 */
function buildTargetConfig(target) {
  target = target || {};
  return {
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
}

/**
 * Generate scan entry with defaults applied
 */
function generateScanEntry(scan, defaults, targetConfig, rootConfig) {
  // Merge auth from defaults and scan-specific (scan takes precedence)
  const mergedAuth = { ...(defaults.auth || {}), ...(scan.auth || {}) };

  // post_pr_comment priority: scan-level > defaults > root > false
  const postPrComment = scan.post_pr_comment !== undefined
    ? scan.post_pr_comment
    : (defaults.post_pr_comment !== undefined
        ? defaults.post_pr_comment
        : (rootConfig.post_pr_comment || false));

  return {
    // Scan identification
    name: scan.name,
    scan_type: scan.type,

    // Scan-specific settings (with defaults fallback)
    target_url: scan.target_url || defaults.target_url || '',
    api_spec: scan.api_spec || defaults.api_spec || '',
    healthcheck_url: scan.healthcheck_url || defaults.healthcheck_url || targetConfig.healthcheck_url,
    max_duration_minutes: scan.max_duration_minutes || defaults.max_duration_minutes || 10,
    rules_file: scan.rules_file || defaults.rules_file || '',
    context_file: scan.context_file || defaults.context_file || '',
    cmd_options: scan.cmd_options || defaults.cmd_options || '',

    // Failure handling
    fail_on_severity: scan.fail_on_severity || defaults.fail_on_severity || 'none',
    allow_failure: scan.allow_failure !== undefined ? scan.allow_failure : (defaults.allow_failure || false),

    // PR comment preference (per-scan)
    post_pr_comment: postPrComment,

    // Authentication
    auth_header_name: mergedAuth.header_name || '',
    auth_header_value: mergedAuth.header_value || '',
    auth_header_secret: mergedAuth.header_secret || '',
    auth_header_site: mergedAuth.site || '',

    // Target settings
    ...targetConfig
  };
}

/**
 * Generate matrices from validated config
 * Returns an object with group names as keys and matrices as values
 */
function generateMatrices(config) {
  const rootDefaults = config.defaults || {};
  const rootTarget = buildTargetConfig(config.target);

  // Flat config style: single matrix
  if (config.scans) {
    const matrix = { include: [] };
    config.scans.forEach(scan => {
      matrix.include.push(generateScanEntry(scan, rootDefaults, rootTarget, config));
    });
    return {
      groups: [{
        name: 'default',
        description: 'ZAP Scans',
        matrix: matrix,
        target: rootTarget
      }]
    };
  }

  // Grouped config style: one matrix per group
  if (config.scan_groups) {
    const groups = config.scan_groups.map(group => {
      // Merge group target with root target (group takes precedence)
      const groupTarget = buildTargetConfig({ ...config.target, ...(group.target || {}) });

      // Merge group defaults with root defaults (group takes precedence)
      const groupDefaults = { ...rootDefaults, ...(group.defaults || {}) };

      const matrix = { include: [] };
      group.scans.forEach(scan => {
        matrix.include.push(generateScanEntry(scan, groupDefaults, groupTarget, config));
      });

      return {
        name: group.name,
        description: group.description || group.name,
        matrix: matrix,
        target: groupTarget
      };
    });

    return { groups };
  }

  throw new Error('Config must have either "scans" or "scan_groups"');
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

    console.log('Generating matrices...');
    const result = generateMatrices(config);
    console.log(`Generated ${result.groups.length} group(s)`);

    // Output for GitHub Actions
    const groupsJson = JSON.stringify(result.groups.map(g => ({
      name: g.name,
      description: g.description,
      mode: g.target.mode
    })));

    console.log('\nGroups JSON:');
    console.log(groupsJson);

    result.groups.forEach(group => {
      console.log(`\nMatrix for ${group.name}:`);
      console.log(JSON.stringify(group.matrix));
    });

    if (process.env.GITHUB_OUTPUT) {
      const outputs = [
        `groups=${groupsJson}`,
        `group_count=${result.groups.length}`,
        `has_scans=${result.groups.some(g => g.matrix.include.length > 0) ? 'true' : 'false'}`,
        `total_scan_count=${result.groups.reduce((sum, g) => sum + g.matrix.include.length, 0)}`,
        // Global settings
        `post_pr_comment=${config.post_pr_comment === true ? 'true' : 'false'}`,
        `enable_code_security=${config.enable_code_security === true ? 'true' : 'false'}`
      ];

      // Output each group's matrix and target settings
      result.groups.forEach((group, index) => {
        const prefix = result.groups.length === 1 ? '' : `group_${index}_`;
        outputs.push(`${prefix}matrix=${JSON.stringify(group.matrix)}`);
        outputs.push(`${prefix}name=${group.name}`);
        outputs.push(`${prefix}description=${group.description}`);
        outputs.push(`${prefix}mode=${group.target.mode}`);
        outputs.push(`${prefix}image=${group.target.image}`);
        outputs.push(`${prefix}ports=${group.target.ports}`);
        outputs.push(`${prefix}scan_count=${group.matrix.include.length}`);
      });

      outputs.forEach(output => {
        fs.appendFileSync(process.env.GITHUB_OUTPUT, `${output}\n`);
      });

      console.log('\nOutputs set for GitHub Actions');
    }

    // Print summary
    console.log('\n--- Configuration Summary ---');
    console.log(`Config style: ${config.scan_groups ? 'grouped' : 'flat'}`);
    console.log(`Total groups: ${result.groups.length}`);
    result.groups.forEach(group => {
      console.log(`\n  Group: ${group.name}`);
      console.log(`    Mode: ${group.target.mode}`);
      if (group.target.image) console.log(`    Image: ${group.target.image}`);
      console.log(`    Scans: ${group.matrix.include.length}`);
      group.matrix.include.forEach(scan => {
        const target = scan.scan_type === 'api' ? scan.api_spec : scan.target_url;
        console.log(`      - ${scan.name}: ${scan.scan_type} -> ${target}`);
      });
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

module.exports = { loadConfig, validateConfig, generateMatrices, buildImageReference };
