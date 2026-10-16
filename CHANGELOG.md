# Changelog

All notable public changes to this project are documented here.

## Unreleased

No unreleased changes.

## [1.0.0] - 2026-10-16

### Added

- public, site-neutral repository structure;
- reusable geometry, calibration, trajectory and control modules;
- public `spherov2` adapter and Vicon DataStream adapter;
- staged one-robot, multi-robot, Vicon-only and calibration examples;
- sanitized single- and three-chariot reference controllers;
- simulator and software-only dry-run workflow;
- TOML configuration with local/private values kept outside tracked source;
- unit tests, coverage checks and release checks;
- MkDocs documentation site and GitHub Pages deployment;
- issue templates, pull-request template, contribution, support and security guidance;
- CODEOWNERS and maintainer workflow documentation;
- OpenSSF Scorecard and scheduled dependency-security auditing;
- release build-provenance attestations and SHA-256 checksums.

### Changed

- refined the public controller architecture around Vicon-referenced displacement calibration;
- documented why fixed P/PD/PID gains are not assumed to transfer reliably between loaded chariots;
- added a stable aggregate `Required CI` gate;
- expanded CI to Linux and Windows on Python 3.11, 3.12 and 3.13;
- added Ruff formatting, Ruff linting, strict mypy, pytest coverage and package build/install validation;
- grouped Dependabot maintenance updates;
- refreshed pre-commit quality checks;
- pinned GitHub Actions to immutable commit SHAs;
- scoped write-capable workflow tokens to the jobs that require them.

### Security

- added Gitleaks history scanning;
- added a project-specific privacy scan for private network/device/path identifiers;
- added CodeQL static analysis;
- added pull-request dependency review with a `pip-audit` fallback;
- added weekly dependency auditing across public optional dependency groups;
- expanded private vulnerability-reporting guidance;
- added signed GitHub provenance attestations for tagged release artifacts.

### Fixed

- corrected CI import-order, formatting and strict-typing failures found during public hardening;
- corrected GitHub Pages deployment permissions and validated deployment;
- hardened the dependency-review workflow so repository-side graph availability does not remove Python vulnerability auditing.
