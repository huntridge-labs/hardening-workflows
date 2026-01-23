# scanner-zap TODO List

Feature parity with scanner-zap.yml reusable workflow

## 1. Scan Mode Support

- [ ] **Add `scan_mode` input** (url, docker-run, compose)
- [ ] **Docker-run mode logic**:
  - [ ] Support `app_image_ref` input for pulling images
  - [ ] Support `app_build_context`, `app_dockerfile`, `app_image_tag` for local builds
  - [ ] Support `app_ports` input for port mappings
  - [ ] Add docker login support (registry_username/password inputs)
  - [ ] Start container with `docker run -d`
  - [ ] Cleanup container on completion (always stop)
- [ ] **Compose mode logic**:
  - [ ] Support `compose_file` input
  - [ ] Support `compose_build` boolean input
  - [ ] Run `docker compose up -d [--build]`
  - [ ] Cleanup with `docker compose down -v`

## 2. Scan Type Support

- [ ] **Add `scan_type` input** (baseline, full, api)
- [ ] **Full scan support**:
  - [ ] Use `zaproxy/action-full-scan@v0.13.0`
  - [ ] Handle same inputs as baseline
- [ ] **API scan support**:
  - [ ] Add `api_spec` input (OpenAPI/Swagger spec URL)
  - [ ] Use `zaproxy/action-api-scan@v0.10.0`
  - [ ] Handle format parameter (openapi)
  - [ ] Update validation to require api_spec for api scans

## 3. Target Readiness

- [ ] **Add `healthcheck_url` input**
- [ ] **Wait for target readiness step**:
  - [ ] Poll healthcheck_url (or target_url if not specified)
  - [ ] 180 second timeout
  - [ ] 3 second retry interval
  - [ ] Use curl with fsS flags

## 4. Outputs & Reporting

- [ ] **Add additional outputs**:
  - [ ] `medium_count` - Number of medium severity findings
  - [ ] `low_count` - Number of low severity findings
  - [ ] `info_count` - Number of informational findings
- [ ] **Update scan summary display**:
  - [ ] Show scan type in title (Baseline/Full/API)
  - [ ] Include scan mode information (docker-run/compose)

## 5. Artifact Naming

- [ ] **Dynamic artifact prefix**:
  - [ ] Hash all inputs (like workflow does)
  - [ ] Use format: `{scan_type}-{hash8}`
  - [ ] Apply to: zap-reports artifact, scanner-summary artifact

## 6. Validation Enhancements

- [ ] **Add scan type validation**:
  - [ ] Require api_spec when scan_type=api
  - [ ] Require target_url when scan_type=baseline or full
- [ ] **Add scan mode validation**:
  - [ ] Require app_image_ref for docker-run mode (or build params)
  - [ ] Require compose_file for compose mode
  - [ ] Check file exists for compose_file

## 7. PR Comment Enhancements

- [ ] **Fix PR comment logic** (currently always string 'true'):
  - [ ] Change input type to string with default 'false'
  - [ ] Compare with `== 'true'` instead of `== true`
- [ ] **Dynamic scan type in comment title**:
  - [ ] Show "Baseline", "Full Scan", or "API Scan"
  - [ ] Use artifact prefix in MARKER (for multi-scan support)
- [ ] **Add timestamp to comment**:
  - [ ] Show "Updated: {date}" at bottom
  - [ ] Link to workflow run

## 8. Input Refinements

- [ ] **Add `allow_failure` input** - Continue on scan failure
- [ ] **Update `target_url` to not be required** - Make conditional based on scan_type
- [ ] **Add secrets support**:
  - [ ] Consider how to handle registry_password (actions don't have secrets)
  - [ ] Document workaround in README

## 9. Cleanup & Error Handling

- [ ] **Always cleanup docker resources**:
  - [ ] Use `if: always()` for docker stop steps
  - [ ] Add continue-on-error for cleanup failures
- [ ] **Better error messages**:
  - [ ] Clear failure messages for missing required inputs per mode
  - [ ] Network troubleshooting info in validation

## 10. Documentation Updates

- [ ] **Update README.md** with:
  - [ ] All three scan modes (url, docker-run, compose)
  - [ ] All three scan types (baseline, full, api)
  - [ ] Full example for each mode
  - [ ] Multi-target workflow pattern
  - [ ] Remove "MVP/Phase 1" language when complete

## 11. Config-Driven Multi-Scan Support

- [ ] **Create parse-zap-config composite action** (mirrors parse-container-config):
  - [ ] Create `.github/actions/parse-zap-config/` directory structure
  - [ ] Create `action.yml` with inputs (config_file) and outputs (matrix, has_scans, scan_count, target config)
  - [ ] Move/copy `parse-zap-config.js` from `.github/scripts/` to action's `scripts/` directory
  - [ ] Move/copy `zap-config.schema.json` from `.github/schemas/` to action's `schemas/` directory
  - [ ] Add Node.js setup and dependency installation (js-yaml, ajv, ajv-formats)
  - [ ] Parse config and output GitHub Actions matrix
  - [ ] Support YAML, JSON, and JS config formats
- [ ] **Matrix output structure**:
  - [ ] Include all scan parameters (name, type, target_url, api_spec, etc.)
  - [ ] Include target configuration (mode, image, ports, compose_file, etc.)
  - [ ] Include registry authentication (registry_host, registry_username, registry_auth_secret)
  - [ ] Include scan options (fail_on_severity, max_duration, rules_file, cmd_options)
- [ ] **Integration patterns**:
  - [ ] Document `secrets: inherit` requirement for dynamic secret resolution
  - [ ] Provide example workflow using parse-zap-config + scanner-zap in matrix
  - [ ] Document how to handle shared target (single docker-run/compose for multiple scans)
- [ ] **Schema validation**:
  - [ ] Validate config against zap-config.schema.json
  - [ ] Provide clear error messages for invalid configs
  - [ ] Support config examples in documentation

---

**Summary**: 11 major feature areas, ~60+ discrete tasks to achieve full parity with scanner-zap.yml reusable workflow plus config-driven multi-scan support.

## Notes

- Current implementation: URL mode + baseline scan only
- Workflow reference: `.github/workflows/scanner-zap.yml`, `.github/workflows/scanner-zap-from-config.yml`
- Scripts: `parse-zap-results.sh`, `generate-zap-summary.sh`, `parse-zap-config.js`
- Schema: `zap-config.schema.json`
- Pattern reference: `.github/actions/parse-container-config/`
