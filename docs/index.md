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
  <div class="sv-card"><div class="sv-card__title"><a href="end-to-end-tutorial/">End-to-end first run</a></div><p>Clean PC to first safe multi-robot run, with exact pass/fail gates and real Tracker screenshots.</p></div>
  <div class="sv-card"><div class="sv-card__title"><a href="vicon-setup/">Vicon procedure</a></div><p>Deep camera health, masking, calibration, origin, rigid-object and DataStream guidance.</p></div>
  <div class="sv-card"><div class="sv-card__title"><a href="vicon-tracker-ui-guide/">Tracker screenshot atlas</a></div><p>Real Tracker 4.1 UI states mapped precisely to current Tracker 4.4 procedure wording.</p></div>
  <div class="sv-card"><div class="sv-card__title"><a href="vicon-datastream/">DataStream SDK</a></div><p>Connect Tracker to Python and verify subject/segment identity before motion.</p></div>
  <div class="sv-card"><div class="sv-card__title"><a href="vicon-operator-checklist/">Operator checklist</a></div><p>A concise bench-side runbook for calibration, object creation, DataStream verification and staged motion.</p></div>
  <div class="sv-card"><div class="sv-card__title"><a href="command-reference/">Command reference</a></div><p>Know which commands are read-only, zero-speed, short-motion or closed-loop before you run them.</p></div>
</div>

## Real Tracker interface

[![Real Vicon Tracker 4.1 Wand Wave in progress](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/wand_in_progress.png)](vicon-tracker-ui-guide.md)

*Real Tracker 4.1 Wand Wave in progress: wand traces, per-camera counts and the Camera Calibration panel are all visible. The screenshot atlas explains every image state precisely.*

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
  <div class="sv-card"><div class="sv-card__title">1. Software first</div><p>Install, run diagnostics and validate the simulator without physical hardware.</p></div>
  <div class="sv-card"><div class="sv-card__title">2. Tracking before motion</div><p>Verify camera health, rigid-object identity, world axes and DataStream output.</p></div>
  <div class="sv-card"><div class="sv-card__title">3. Calibrate every robot</div><p>Measure Sphero command heading against observed Vicon displacement.</p></div>
  <div class="sv-card"><div class="sv-card__title">4. Scale deliberately</div><p>Single chariot → dry-run swarm → conservative physical multi-robot run.</p></div>
</div>

## Key design choice

The repository uses the **Vicon DataStream SDK** as the live pose interface. Tracker's UDP Object Stream is not required.

This keeps the lab procedure aligned with `src/sphero_vicon_swarm/tracking/vicon.py`, while configuration keeps site-specific addresses, device names and object identifiers outside source control.

## Documentation map

1. **[End-to-end first-run tutorial](end-to-end-tutorial.md)** — primary new-user path.
2. [Getting started](getting-started.md)
3. [Vicon setup and reproduction workflow](vicon-setup.md)
4. [Vicon Tracker visual guide](vicon-tracker-ui-guide.md)
5. [Vicon DataStream SDK setup](vicon-datastream.md)
6. [Vicon operator quick checklist](vicon-operator-checklist.md)
7. [Vicon procedure sources and version provenance](vicon-procedure-sources.md)
8. [Configuration](configuration.md)
9. [Hardware setup](hardware-setup.md)
10. [Control design](control-design.md)
11. [Validation](validation.md)
12. [Command reference](command-reference.md)
13. [Glossary](glossary.md)
