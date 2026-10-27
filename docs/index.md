# Sphero + Vicon Swarm Control

This site documents a public toolkit for external-motion-capture control of Sphero chariots.

!!! tip "Want to reproduce the laboratory setup?"
    Start with the **[step-by-step Vicon setup and reproduction workflow](vicon-setup.md)**.

    Keep the **[Vicon Tracker UI guide](vicon-tracker-ui-guide.md)** open for the clear Tracker 4.x panel map, current Tracker 4.4 control paths, official Vicon visual references, and separately labeled historical lab captures. Use the **[operator quick checklist](vicon-operator-checklist.md)** once you know the system.

~~~mermaid
flowchart LR
    A["System / cameras"] --> B["Camera Calibration"]
    B --> C["Tracking / rigid objects"]
    C --> D["DataStream verification"]
    D --> E["Heading calibration"]
    E --> F["Single robot"]
    F --> G["Swarm"]
~~~

## Reproduction path

1. [Getting started](getting-started.md) — install and verify the software-only path.
2. [Vicon setup and reproduction workflow](vicon-setup.md) — camera system, calibration, origin, rigid bodies and validation.
3. [Vicon Tracker UI guide](vicon-tracker-ui-guide.md) — clear Tracker 4.x visual map, current manufacturer procedures, and official high-resolution references.
4. [Vicon DataStream SDK setup](vicon-datastream.md) — Python SDK installation and live connection.
5. [Vicon operator quick checklist](vicon-operator-checklist.md) — bench-side procedure.
6. [Vicon procedure sources and version provenance](vicon-procedure-sources.md) — exact source/version audit for the instructions and screenshots.
7. [Configuration](configuration.md) — map local Vicon objects and Sphero devices.
8. [Hardware setup](hardware-setup.md) — verify robots and physical workspace.
9. Run the Vicon-only pose monitor.
10. Perform per-robot heading calibration.
11. Validate one robot.
12. Dry-run the three-robot controller.
13. Run the physical swarm conservatively.

## Key design choice

The repository uses the **Vicon DataStream SDK** as the live pose interface. Tracker's UDP Object Stream is not required.

This keeps the lab procedure aligned with the code in `src/sphero_vicon_swarm/tracking/vicon.py` and avoids teaching an unnecessary UDP configuration step.

The project keeps hardware-specific identifiers outside source control and includes automated privacy, quality and security checks suitable for a public GitHub repository.
