# Changelog

## Unreleased

- Fix Ruff import-order failures in CI.
- Add a stable aggregate `Required CI` check for branch protection.
- Validate documentation on pull requests and deploy only from non-PR runs.
- Update GitHub Actions to current Node 24-compatible major versions.
- Add live workflow badges and canonical project URLs.
- Pin GitHub Actions to immutable commit SHAs for supply-chain integrity.
- Add CODEOWNERS and strengthen pull-request review guidance.
- Add package build/install validation to CI.
- Add scheduled dependency auditing and OpenSSF Scorecard analysis.
- Refresh pre-commit hooks and group Dependabot updates.
- Require Ruff formatting checks in CI.

All notable public changes are recorded here.

## [1.0.0] - 2026-09-09

### Added

- public, site-neutral repository structure;
- TOML configuration with local/private file separation;
- public `spherov2` adapter and Vicon DataStream adapter;
- reusable geometry, calibration, trajectory and control modules;
- staged hardware examples;
- sanitized single- and three-chariot reference controllers;
- simulator, unit tests and release checks;
- privacy scanning;
- CI, CodeQL, dependency review, Dependabot, docs deployment and release automation;
- issue templates, pull-request template, contribution, support and security guidance.
