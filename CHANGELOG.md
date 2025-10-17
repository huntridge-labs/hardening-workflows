# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).



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
