## Summary

Describe what changed and why. Keep the scope focused and link any related issue.

## Validation

- [ ] `ruff check .` passes
- [ ] `ruff format --check .` passes
- [ ] `mypy src/sphero_vicon_swarm` passes
- [ ] `pytest` passes
- [ ] `python tools/privacy_scan.py .` passes
- [ ] documentation was updated if behaviour or public interfaces changed
- [ ] software-only, bench and integrated-hardware validation are clearly distinguished

## Physical-motion impact

Describe any change to speed, heading, calibration, collision handling, boundary handling, stop behaviour or failure recovery.

If there is no physical-motion impact, write **None**.

## Compatibility

Note any effect on:

- Python versions;
- Sphero/BOLT firmware or BLE backends;
- Vicon DataStream SDK versions;
- configuration-file compatibility.

## Privacy and security check

Confirm that the change contains no:

- private IP addresses;
- raw Bluetooth identifiers;
- credentials or tokens;
- personal filesystem paths;
- identifying or unsanitized experiment logs.

For security-sensitive changes, explain the threat/failure mode being addressed.

## Checklist

- [ ] change is small enough to review confidently
- [ ] public API changes are documented
- [ ] new behaviour has tests where practical
- [ ] generated/runtime artifacts are not committed
- [ ] changelog entry added when user-visible behaviour changes
