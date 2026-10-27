# Sphero + Vicon Swarm Control

[![CI](https://github.com/RV-crtl/sphero-vicon-swarm/actions/workflows/ci.yml/badge.svg)](https://github.com/RV-crtl/sphero-vicon-swarm/actions/workflows/ci.yml)
[![Docs](https://github.com/RV-crtl/sphero-vicon-swarm/actions/workflows/docs.yml/badge.svg)](https://github.com/RV-crtl/sphero-vicon-swarm/actions/workflows/docs.yml)
[![CodeQL](https://github.com/RV-crtl/sphero-vicon-swarm/actions/workflows/codeql.yml/badge.svg)](https://github.com/RV-crtl/sphero-vicon-swarm/actions/workflows/codeql.yml)
[![Secret Scan](https://github.com/RV-crtl/sphero-vicon-swarm/actions/workflows/secret-scan.yml/badge.svg)](https://github.com/RV-crtl/sphero-vicon-swarm/actions/workflows/secret-scan.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/RV-crtl/sphero-vicon-swarm/badge)](https://scorecard.dev/viewer/?uri=github.com/RV-crtl/sphero-vicon-swarm)
[![Release](https://img.shields.io/github/v/release/RV-crtl/sphero-vicon-swarm)](https://github.com/RV-crtl/sphero-vicon-swarm/releases/latest)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

A reproducible toolkit for controlling **Sphero BOLT/BOLT+ robots mounted in wheeled chariots** using **Vicon motion capture as external navigation truth**.

The repository is designed to be understandable by a new laboratory user, not only by the original developer. Site-specific identities, network values and workspace limits live in a private TOML file; hardware-free simulation and staged tests let you validate each layer before enabling closed-loop multi-robot motion.

> **Start here:** [End-to-end first-run tutorial](docs/end-to-end-tutorial.md) — clean PC → Tracker calibration → rigid bodies → DataStream → robot mapping → per-robot heading calibration → single robot → dry-run swarm → first conservative physical run.

> **Safety:** these scripts can command physical robots. Keep the motion volume clear, prove the Sphero/Vicon identity mapping before motion, keep Ctrl+C immediately available, and understand both the mission and startup-calibration command limits before a live run.

## Real Tracker workflow

The documentation uses **real Tracker 4.1 screenshots** for visual recognition and current Tracker 4.4 procedure wording.

[![Real Tracker 4.1 wand calibration in progress](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/wand_in_progress.png)](docs/vicon-tracker-ui-guide.md)

*Real Tracker 4.1 calibration in progress: per-camera Wand Count values and wand traces are visible. The [visual guide](docs/vicon-tracker-ui-guide.md) contains the full screenshot atlas with exact captions for each UI state.*

## Recommended validation path

~~~mermaid
flowchart LR
    A["Software self-test"] --> B["Camera health"]
    B --> C["Mask + wand calibration"]
    C --> D["World origin"]
    D --> E["Rigid-object identity"]
    E --> F["TOML mapping"]
    F --> G["Vicon-only pose"]
    G --> H["Sphero identity"]
    H --> I["Per-robot heading basis"]
    I --> J["Single chariot"]
    J --> K["Dry-run swarm"]
    K --> L["Live swarm"]
~~~

Each arrow is a gate. If one stage fails, fix it before moving forward.

## What is included

- reusable Python package under src/sphero_vicon_swarm;
- public TOML configuration model;
- staged examples that isolate BLE, Vicon and calibration;
- single-chariot Vicon-referenced closed-loop controller;
- feature-rich three-chariot square-trajectory reference controller;
- hardware-free simulator/dry-run path;
- physical-footprint collision/boundary handling;
- per-robot Sphero-heading ↔ Vicon-world calibration;
- Vicon continuity/occlusion handling;
- adaptive loaded-chariot drive/stiction handling;
- CSV telemetry and persistent learned state;
- real-time digital twin;
- unit tests, linting, typing, security/privacy checks;
- MkDocs Material documentation site;
- detailed Tracker screenshot atlas and operator checklist.

The project documents P/PD/PID experiments but does **not** claim one fixed gain set transfers universally across loaded chariots. The architecture prioritises measured Vicon state, per-robot calibration, bounded correction and explicit physical safeguards.

## Repository layout

~~~text
.
├── config/
│   └── robot_setup.example.toml
├── examples/
│   ├── 01_single_sphero_smoke_test.py
│   ├── 02_multi_sphero_smoke_test.py
│   ├── 03_vicon_pose_monitor.py
│   └── 04_heading_calibration.py
├── reference_controllers/
│   ├── single_chariot_vicon_circle.py
│   └── three_chariot_square_swarm.py
├── src/sphero_vicon_swarm/
├── tests/
├── tools/
├── docs/
├── .github/
├── mkdocs.yml
└── pyproject.toml
~~~

## Quick start — no hardware

~~~powershell
git clone https://github.com/RV-crtl/sphero-vicon-swarm.git
cd sphero-vicon-swarm
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,docs]"

python -m sphero_vicon_swarm doctor
python -m sphero_vicon_swarm validate-config --config config/robot_setup.example.toml
python -m sphero_vicon_swarm simulate --seconds 8
pytest
python tools/privacy_scan.py .
~~~

Advanced-controller dry run:

~~~powershell
python reference_controllers/three_chariot_square_swarm.py --dry-run --timeout 8 --no-digital-twin
~~~

Dry-run can fall back to the public example configuration if the private hardware TOML does not exist.

## One private configuration for the hardware workflow

~~~powershell
Copy-Item config/robot_setup.example.toml config/robot_setup.toml
~~~

The local file is ignored by Git.

Example robot entry:

~~~toml
[[robots]]
label = "robot-1"
sphero_name = "YOUR_REAL_BLE_NAME"
vicon_subject = "YOUR_TRACKER_OBJECT"
vicon_segment = "YOUR_TRACKER_SEGMENT"
body_length_mm = 200.0
body_width_mm = 140.0
body_yaw_offset_deg = 0.0
~~~

The staged examples **and both reference controllers** now consume the same TOML mapping.

See [Configuration](docs/configuration.md).

## Staged hardware validation

### 1. Vicon only — no robot command

~~~powershell
python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
~~~

Move each physical chariot by hand and prove one physical body maps to one software label.

### 2. One Sphero

~~~powershell
python examples/01_single_sphero_smoke_test.py --config config/robot_setup.toml --speed 60 --seconds 0.5
~~~

### 3. All configured Spheros

~~~powershell
python examples/02_multi_sphero_smoke_test.py --config config/robot_setup.toml
~~~

### 4. Measure every robot's heading basis

~~~powershell
python examples/04_heading_calibration.py --config config/robot_setup.toml
~~~

The calibration example now processes configured robots **sequentially** and pauses before each robot moves. Results are saved to artifacts/heading_calibration.json.

### 5. Single-chariot closed loop

~~~powershell
python reference_controllers/single_chariot_vicon_circle.py --config config/robot_setup.toml
~~~

Choose a specific configured label with --robot when required.

### 6. Three-chariot dry run

~~~powershell
python reference_controllers/three_chariot_square_swarm.py --config config/robot_setup.toml --dry-run --timeout 8 --no-digital-twin
~~~

### 7. Conservative first live run

~~~powershell
python reference_controllers/three_chariot_square_swarm.py --config config/robot_setup.toml --laps 1 --max-speed 140 --calibration-speed 180
~~~

The example value 180 is **not a universal calibration recommendation**. Use a command that gives sufficient measured displacement on your hardware while preserving clear travel margin.

## Mission cap versus calibration command

The advanced controller separates two concepts deliberately:

- **--max-speed** — caps normal mission commands and mission stiction/breakaway pulses;
- **--calibration-speed** — controls the startup displacement-calibration move; default is 255 because the original loaded platform required decisive motion for measurement.

A low mission cap does not imply a low startup calibration command. Read [Safety](docs/safety.md) and the [end-to-end tutorial](docs/end-to-end-tutorial.md) before a live run.

## Why displacement calibration matters

Sphero command headings and the Vicon world axes should not be assumed to align.

~~~text
Sphero heading 0°  -> measured Vicon displacement e0
Sphero heading 90° -> measured Vicon displacement e90

desired world vector
        |
        v
project into measured basis
        |
        v
Sphero command heading
~~~

This handles mounting orientation and command/world-frame differences that can otherwise create sideways or mirrored motion.

## Controller architecture

~~~mermaid
flowchart LR
    V["Vicon DataStream pose"] --> F["continuity + velocity state"]
    F --> C["per-robot heading/course calibration"]
    P["square moving reference"] --> G["formation / trajectory control"]
    C --> G
    G --> S["boundary + body-separation safeguards"]
    S --> M["world motion vector"]
    M --> H["world -> Sphero heading"]
    H --> B["BLE commands"]
    F --> D["logs + digital twin"]
    G --> D
~~~

The three-robot implementation is centralised: one process observes the Vicon state and commands all agents.

## Documentation

**New users**
- [End-to-end first-run tutorial](docs/end-to-end-tutorial.md)
- [Getting started](docs/getting-started.md)
- [Configuration](docs/configuration.md)
- [Hardware setup](docs/hardware-setup.md)

**Vicon**
- [Detailed Vicon setup workflow](docs/vicon-setup.md)
- [Tracker real-UI screenshot atlas](docs/vicon-tracker-ui-guide.md)
- [DataStream SDK setup](docs/vicon-datastream.md)
- [Operator quick checklist](docs/vicon-operator-checklist.md)
- [Procedure/source provenance](docs/vicon-procedure-sources.md)

**Engineering and operations**
- [Architecture](docs/architecture.md)
- [Control design](docs/control-design.md)
- [Safety](docs/safety.md)
- [Validation](docs/validation.md)
- [Troubleshooting](docs/troubleshooting.md)

## Quality gates

Local release check:

~~~powershell
python tools/release_check.py
~~~

The local release check performs Python compilation, unit tests, privacy scanning and the advanced-controller dry run.

GitHub Actions additionally checks the repository's configured lint/type/test/build/security/documentation workflows, including Ruff, mypy, coverage, package build/install, CodeQL, secret/privacy scanning and Pages build/deployment.

## Privacy model

Real local values belong in ignored configuration/runtime artifacts, not in the public tree.

Do not commit:

- private network addresses;
- BLE identifiers;
- local user paths;
- raw logs containing local identifiers;
- unreviewed calibration/learning artifacts.

Run:

~~~powershell
python tools/privacy_scan.py .
~~~

before publishing local changes.

## Limitations

- BLE is not hard real-time.
- Vicon accuracy depends on calibration, visibility and rigid-object quality.
- loaded chariots can differ materially in breakaway and rolling response;
- simulation validates software structure, not exact hardware dynamics;
- collision/boundary logic is a safeguard, not a safety-certified protection system;
- the public Sphero backend is third-party software;
- the reference controllers are research/prototyping software, not safety-certified motion products.

## Releases

Tagged releases are published on the GitHub Releases page. The repository is the recommended form when you need examples, docs, configuration templates and reference controllers alongside the package.

See [v1.0.0 release notes](docs/releases/v1.0.0.md).

## License

MIT. Third-party SDKs, documentation and hardware APIs retain their own licences.

Sphero/BOLT and Vicon are trademarks of their respective owners. This independent project is not endorsed by either vendor.
