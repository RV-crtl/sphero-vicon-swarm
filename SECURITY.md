# Security policy

## Reporting

Please use GitHub's **private security advisory** feature for suspected vulnerabilities. Do not publish secrets, private network details or identifying hardware logs in a public issue.

## Scope

Security-sensitive areas include configuration parsing, accidental secret/identifier disclosure, dependency vulnerabilities and unsafe failure modes that could leave a robot moving after an exception.

The project intentionally stores local hardware configuration outside tracked source and includes an automated privacy scan in CI.
