# Sphero + Vicon Swarm Control

This site documents a public toolkit for external-motion-capture control of Sphero chariots.

!!! tip "Want to reproduce the laboratory setup?"
    Start with the **[step-by-step Vicon setup and reproduction workflow](vicon-setup.md)**.

    Keep the **[Vicon Tracker UI guide — actual screenshots](vicon-tracker-ui-guide.md)** open for click maps showing where the relevant controls are, and use the **[operator quick checklist](vicon-operator-checklist.md)** once you know the system.

![Tracker 4.x orientation map](assets/vicon/tracker4-overview.svg)

## Reproduction path

1. [Getting started](getting-started.md) — install and verify the software-only path.
2. [Vicon setup and reproduction workflow](vicon-setup.md) — camera system, calibration, origin, rigid bodies and validation.
3. [Vicon Tracker visual guide](vicon-tracker-ui-guide.md) — where to click in Tracker 4.x.
4. [Vicon DataStream SDK setup](vicon-datastream.md) — Python SDK installation and live connection.
5. [Vicon operator quick checklist](vicon-operator-checklist.md) — bench-side procedure.
6. [Configuration](configuration.md) — map local Vicon objects and Sphero devices.
7. [Hardware setup](hardware-setup.md) — verify robots and physical workspace.
8. Run the Vicon-only pose monitor.
9. Perform per-robot heading calibration.
10. Validate one robot.
11. Dry-run the three-robot controller.
12. Run the physical swarm conservatively.

## Key design choice

The repository uses the **Vicon DataStream SDK** as the live pose interface. Tracker's UDP Object Stream is not required.

This keeps the lab procedure aligned with the code in `src/sphero_vicon_swarm/tracking/vicon.py` and avoids teaching an unnecessary UDP configuration step.

The project keeps hardware-specific identifiers outside source control and includes automated privacy, quality and security checks suitable for a public GitHub repository.
