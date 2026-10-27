# Validation

The project is validated as a **sequence of gates**, not as one final demo. A multi-robot run is meaningful only if the lower layers have already passed.

## Validation matrix

| Level | Test | Hardware motion? | Pass evidence |
|---|---|---:|---|
| software | import/doctor | no | environment reported correctly |
| software | config parser | no | TOML parses and values are sane |
| software | unit tests | no | pytest passes |
| software | simulator | simulated | state changes without exception |
| tracking | camera/system health | no robot motion | stable Vicon reconstruction |
| tracking | rigid-body identity | hand movement only | one physical body ↔ one label |
| tracking | pose monitor | hand movement only | axes/yaw/occlusion credible |
| BLE | one-Sphero smoke | short move | intended robot moves/stops |
| BLE | multi-Sphero smoke | zero-speed commands | all devices connect |
| calibration | heading displacement | sequential short moves | valid non-collinear basis |
| control | single chariot | yes | closed-loop milestone stable |
| integration | advanced dry-run | simulated | mission/logging/cleanup pass |
| integration | live swarm | yes | conservative lap within bounds |

## Software-only release check

Run:

```powershell
python tools/release_check.py
```

The release check performs compilation, tests, privacy scanning and an advanced-controller dry run.

You can also run the components separately:

```powershell
python -m compileall -q src examples
pytest
python tools/privacy_scan.py .
python reference_controllers/three_chariot_square_swarm.py --dry-run --timeout 8 --no-digital-twin
```

## Configuration validation

```powershell
python -m sphero_vicon_swarm validate-config --config config/robot_setup.toml
```

This is a syntax/sanity gate, not proof that the physical identity mapping is correct.

## Vicon identity validation

```powershell
python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
```

Move each physical chariot by hand.

Pass only when:

- one intended label changes;
- X/Y directions match the world axes;
- yaw changes plausibly;
- occlusion flag responds to a deliberate brief occlusion.

## Sphero identity validation

Single device:

```powershell
python examples/01_single_sphero_smoke_test.py --config config/robot_setup.toml --speed 60 --seconds 0.5
```

Multiple devices:

```powershell
python examples/02_multi_sphero_smoke_test.py --config config/robot_setup.toml
```

Do not proceed if discovery selects the wrong physical robot.

## Per-robot heading validation

```powershell
python examples/04_heading_calibration.py --config config/robot_setup.toml
```

The example now calibrates all configured robots sequentially by default and writes measured evidence to:

```text
artifacts/heading_calibration.json
```

A pass requires enough displacement in both calibration axes and a valid basis.

## Single-chariot closed-loop gate

```powershell
python reference_controllers/single_chariot_vicon_circle.py --config config/robot_setup.toml
```

A meaningful pass includes:

- no sustained occlusion;
- calibration succeeds;
- wrong-way protection does not trip;
- path response is bounded;
- Ctrl+C stops/cleans up.

## Advanced dry-run gate

```powershell
python reference_controllers/three_chariot_square_swarm.py --config config/robot_setup.toml --dry-run --timeout 8 --no-digital-twin
```

Dry-run exercises asymmetric robot response and stiction handling without hardware.

## First live swarm validation

Use one lap and chosen caps.

Example:

```powershell
python reference_controllers/three_chariot_square_swarm.py --config config/robot_setup.toml --laps 1 --max-speed 140 --calibration-speed 180
```

Review both live behaviour and the generated log.

A visually impressive trajectory is not enough. Check:

- body clearance;
- workspace-edge clearance;
- formation error;
- cross-track error;
- command speed/heading;
- stiction activity;
- identity/tracking continuity.

## Regression rule

After changing a lower layer, re-run all dependent gates.

Examples:

- change Vicon object definition → repeat pose identity + calibration + closed-loop tests;
- change wheel/chariot → repeat Sphero identity + calibration + closed-loop tests;
- change controller only → software tests + dry-run + conservative hardware validation;
- change workspace/origin → repeat Vicon axis/bounds verification.

For the exact operator sequence, use the [end-to-end tutorial](end-to-end-tutorial.md).
