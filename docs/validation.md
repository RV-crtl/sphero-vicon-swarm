# Validation

The repository separates validation into three levels.

## Software-only

- source compilation;
- unit tests for geometry, configuration and calibration;
- simulator smoke test;
- reference-controller dry-run;
- privacy scan.

## Bench / subsystem

- single Sphero connect/stop;
- multi-Sphero addressing;
- Vicon-only pose stream;
- Sphero/Vicon heading calibration.

## Integrated hardware

- low-speed single-chariot trajectory;
- emergency stop;
- boundary response;
- three-robot mapping verification;
- low-speed one-lap multi-robot run;
- log review after every first run on a changed setup.

Passing software-only checks is not evidence that a new physical setup is safe or correctly calibrated.
