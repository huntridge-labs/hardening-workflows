# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).



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
