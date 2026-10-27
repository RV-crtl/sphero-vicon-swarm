# Sphero + Vicon Swarm Control

<div class="sv-hero">
  <h1>Sphero + Vicon Swarm Control</h1>
  <p>A reproducible toolkit for Vicon-referenced control of Sphero BOLT/BOLT+ chariots, from camera calibration and DataStream verification through per-robot heading calibration and multi-robot control.</p>
  <div class="sv-badges">
    <span class="sv-badge">Vicon-referenced</span>
    <span class="sv-badge">Python 3.11+</span>
    <span class="sv-badge">Hardware + simulation</span>
    <span class="sv-badge">Public reproducible workflow</span>
  </div>
</div>

<div class="sv-grid">
  <div class="sv-card"><h3><a href="vicon-setup.md">Reproduce the lab</a></h3><p>Camera health, masking, wand wave, origin, rigid objects and staged validation.</p></div>
  <div class="sv-card"><h3><a href="vicon-tracker-ui-guide.md">Tracker visual guide</a></h3><p>Version-aware visual references plus crisp, scalable interface maps.</p></div>
  <div class="sv-card"><h3><a href="vicon-datastream.md">DataStream SDK</a></h3><p>Connect Tracker to Python and verify subject/segment identity before motion.</p></div>
  <div class="sv-card"><h3><a href="vicon-operator-checklist.md">Operator checklist</a></h3><p>Bench-side runbook with no blurry screenshots or fragile external image dependencies.</p></div>
</div>

<figure class="sv-figure sv-figure--wide">
  <img src="assets/site/tracker-overview.svg" alt="High-resolution Vicon Tracker 4.x interface map">
  <figcaption>Tracker 4.x system map. This vector illustration is deliberately local and resolution-independent; the visual guide also links to real Tracker screenshots for appearance/version comparison.</figcaption>
</figure>

## Reproduction path

```mermaid
flowchart LR
    A["Camera health"] --> B["Mask + calibrate"]
    B --> C["Set world origin"]
    C --> D["Create rigid objects"]
    D --> E["Verify DataStream"]
    E --> F["Heading calibration"]
    F --> G["Single robot"]
    G --> H["Three-robot swarm"]
```

<div class="sv-grid">
  <div class="sv-card"><h4>1. Software first</h4><p>Install, run diagnostics and validate the simulator without physical hardware.</p></div>
  <div class="sv-card"><h4>2. Tracking before motion</h4><p>Verify camera health, rigid-object identity, world axes and DataStream output.</p></div>
  <div class="sv-card"><h4>3. Calibrate every robot</h4><p>Measure Sphero command heading against observed Vicon displacement.</p></div>
  <div class="sv-card"><h4>4. Scale deliberately</h4><p>Single chariot → dry-run swarm → conservative physical multi-robot run.</p></div>
</div>

## Key design choice

The repository uses the **Vicon DataStream SDK** as the live pose interface. Tracker's UDP Object Stream is not required.

This keeps the lab procedure aligned with `src/sphero_vicon_swarm/tracking/vicon.py`, while configuration keeps site-specific addresses, device names and object identifiers outside source control.

## Documentation map

1. [Getting started](getting-started.md)
2. [Vicon setup and reproduction workflow](vicon-setup.md)
3. [Vicon Tracker visual guide](vicon-tracker-ui-guide.md)
4. [Vicon DataStream SDK setup](vicon-datastream.md)
5. [Vicon operator quick checklist](vicon-operator-checklist.md)
6. [Vicon procedure sources and version provenance](vicon-procedure-sources.md)
7. [Configuration](configuration.md)
8. [Hardware setup](hardware-setup.md)
9. [Control design](control-design.md)
10. [Validation](validation.md)
