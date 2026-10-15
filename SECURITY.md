# Security policy

## Reporting

Please report suspected vulnerabilities privately through the repository's [GitHub Security Advisory form](https://github.com/RV-crtl/sphero-vicon-swarm/security/advisories/new).

Do **not** publish credentials, private network details, raw Bluetooth identifiers, personal filesystem paths or identifying hardware logs in a public issue.

When possible, include:

- the affected version or commit;
- a minimal reproduction;
- expected versus observed behaviour;
- whether physical robot motion is involved;
- a sanitized log or trace.

## Scope

Security-sensitive areas include configuration parsing, accidental secret/identifier disclosure, dependency vulnerabilities, unsafe failure modes that could leave a robot moving after an exception, and supply-chain integrity of CI/release automation.

The project intentionally stores local hardware configuration outside tracked source and uses multiple automated checks, including CodeQL, Gitleaks, a project-specific privacy scanner, dependency auditing and OpenSSF Scorecard analysis.

## Response expectations

Security reports should be handled privately until a fix or mitigation is available. Public disclosure should avoid operational secrets and should clearly distinguish software-only findings from issues demonstrated on physical hardware.
