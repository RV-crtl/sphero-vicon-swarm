# Maintainer workflow

This page documents the recommended repository-maintenance workflow. It contains no deployment secrets or site-specific hardware values.

## Before the first protected-branch ruleset

1. Enable GitHub Pages with **Settings → Pages → Source → GitHub Actions**.
2. Run the workflows once on `main` and confirm `CI / Required CI`, CodeQL, Secret Scan, and Docs are green.
3. Enable repository security features that are available for the repository.
4. Create a `main` branch ruleset only after the required status checks have appeared at least once.

## Normal contribution flow

Create a topic branch, run the local checks, open a pull request, let automated checks complete, then squash-merge after review. Do not commit `config/robot_setup.toml`, `.env`, runtime logs, calibration state, learned state, videos, or private network/device identifiers.

## Local preflight

```bash
python -m pip install -e ".[dev,docs]"
pre-commit run --all-files
pytest
python tools/privacy_scan.py .
mkdocs build --strict
python reference_controllers/three_chariot_square_swarm.py --dry-run --timeout 2 --no-digital-twin
```

## Release flow

Run `python tools/release_check.py`, ensure the default branch is green, then create a semantic-version tag such as `v1.0.0`. The release workflow builds the Python distributions, creates SHA-256 checksums, and publishes the artifacts to a GitHub Release.
