# Vicon procedure sources and version provenance

This page records where each part of the public Vicon reproduction procedure comes from.

The purpose is to make the documentation auditable and to avoid silently mixing Tracker versions.

| Topic | Procedure authority | Version | What the repository uses |
|---|---|---:|---|
| General lab start-up / practical object workflow | Supplied local Vicon checklist and training material | Lab material | Used only for practical workflow context; credentials, private addresses and site-specific network rules are not published |
| Current camera masking | Vicon Tracker documentation | Tracker 4.0 | **Camera Calibration → Masking → Mask All**, plus documented manual-mask controls |
| Wand calibration | Vicon Tracker User Guide | Tracker 4.4, 2025-09-17 Rev 1 | **Camera Calibration → Wand Wave → Wave All**, depth/height coverage, Wand Count, Auto Stop |
| Volume origin | Vicon Tracker User Guide | Tracker 4.4, 2025-09-17 Rev 1 | **Camera Calibration → Volume Setup → Start Set Origin → Set Origin**, X red / Y green / Z blue |
| Floor plane controls | Vicon Tracker User Guide | Tracker 4.4, 2025-09-17 Rev 1 | Separate **Set Floor Plane** workflow; manufacturer default Height offset 7 mm |
| System Health definitions | Vicon Tracker User Guide | Tracker 4.4, 2025-09-17 Rev 1 | Performance, Calibration Details, Centroid Connectivity, Image Error, temperature/accelerometer/healing sections |
| Rigid-object creation | Vicon Tracker User Guide | Tracker 4.4, 2025-09-17 Rev 1 | **View → Tracking**, Ctrl-click / Alt-drag, ≥4 trajectories, 5+ recommended, Object field → Create |
| Add / remove marker | Vicon Tracker documentation | Tracker 4.4 | Ctrl-select + **Add Marker**; **Remove Marker**; cannot reduce below four markers |
| DataStream software | Vicon DataStream SDK documentation | SDK 1.13 current release | `vicon_dssdk`; vendor SDK installed separately |
| Python DataStream connection example | Vicon DataStream Python Quick Start | SDK 1.10 documentation | Vicon example connects to `localhost:801`; repository uses the same `HOST:PORT` convention |
| Project pose adapter | This repository | current `main` | `src/sphero_vicon_swarm/tracking/vicon.py` |
| Vicon-only validation command | This repository | current `main` | `examples/03_vicon_pose_monitor.py` |
| Heading/world-frame calibration | This repository | current `main` | `examples/04_heading_calibration.py` |

## Visual-source provenance

### Primary visual guidance

The main documentation now uses **clear Tracker 4.x panel/navigation maps** plus direct links to current Vicon documentation. This avoids two problems with the supplied captures:

- the original files are low-resolution and difficult to read on GitHub Pages;
- the Tracker 3.9 layout is not a reliable guide to Tracker 4.4 button locations.

Official current references are preferred for UI appearance and control placement.

### Historical lab captures

The following supplied images remain in the repository for provenance only:

- `tracker4-actual-overview-annotated.jpg`
- `tracker4-actual-datastream-connections.jpg`
- `tracker39-actual-calibrate-tab.jpg`
- `tracker39-actual-object-workflow.jpg`

The Tracker 4.0 files preserve the real lab context after privacy redaction. The Tracker 3.9 files preserve older training context. None of these images is treated as pixel-identical evidence for Tracker 4.4.

## Manufacturer references

### Vicon Tracker

**Tracker 4.4 User Guide — 17 September 2025, Revision 1**

https://help.vicon.com/download/attachments/376309877/Vicon%20Tracker%20User%20Guide.pdf

Relevant sections:

- Perform a wand wave — pp. 130–132
- Set up the volume / set volume origin — pp. 133–139
- Volume Setup controls — around p. 147
- Understand System Health Report — pp. 177–187
- Setting up object tracking / Create objects — pp. 187–190

**Tracker 4.0 — Mask cameras**

https://help.vicon.com/space/Tracker40/14190245

**Tracker 4.4 — Add or remove a marker on an object**

https://help.vicon.com/space/Tracker44/376309055

### Vicon DataStream SDK

**Current DataStream SDK download / release information**

https://www.vicon.com/software/datastream-sdk/

**DataStream SDK 1.13 documentation**

https://help.vicon.com/space/DSSDK113

**Python Quick Start (older 1.10 page, used only for the documented Python connection/install example)**

https://help.vicon.com/space/DSSDK110/9240617

## Version rule used by this repository

When the screenshot version and current manufacturer procedure differ:

1. the screenshot is labeled with its actual version;
2. current manufacturer terminology is used for the written procedure;
3. the documentation does **not** imply that an old screenshot is pixel-identical to Tracker 4.4;
4. a user should follow the installed Tracker version's official help if a control has moved.
