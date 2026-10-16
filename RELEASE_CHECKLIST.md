# Release checklist

Use this checklist for every public version tag.

## Pre-release

- [ ] `python tools/release_check.py` passes.
- [ ] `ruff format --check .` and `ruff check .` pass.
- [ ] `mypy src/sphero_vicon_swarm` passes.
- [ ] `pytest` passes with the configured coverage threshold.
- [ ] `mkdocs build --strict` passes.
- [ ] `python tools/privacy_scan.py .` passes.
- [ ] dependency auditing reports no known unresolved vulnerabilities.
- [ ] no local `config/robot_setup.toml` is staged.
- [ ] no raw experimental logs, videos or private metadata are staged.
- [ ] controller changes have appropriate tests or clearly documented hardware validation.
- [ ] the version in `pyproject.toml` and `src/sphero_vicon_swarm/__init__.py` matches the tag.
- [ ] the changelog and release notes describe user-visible changes and limitations.
- [ ] the tag uses semantic versioning, for example `v1.0.0`.

## Release artifacts

A normal tagged release should contain:

- [ ] Python wheel;
- [ ] source distribution;
- [ ] `SHA256SUMS.txt`;
- [ ] generated GitHub release notes or a curated release note;
- [ ] GitHub build-provenance attestation.

## Post-release

- [ ] the GitHub Release is published rather than left as a draft.
- [ ] the documentation site is reachable.
- [ ] the release badge resolves to the new version.
- [ ] the release assets download successfully.
- [ ] the release tag points to the intended `main` commit.
- [ ] security/CI checks on the release commit are green.
