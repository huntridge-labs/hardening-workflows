# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).



## [2.11.0](https://github.com/huntridge-labs/hardening-workflows/compare/2.10.0...2.11.0) (2026-01-15)

### Features

* Enhance ZAP scanning workflows with multiple methods and configuration options ([a8ee3fa](https://github.com/huntridge-labs/hardening-workflows/commit/a8ee3fa9ba44053ca294cf4fe3f30c64e13acb4d))
* **husky:** enhance commit hooks with environment checks and improved error handling ([af495b0](https://github.com/huntridge-labs/hardening-workflows/commit/af495b0b80b857598bc45e7173d6eebcc46e95ca))
* **zap:** add ZAP DAST scanner with config-file support ([79dbc29](https://github.com/huntridge-labs/hardening-workflows/commit/79dbc2998a0c6f83e77d44176ea38fc67bd15fe0))

### Bug Fixes

* **release-it.json:** scanner-zap.yml version not updating ([0c90612](https://github.com/huntridge-labs/hardening-workflows/commit/0c90612a2e82a418ff795084dc6bbf9fcef18837))

### Maintenance

* **dependencies:** update ajv, ajv-formats, and js-yaml versions ([83a617a](https://github.com/huntridge-labs/hardening-workflows/commit/83a617a972eaaa4f268d9eb083594c37ac2d3d83))
* **example-zap:** update workflow to default to 'all' scan type and enhance condition checks ([7f2b5ec](https://github.com/huntridge-labs/hardening-workflows/commit/7f2b5ec147b2e10d4f546e29e22a4c9ecf7de45f))
* **release-it.json:** remove extra scanner-zap config ([b17a6f9](https://github.com/huntridge-labs/hardening-workflows/commit/b17a6f9c978fe39da0774c3ac4130ff4ab647b3a))
* **scanner-zap:** add example workflow for ZAP scanning methods and update config examples ([4987a9a](https://github.com/huntridge-labs/hardening-workflows/commit/4987a9aa27bdbf61c2f3304ff86dc4a7bb881c11))
* **scanner-zap:** enhance matrix output with combined group metadata ([eee09f5](https://github.com/huntridge-labs/hardening-workflows/commit/eee09f5a9d5f227e0fe33d4fd159e1c422596cb3))
* **scanner-zap:** generate unique prefix from all inputs ([c5a663f](https://github.com/huntridge-labs/hardening-workflows/commit/c5a663f0283b4342f126c453af7f78cbce7adeac))
* **scanner-zap:** refactor matrix variable usage in workflow and parser ([fcb64d0](https://github.com/huntridge-labs/hardening-workflows/commit/fcb64d0469bb8441b37e2f2550c0364c6265c2e0))
* **scanner-zap:** rename output variable for post PR comment in ZAP workflow ([8748562](https://github.com/huntridge-labs/hardening-workflows/commit/874856229a7816c3593a9c5bbbc8060ef6163ac1))
* **scanner-zap:** update ZAP risk code handling to match severity levels ([681011b](https://github.com/huntridge-labs/hardening-workflows/commit/681011b88c189f26f1198708ae650bfb6176dca0))
* **scanner-zap:** update ZAP risk code mapping to reflect 1:1 severity levels ([1257c3a](https://github.com/huntridge-labs/hardening-workflows/commit/1257c3aa84d53c5b0f36987405246cfc1519239b))
* **test-zap:** add security-events permission for enhanced security handling ([a79b7c0](https://github.com/huntridge-labs/hardening-workflows/commit/a79b7c0178758c0e57765988ecb8a70d08b80723))
* **zap-config.example:** update fail_on_severity settings to 'none' for all scans ([683fd64](https://github.com/huntridge-labs/hardening-workflows/commit/683fd64d30916e0a15371e3cb1c33b08ef799a54))
* **zap-config:** add inputs to defaults w/override options ([7f4023e](https://github.com/huntridge-labs/hardening-workflows/commit/7f4023e430e727344b0e4bffed9382d2f3d68056))
* **zap:** add example ZAP DAST scan workflow for Podinfo application ([8bb9b3f](https://github.com/huntridge-labs/hardening-workflows/commit/8bb9b3f2f58be2a23476f28fe8b8dee83c8c3394))


### Documentation

* add security policy and reporting guidelines ([07ad4c8](https://github.com/huntridge-labs/hardening-workflows/commit/07ad4c8f82aa2bdba8b86ca4b96992e19832143f))
* update license information from MIT to AGPL v3 ([68a6dcc](https://github.com/huntridge-labs/hardening-workflows/commit/68a6dcc93460e51dd478893a4597e4fd610b7fd4))

## [2.10.0](https://github.com/huntridge-labs/hardening-workflows/compare/2.9.1...2.10.0) (2026-01-05)

### Features

* add digest to container scan summary ([53af4f6](https://github.com/huntridge-labs/hardening-workflows/commit/53af4f65fde61951d6744a7d25139630b5e6de94))
* **container-scanners:** add composite action and remote registry scanning ([ab1c321](https://github.com/huntridge-labs/hardening-workflows/commit/ab1c32103d93365b6c28826eb6e7b0e20e568c47))
* **container-scanners:** add config-driven matrix scanning ([127ae09](https://github.com/huntridge-labs/hardening-workflows/commit/127ae095908ae3c40c1c7415543957c8e3eb206b))
* **container-scanners:** add remote registry authentication support ([bcb47ca](https://github.com/huntridge-labs/hardening-workflows/commit/bcb47cac8b6e636aa7d2d450d72fc692efd197a6))

### Security Tools

* **deps:** bump bridgecrewio/checkov-action ([81320bb](https://github.com/huntridge-labs/hardening-workflows/commit/81320bb2d81ca490db2cd9586e293a0832ae01d9))

### Dependencies

* **deps:** bump @commitlint/cli from 20.2.0 to 20.3.0 ([bc34f9d](https://github.com/huntridge-labs/hardening-workflows/commit/bc34f9dcfc886abb4688dbd71aa611c8d7e2f1dc))

### Maintenance

* **container-config-schema:** consolidate registry configuration ([49d4641](https://github.com/huntridge-labs/hardening-workflows/commit/49d46412f61afc9b524c85e7ea86e86a23d2a194))
* **container-scan-from-config:** enhance registry authentication and environment variable support ([4ea3b81](https://github.com/huntridge-labs/hardening-workflows/commit/4ea3b81a3bee43f5429f8b88c22e65f0b6e2a5dc))


### Documentation

* restructure and consolidate to improve readability and flow ([342bbd0](https://github.com/huntridge-labs/hardening-workflows/commit/342bbd087d5e482382dfcc26e1fc8d33c9adbe7a))

### Code Refactoring

* **container-scan:** extract inline scripts to external files ([85a3191](https://github.com/huntridge-labs/hardening-workflows/commit/85a3191109f2e13139e0a54b987565b9f304df4c))

## [2.9.1](https://github.com/huntridge-labs/hardening-workflows/compare/2.9.0...2.9.1) (2025-12-29)

### Security Tools

* **deps:** bump anchore/sbom-action from 0.20.11 to 0.21.0 ([68fc8b8](https://github.com/huntridge-labs/hardening-workflows/commit/68fc8b8f511ed928d9e5484dfcb22db726214ced))
* **deps:** bump bridgecrewio/checkov-action ([625294b](https://github.com/huntridge-labs/hardening-workflows/commit/625294b33eeba2eef6b43a43b4dbdb9c6e4eab60))

### Dependencies

* **deps:** bump @release-it/conventional-changelog ([2915436](https://github.com/huntridge-labs/hardening-workflows/commit/2915436dacbc1b6ba49234637c7a1a5ee92b6ecd))
* **deps:** bump release-it from 19.1.0 to 19.2.2 ([22a15dd](https://github.com/huntridge-labs/hardening-workflows/commit/22a15dde11cb78a94f82fd56547d6ec1258a3d96))


## [2.9.0](///compare/2.8.1...2.9.0) (2025-12-21)

### Features

* **gitleaks:** add organization license and configuration support b17e00a

### Bug Fixes

* **reusable-security-hardening:** reusable workflow not passing GITLEAKS_LICENSE from org secrets a60715b


### Documentation

* update reusable workflow example and README w/detailed scanner options and descriptions 5e65c1d

## [2.8.1](///compare/2.8.0...2.8.1) (2025-12-16)

### Security Tools

* **deps:** bump anchore/sbom-action from 0.20.10 to 0.20.11 f302689

### Dependencies

* **deps:** bump @commitlint/cli from 20.1.0 to 20.2.0 ([#84](undefined/undefined/undefined/issues/84)) 5cc7c24
* **deps:** bump @commitlint/config-conventional from 20.0.0 to 20.2.0 ([#83](undefined/undefined/undefined/issues/83)) 5f1dd6d
* **deps:** bump @release-it/conventional-changelog 81d0e26
* **deps:** bump release-it from 19.0.6 to 19.1.0 ec15994
* **deps:** bump the github-actions-major group with 2 updates cd16739


## [2.8.0](https://github.com/huntridge-labs/hardening-workflows/compare/2.7.0...2.8.0) (2025-12-14)

### Features

* **container-scan:** add detailed scanner breakdown with deduplication ([a0f49e6](https://github.com/huntridge-labs/hardening-workflows/commit/a0f49e6fb6590b20253ff698b511b58fe51e6a1e))
* **scanners:** improve vuln summary details ([5a64ad3](https://github.com/huntridge-labs/hardening-workflows/commit/5a64ad3298e35d1a6cc9cb24e43688b30eb1da31))

### Bug Fixes

* **comment pr:** update max character count ([f2fdeae](https://github.com/huntridge-labs/hardening-workflows/commit/f2fdeaecc4b58b70e099f7d4ff7b7ed626321dee))
* **container-scan:** prevent early exit on Grype severity threshold ([0ab3713](https://github.com/huntridge-labs/hardening-workflows/commit/0ab3713c277393d0c03030b547023351fe2a1afc))
* **grype:** use output-file parameter instead of action outputs ([5729d2a](https://github.com/huntridge-labs/hardening-workflows/commit/5729d2aebf14ad1328251758060c70279e8b7901))

### Maintenance

* **checkov:** remove detailed check summaries for grouped by rule and passed checks ([cbe9749](https://github.com/huntridge-labs/hardening-workflows/commit/cbe9749f94680fc77a7803ee92beba204ca386c8))
* **infrastructure-scan:** default trivy findings details section to be closed ([ad4575f](https://github.com/huntridge-labs/hardening-workflows/commit/ad4575fa21c41c3883cd1747d08f362f53749241))
* **scanner-trivy-iac:** add vuln links ([397f66e](https://github.com/huntridge-labs/hardening-workflows/commit/397f66effc4dfc994f636469eb175514d5413731))
* **test-docker:** bump express ([#79](https://github.com/huntridge-labs/hardening-workflows/issues/79)) ([e7d8af8](https://github.com/huntridge-labs/hardening-workflows/commit/e7d8af8e504e69cf04cdfeb4534388e1bea40a35))


### Code Refactoring

* **scanners:** limit vulnerability table output to 50 rows ([6d0a31e](https://github.com/huntridge-labs/hardening-workflows/commit/6d0a31ef0ab98a13156a4f687b755e19f050aa51))

## [2.7.0](https://github.com/huntridge-labs/hardening-workflows/compare/2.6.0...2.7.0) (2025-12-07)

### Features

* add allow_failure and fail_on_severity options ([e09c8fa](https://github.com/huntridge-labs/hardening-workflows/commit/e09c8fa56400bceb8730684ab426276d7ada0c89))
* support GHE servers ([4d66f7c](https://github.com/huntridge-labs/hardening-workflows/commit/4d66f7c77d6effb3618d1b8dc31ca1697a687f9d))

### Bug Fixes

* add sarif extra dependency for Bandit SARIF output support ([d19e004](https://github.com/huntridge-labs/hardening-workflows/commit/d19e00445f587409f1c99d13f567eecd93ea83cb))
* correct Bandit critical threshold behavior - Bandit has no critical level ([b0ac80f](https://github.com/huntridge-labs/hardening-workflows/commit/b0ac80f1ceab25c902beba691508574eebca6690))


### Documentation

* add allow_failure and severity_threshold documentation ([6de36d3](https://github.com/huntridge-labs/hardening-workflows/commit/6de36d350fe57d2de99a905bef7f02d6c87b7a13))

## [2.6.0](https://github.com/huntridge-labs/hardening-workflows/compare/2.5.8...2.6.0) (2025-12-02)

### Features

* **container-scan:** add unique CVE column to summary totals ([ec99c3f](https://github.com/huntridge-labs/hardening-workflows/commit/ec99c3fe209e2fff24f4fe4122c933dd4a1c5a9d))
* **container-scan:** summary PR comment separated by container name ([9c64431](https://github.com/huntridge-labs/hardening-workflows/commit/9c644314e84eed6eae227667ab24da8986f04f77)), closes [#78](https://github.com/huntridge-labs/hardening-workflows/issues/78)

### Bug Fixes

* **container-scan-summary:** incorrect trivy vuln counts ([9cf052a](https://github.com/huntridge-labs/hardening-workflows/commit/9cf052aebf0ed27e40631d975aac97787d3794d7)), closes [#74](https://github.com/huntridge-labs/hardening-workflows/issues/74)
* **pr-verification:** container-scan.yml changes not triggering workflows ([bb47c3d](https://github.com/huntridge-labs/hardening-workflows/commit/bb47c3d539bb9b340f3a00eefcd42283950fbc2f)), closes [#77](https://github.com/huntridge-labs/hardening-workflows/issues/77)
* **trivy:** vuln table not displaying ([f159e2c](https://github.com/huntridge-labs/hardening-workflows/commit/f159e2cd9400b42539678d5daf6575da60c8f95d)), closes [#75](https://github.com/huntridge-labs/hardening-workflows/issues/75)

### Security Tools

* **deps:** bump bridgecrewio/checkov-action ([b6fbc9b](https://github.com/huntridge-labs/hardening-workflows/commit/b6fbc9bca277b6d1518e75cf9264d528c7a7e213))

### Dependencies

* **deps:** bump actions/checkout in the github-actions-major group ([2d6bcfd](https://github.com/huntridge-labs/hardening-workflows/commit/2d6bcfd5b4d1742d899cabd9d13863635b636dd7))

### Maintenance

* **.release-it.json:** update to improve changelog handling ([bda1287](https://github.com/huntridge-labs/hardening-workflows/commit/bda1287fd156bb33555136829e31f01b381b99c9))
* **container-scan:** remove docker emoji from summary ([0934258](https://github.com/huntridge-labs/hardening-workflows/commit/0934258b4207118819ef384d09944c8dcccdb4e1))
* **container-scan:** skip sbom files found in container_dir ([20ea5bf](https://github.com/huntridge-labs/hardening-workflows/commit/20ea5bfe3313d719600022e73dcef5b02af6f75d))
* **container-scan:** vulnerability summary in job summary and reports ([8c76557](https://github.com/huntridge-labs/hardening-workflows/commit/8c7655746a3840c6d936b6d64c89862c82bb2ebe))
* **pr-verification:** add contianer-scan to any_scanner ([9d4d308](https://github.com/huntridge-labs/hardening-workflows/commit/9d4d3080e3023df481e0419825ae2563929597bb))
* **reusable-security-hardening.yml:** temporarily set container-scan.yml ref to feat branch ([134b90e](https://github.com/huntridge-labs/hardening-workflows/commit/134b90eb150625f77554cc286da1a1359637b01c))


## [2.5.8](https://github.com/huntridge-labs/hardening-workflows/compare/2.5.6...2.5.8) (2025-11-18)

### Security Tools

* **deps:** bump anchore/sbom-action from 0.20.9 to 0.20.10 ([fccfc4e](https://github.com/huntridge-labs/hardening-workflows/commit/fccfc4efe2d1b464d3e3ef7947c583ce9a66aff6))
* **deps:** bump bridgecrewio/checkov-action ([1afe4f4](https://github.com/huntridge-labs/hardening-workflows/commit/1afe4f473295f507d666137fbc55d4c8820e7f53))

### Dependencies

* **deps:** bump @release-it/conventional-changelog ([0bd7763](https://github.com/huntridge-labs/hardening-workflows/commit/0bd77633003653133dbf0d49e848458363fb99d4))
* **deps:** bump js-yaml from 4.1.0 to 4.1.1 ([30761d1](https://github.com/huntridge-labs/hardening-workflows/commit/30761d1aa308d3e2db8d25001652d381639531f2))

### Maintenance

* **.release-it.json:** regex for all refs in QUICK-START.md and README.md ([260df17](https://github.com/huntridge-labs/hardening-workflows/commit/260df173fe933c3ac68d37ce2f297371ae7159a0))
* **release-it-process-changelog.js:** add debug logging ([f8ba371](https://github.com/huntridge-labs/hardening-workflows/commit/f8ba3717593edefc81d825df515a80388572b731))
* **release:** v2.5.7 ([b2856bb](https://github.com/huntridge-labs/hardening-workflows/commit/b2856bb5a9c57b3325b52ec8b59b8b4cb9067068))


### Continuous Integration

* **dependabot:** consolidate minor and patch updates for GitHub Actions and Docker ([aea0ac1](https://github.com/huntridge-labs/hardening-workflows/commit/aea0ac1a8e34d110b10dc099ddf0983854d5ddb9))

## [2.5.7](///compare/2.5.6...2.5.7) (2025-11-18)

## [2.5.6](https://github.com/huntridge-labs/hardening-workflows/compare/2.5.5...2.5.6) (2025-11-11)

### Security Tools

* **deps:** bump bridgecrewio/checkov-action ([a3b586e](https://github.com/huntridge-labs/hardening-workflows/commit/a3b586e9c078f826dd26265fe190282dd042793d))

### Dependencies

* **deps:** bump release-it from 19.0.5 to 19.0.6 ([c1cc96c](https://github.com/huntridge-labs/hardening-workflows/commit/c1cc96cb24f75e920a61c00ef16499a4f70198cc))

### Maintenance

* **.release-it.json:** restructure to use preset.name as before ([980ba98](https://github.com/huntridge-labs/hardening-workflows/commit/980ba98f7fab33d58260b2fb4fa22537451576f4))
* **.release-it.json:** update to improve changelog handling ([3933e45](https://github.com/huntridge-labs/hardening-workflows/commit/3933e45fea61333682a6c8cd775233f385047384))
* **package-lock.json:** regenerate for npm consistency ([ff8c21c](https://github.com/huntridge-labs/hardening-workflows/commit/ff8c21ce4ffd399f529ded0a9c7638916f55eb44))
* **package-lock.json:** remove unused conventional-commits-parser dependency ([2189d8e](https://github.com/huntridge-labs/hardening-workflows/commit/2189d8e9130a2371cf55f016b563f8ec93095e18))


### Documentation

* add Code of Conduct to promote a respectful community ([5469bef](https://github.com/huntridge-labs/hardening-workflows/commit/5469bef1b457ae1280671f91f264c82fa3f0e1a3))

## [2.5.5](https://github.com/huntridge-labs/hardening-workflows/compare/2.5.4...2.5.5) (2025-11-04)

### Security Tools

* **deps:** bump bridgecrewio/checkov-action ([d8dc4a6](https://github.com/huntridge-labs/hardening-workflows/commit/d8dc4a630eacfef7548fbc85cf4ee151d4e106b6))

### Dependencies

* **deps:** bump @octokit/plugin-paginate-rest in the npm-major group ([3463a53](https://github.com/huntridge-labs/hardening-workflows/commit/3463a53f6a8d684eebc1b691880a33701944c14d))


### Documentation

* add templates for bug reports, feature requests, and PRs ([270ae1d](https://github.com/huntridge-labs/hardening-workflows/commit/270ae1d87846aa00514f68fd58b82debdc315aa1))

## [2.5.4](https://github.com/huntridge-labs/hardening-workflows/compare/2.5.3...2.5.4) (2025-10-29)


## [2.5.3](https://github.com/huntridge-labs/hardening-workflows/compare/2.5.2...2.5.3) (2025-10-29)

### Bug Fixes

* **pr-reusable-security-hardening:** add 'actions: read' permission to linting job ([8da25b6](https://github.com/huntridge-labs/hardening-workflows/commit/8da25b670db424adecd5e6ab926e6b728e393d0a))
* update condition for validating workflow sync to include any scanner changes ([da852cc](https://github.com/huntridge-labs/hardening-workflows/commit/da852cc0226d4eeee19b1d4c3fb36fdab64447f2))

### Security Tools

* **deps)(deps:** bump anchore/sbom-action from 0.20.8 to 0.20.9 ([8cdb71d](https://github.com/huntridge-labs/hardening-workflows/commit/8cdb71d75d1abb33c7f6cb7472e11b1588a3caf6))
* **deps)(deps:** bump bridgecrewio/checkov-action ([c6f125b](https://github.com/huntridge-labs/hardening-workflows/commit/c6f125b42aa5283c13575a8bf538c31d0c00aa54))

### Dependencies

* **deps)(deps:** bump the github-actions-major group with 3 updates ([168567e](https://github.com/huntridge-labs/hardening-workflows/commit/168567efe52b237b6ddc7d95a7662bff097d68ab))
* **deps:** bump @octokit/plugin-paginate-rest from 13.2.0 to 13.2.1 ([c03a077](https://github.com/huntridge-labs/hardening-workflows/commit/c03a0770770032a7327c4afe85cad9ff60aa4163))


### Documentation

* **CONTRIBUTING:** add instructions for updating release-it-process-changelog ([ae51bff](https://github.com/huntridge-labs/hardening-workflows/commit/ae51bfff09aa30444fe801de7416759042d4452a))

### Continuous Integration

* **changelog:** categorize security tool updates in release changelog ([07eeeee](https://github.com/huntridge-labs/hardening-workflows/commit/07eeeeea3829a6403c6ee3f420b5779f8351fe87))
* **dependabot:** fix double scoped commit ([c3217a0](https://github.com/huntridge-labs/hardening-workflows/commit/c3217a058c543c836f17794d24c345b514135e68))
* **pr-verification.yml:** handle skipped tests in PR verification workflow ([6494b7a](https://github.com/huntridge-labs/hardening-workflows/commit/6494b7a9cf49b0503aeb13efa0142d02e366d8c7))

## [2.5.2](https://github.com/huntridge-labs/hardening-workflows/compare/2.5.1...2.5.2) (2025-10-24)

### Bug Fixes

* **reusable-security-hardening:** add 'actions: read' permissions to ([d030310](https://github.com/huntridge-labs/hardening-workflows/commit/d030310b6b2423b31ca4ce17305b7c0d0e1ffff3))

## [2.5.1](https://github.com/huntridge-labs/hardening-workflows/compare/2.5.0...2.5.1) (2025-10-24)

### Bug Fixes

* **linting.yml:** add permissions to read contents and actions in linting workflow ([4397e26](https://github.com/huntridge-labs/hardening-workflows/commit/4397e26e99f32985de45bd193a77f507916494fa))

## [2.5.0](https://github.com/huntridge-labs/hardening-workflows/compare/2.4.0...2.5.0) (2025-10-24)

### Features

* add ClamAV malware into PR verification workflow ([56ef41b](https://github.com/huntridge-labs/hardening-workflows/commit/56ef41b76988800fb96092795507661228744b41))
* **clamav:** add ClamAV malware scanner with archive extraction ([4384ed1](https://github.com/huntridge-labs/hardening-workflows/commit/4384ed1d664873bef03c4a55930bbd0aa9904f55))
* **workflows:** add composite action for unique artifact naming ([ed34421](https://github.com/huntridge-labs/hardening-workflows/commit/ed34421f19a53b3d598e68b6f8b5c32e08890a22))

### Bug Fixes

* **release-it:** reusable workflow versions not updating ([cbad3e3](https://github.com/huntridge-labs/hardening-workflows/commit/cbad3e35b84ee44e3be90266f5318ce1875fcf20))
* **reusable-security-hardening.yml:** scanners: all not running all 13 scanners ([92b1273](https://github.com/huntridge-labs/hardening-workflows/commit/92b1273170b780790134aec4b50447bdcfaaf63a))

### Documentation

* update CONTRIBUTING.md to clarify workflow integration for new scanners ([76ab04f](https://github.com/huntridge-labs/hardening-workflows/commit/76ab04fc1311783f6eb871b3a2c56d4cf578bb75))

### Code Refactoring

* **pr-verification:** remove redundant code quality checks ([b02b281](https://github.com/huntridge-labs/hardening-workflows/commit/b02b28195b622f5c541f4d58351cce0d1a453c4f))

### Performance Improvements

* **clamav:** replace rglob with iterdir for faster directory scanning ([955b1a7](https://github.com/huntridge-labs/hardening-workflows/commit/955b1a7a023b992d0a3d6d202ee064c442734e62))

### Tests

* add comprehensive test suites for extract-archives.py and parse-clamav-report.py ([449beb1](https://github.com/huntridge-labs/hardening-workflows/commit/449beb170f8dfbc50cd6b564d9985cf21867a995))

### Continuous Integration

* **release-it:** update reusable-security-hardening.yml pattern to match any ref ([b8c153a](https://github.com/huntridge-labs/hardening-workflows/commit/b8c153a1ee07f902c15c0c3470400bc978b7e0a8))

## [2.4.0](https://github.com/huntridge-labs/hardening-workflows/compare/2.3.1...2.4.0) (2025-10-21)

### Features

* **ci:** add conditional scanner testing based on file changes ([f472660](https://github.com/huntridge-labs/hardening-workflows/commit/f47266093d4fc77b5f837095fb415d0d86ed35fc))
* **ci:** add PR testing workflow with relative paths for scanner validation ([53b7dff](https://github.com/huntridge-labs/hardening-workflows/commit/53b7dffa69d380ab221101b8712fa6ea4471884e))
* **ci:** implement workflow synchronization validation script ([bdae6da](https://github.com/huntridge-labs/hardening-workflows/commit/bdae6da6db5ef3429f3889ff9a16e3a1f165cfe7))

### Bug Fixes

* **ci:** enable release preview and PR verification workflows for forked PRs ([ce559d9](https://github.com/huntridge-labs/hardening-workflows/commit/ce559d9aed9cc98659ffb50f7d1b0aeee8faf743))
* **ci:** update checkout ref to use pull request head ref ([9d20643](https://github.com/huntridge-labs/hardening-workflows/commit/9d206434010e84ea402b952a5e8b06649562a63b))
* update SBOM summary to reflect dynamic Syft version ([633851e](https://github.com/huntridge-labs/hardening-workflows/commit/633851e34da4e26453c6fd10d3569487261e2a5d))

### Documentation

* **LICENSE.md:** include text of GNU Affero GPL ([4e4fe09](https://github.com/huntridge-labs/hardening-workflows/commit/4e4fe09732b9e435157a1b99af22810d92aca397)), closes [#42](https://github.com/huntridge-labs/hardening-workflows/issues/42)
* **LICENSE.md:** remove duplicated verbiage ([791bdef](https://github.com/huntridge-labs/hardening-workflows/commit/791bdefbceef907c70173004a88d46782f33ebd7))

## [2.3.1](https://github.com/huntridge-labs/hardening-workflows/compare/2.3.0...2.3.1) (2025-10-18)

## [2.3.0](https://github.com/huntridge-labs/hardening-workflows/compare/2.2.0...2.3.0) (2025-10-18)

### Features

* Add SBOM generation to hardening pipeline ([e5a0344](https://github.com/huntridge-labs/hardening-workflows/commit/e5a03444c3b76dbf797f131d0ef0dc0bc34f54cd))

### Bug Fixes

* Update conditions for release and dry-run jobs in workflow ([afa1462](https://github.com/huntridge-labs/hardening-workflows/commit/afa1462e7b71a0b6435fddfbc0d76c6604e22186))

## [2.2.0](https://github.com/huntridge-labs/hardening-workflows/compare/2.1.1...2.2.0) (2025-10-17)

### Features

* **scanners:** extract individual scanner workflows for modular usage ([b86f74f](https://github.com/huntridge-labs/hardening-workflows/commit/b86f74fca6006814a52d8703c165326d6d0509fa))

### Bug Fixes

* **release-it:** reusable workflow versions not updating ([3512942](https://github.com/huntridge-labs/hardening-workflows/commit/351294269239c7f8844c3fdf8a2df1e0f63a8be0))
* **release:** update GITHUB_TOKEN usage to support RELEASE_BOT_TOKEN for automated releases ([eb6aeda](https://github.com/huntridge-labs/hardening-workflows/commit/eb6aeda2427e20e44e6e2bc78661fe0c7e6568b8))

### Code Refactoring

* deprecate legacy workflows ([f813c55](https://github.com/huntridge-labs/hardening-workflows/commit/f813c5506cfefbc2278f7a37a41b647a7b08be79))
* update Trivy and Checkov actions to use pinned versions ([15a0e6e](https://github.com/huntridge-labs/hardening-workflows/commit/15a0e6efbf9cc180f2c3f213f42a92204e880617))

### Continuous Integration

* **deps:** organize Dependabot PRs by level ([09e1ff0](https://github.com/huntridge-labs/hardening-workflows/commit/09e1ff0d9764d769198bed0fd3820490dc0ab37e))

## [2.1.1](https://github.com/huntridge-labs/hardening-workflows/compare/2.1.0...2.1.1) (2025-10-16)

### Bug Fixes

* use absolute workflow paths in reusable workflow ([4a7b57e](https://github.com/huntridge-labs/hardening-workflows/commit/4a7b57eb48a6b431c1f4b4b40a901bf47a072dd9)), closes [#34](https://github.com/huntridge-labs/hardening-workflows/issues/34)

## [2.1.0](https://github.com/huntridge-labs/hardening-workflows/compare/2.0.0...2.1.0) (2025-10-12)

### Features

* implement automated release system with preview functionality ([cb64ef5](https://github.com/huntridge-labs/hardening-workflows/commit/cb64ef57a9ae9686c99eac4c1a059a3e7032ff30))

### Bug Fixes

* disable Husky during release and dry run jobs in release.yml ([641ff11](https://github.com/huntridge-labs/hardening-workflows/commit/641ff119e5288ff3196afb19092a56263e906376))
* **pre-commit:** ignore tests and apply fixes ([f9c9369](https://github.com/huntridge-labs/hardening-workflows/commit/f9c9369cad6db460549d9e2e2dd2f02e8cbe4db3))
* update condition for release job to include push events in release.yml ([f267ae4](https://github.com/huntridge-labs/hardening-workflows/commit/f267ae49fffc017439524f728199760bab2c8fa2))
* update conditions for workflow dispatch and dry run jobs in release.yml ([8a831a5](https://github.com/huntridge-labs/hardening-workflows/commit/8a831a5da8df73def731185c10d7d0fdfb04bd90))
