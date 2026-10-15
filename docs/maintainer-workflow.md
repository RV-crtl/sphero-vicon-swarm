# Maintainer workflow

This page documents the recommended repository-maintenance workflow. It contains no deployment secrets or site-specific hardware values.

## Recommended repository settings

For a public repository, use the following GitHub settings:

- Issues: enabled.
- Discussions: enabled when community Q&A is wanted.
- Wiki: disabled; version-controlled MkDocs documentation is the source of truth.
- Squash merging: enabled.
- Rebase merging: enabled.
- Merge commits: disabled.
- Automatically delete head branches: enabled.
- Dependency graph, Dependabot alerts, secret scanning and push protection: enabled when available.
- GitHub Pages source: GitHub Actions.

For `main`, use a repository ruleset that blocks deletion and force-pushes, requires linear history, requires pull requests, requires conversation resolution, and requires the stable `Required CI`, CodeQL and Secret Scan checks. Solo maintainers can leave required external approvals at zero until another reviewer is available.

## Normal contribution flow

Create a topic branch, run the local checks, open a pull request, let automated checks complete, then squash-merge after review. `.github/CODEOWNERS` records default review ownership for sensitive paths.

Do not commit `config/robot_setup.toml`, `.env`, runtime logs, calibration state, learned state, videos, or private network/device identifiers.

## Local preflight

```bash
python -m pip install -e ".[dev,docs]"
pre-commit run --all-files
ruff format --check .
ruff check .
mypy src/sphero_vicon_swarm
pytest
python tools/privacy_scan.py .
mkdocs build --strict
python reference_controllers/three_chariot_square_swarm.py --dry-run --timeout 2 --no-digital-twin
python -m build
```

## Automated security

The repository uses several independent layers rather than relying on one scanner:

- CodeQL for static analysis;
- Gitleaks for Git-history secret detection;
- a project-specific privacy scanner for network/device/path identifiers;
- dependency review and `pip-audit`;
- Dependabot;
- OpenSSF Scorecard;
- immutable SHA pinning for GitHub Actions.

## Release flow

Run `python tools/release_check.py`, ensure the default branch is green, then create a semantic-version tag such as `v1.0.0`. The release workflow reruns validation, audits runtime dependencies, builds the Python distributions, installs the built wheel, creates SHA-256 checksums, and publishes the artifacts to a GitHub Release.
