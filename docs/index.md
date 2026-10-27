# Sphero + Vicon Swarm Control

This site documents a public toolkit for external-motion-capture control of Sphero chariots.

!!! tip "Want to reproduce the laboratory setup?"
    Start with the **[step-by-step Vicon setup and reproduction workflow](vicon-setup.md)**. It covers camera checks, calibration, origin/floor-plane verification, rigid-body creation, Vicon object naming, software mapping, pose-stream validation and heading calibration before any swarm motion.

    If you already know the system and want a bench-side prompt, use the **[Vicon operator quick checklist](vicon-operator-checklist.md)**.

## Recommended path

1. [Getting started](getting-started.md) — install and verify the software-only path.
2. [Vicon setup and reproduction workflow](vicon-setup.md) — prepare Tracker and the motion-capture volume.
3. [Vicon operator quick checklist](vicon-operator-checklist.md) — practical workstation checklist.
4. [Configuration](configuration.md) — map local Vicon objects and Sphero devices.
5. [Hardware setup](hardware-setup.md) — verify robots and physical workspace.
6. Run the Vicon-only pose monitor.
7. Perform per-robot heading calibration.
8. Validate one robot.
9. Dry-run the three-robot controller.
10. Run the physical swarm conservatively.

The project keeps hardware-specific identifiers outside source control and includes automated privacy, quality and security checks suitable for a public GitHub repository.
