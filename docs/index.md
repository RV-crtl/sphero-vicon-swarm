# Sphero + Vicon Swarm Control { .sv-page-title-hidden }

<div class="sv-hero">
  <div class="sv-hero__title">Sphero + Vicon Swarm Control</div>
  <p>A reproducible toolkit for Vicon-referenced control of Sphero BOLT/BOLT+ chariots, from camera calibration and DataStream verification through per-robot heading calibration and multi-robot control.</p>
  <div class="sv-badges">
    <span class="sv-badge">Vicon-referenced</span>
    <span class="sv-badge">Python 3.11+</span>
    <span class="sv-badge">Hardware + simulation</span>
    <span class="sv-badge">Public reproducible workflow</span>
  </div>
</div>

<div class="sv-grid">
  <div class="sv-card"><h3><a href="vicon-setup/">Reproduce the lab</a></h3><p>Camera health, masking, wand wave, origin, rigid objects and staged validation.</p></div>
  <div class="sv-card"><h3><a href="vicon-tracker-ui-guide/">Tracker visual guide</a></h3><p>Real Tracker UI screenshots with clear version labels and current operating guidance.</p></div>
  <div class="sv-card"><h3><a href="vicon-datastream/">DataStream SDK</a></h3><p>Connect Tracker to Python and verify subject/segment identity before motion.</p></div>
  <div class="sv-card"><h3><a href="vicon-operator-checklist/">Operator checklist</a></h3><p>A concise bench-side runbook for calibration, object creation, DataStream verification and staged motion.</p></div>
</div>

## Real Tracker interface

[![Real Vicon Tracker 4.1 Tracking interface](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/object_create.png)](https://dasc-lab.github.io/robot-framework/flylab/object.html)

*Real Vicon Tracker 4.1 UI from DASC Lab's public setup documentation. The site's written procedure is checked against Tracker 4.4, while this image provides a recognisable real interface rather than a mockup.*

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
