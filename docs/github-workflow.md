# GitHub workflow

The repository includes enough automation to support a normal public open-source workflow.

## Recommended repository settings

After creating the repository on GitHub:

1. Set the default branch to `main`.
2. Protect `main` and require the CI checks before merge.
3. Require at least one approving review for external pull requests if you expect collaborators.
4. Enable Dependabot alerts and security updates.
5. Enable private vulnerability reporting / security advisories.
6. Enable GitHub Pages with **GitHub Actions** as the source if you want the MkDocs site.
7. Enable secret scanning where available.
8. Prefer squash merge or rebase merge to keep history readable.

## Development loop

```text
issue -> branch -> implementation -> tests -> pull request -> CI -> review -> merge -> release
```

For physical-motion changes, include a short validation note distinguishing:

- software-only simulation;
- subsystem/bench testing;
- integrated physical testing.

## Releases

Use semantic version tags such as `v1.0.0`. The release workflow builds the Python distribution, runs the repository release checks and attaches the generated package files to the GitHub Release.

## Documentation

Changes under `docs/`, `README.md` or `mkdocs.yml` trigger a documentation build and Pages deployment.

## Dependencies

Dependabot checks Python and GitHub Actions dependencies monthly. Pull requests also run GitHub dependency review.
