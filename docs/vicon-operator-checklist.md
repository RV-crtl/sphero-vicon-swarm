# Vicon operator quick checklist

Use this as the **bench-side checklist** once the full [Vicon setup and reproduction workflow](vicon-setup.md) has been read.

For screenshots/click maps, keep the [Vicon Tracker visual guide](vicon-tracker-ui-guide.md) open beside this page.

For SDK installation/network debugging, use [Vicon DataStream SDK setup](vicon-datastream.md).

It condenses the practical sequence into one page for a returning user.

![Actual Vicon Tracker 4.0 lab interface, sanitized](assets/vicon/tracker4-actual-overview-annotated.jpg)

*Actual Tracker 4.0 lab screenshot. Site-specific addresses are redacted. Use the numbered callouts to locate the View menu, 3D View, System Health, DataStream connection area, and optional UDP settings.*

For exact UI/version notes and manufacturer-source links, use the [Vicon Tracker UI guide](vicon-tracker-ui-guide.md).

## A. Start the Vicon system

- [ ] Start the dedicated Vicon workstation.
- [ ] Confirm the Vicon camera-network hardware is powered.
- [ ] Confirm any local streaming/network equipment required by the lab is powered and isolated according to local network policy.
- [ ] Open **Vicon Tracker 4.x**.
- [ ] Open **System** and confirm every expected camera is online and contributing.
- [ ] Check the 3D view: reflective markers should reconstruct as points when moved through the capture volume.
- [ ] Check **System Health Report**: calibration status, latency/drop frames, Centroid Connectivity and Image Error.
- [ ] Stop if the expected camera count or tracking volume is not healthy.

## B. Check or calibrate the volume

If the current calibration is known to be valid, perform the validation checks and continue.

If cameras have moved, Tracker reports an invalid calibration, or tracking quality is poor:

- [ ] Open the **Cameras** view.
- [ ] Remove or cover unnecessary reflective objects.
- [ ] Mask persistent reflections only when they cannot be physically removed.
- [ ] Select the correct calibration wand.
- [ ] Run the wand-wave calibration throughout the **actual robot working volume**.
- [ ] Set/verify the volume origin using the lab-approved origin procedure.
- [ ] Confirm floor plane and positive axis directions.
- [ ] Check tracking in the centre **and near the planned workspace edges**.
- [ ] Save the valid Tracker setup.

## C. Create the rigid bodies

For **each** chariot:

- [ ] Use at least four rigid, asymmetric, well-spaced reflective markers; **five or more is preferred** where practical.
- [ ] Make the constellation visibly different from the other robots.
- [ ] Place the chariot in the capture volume.
- [ ] Open the **Tracking** panel.
- [ ] Ctrl-select only that chariot's markers.
- [ ] Give the object a clear, unique name.
- [ ] Click **Create**.
- [ ] Move the chariot by hand and confirm only that Vicon object follows it.
- [ ] Add/remove markers if necessary.
- [ ] Save the object/setup.

## D. Record the robot mapping

For each physical robot, write down:

| Physical robot | Sphero/BLE name | Vicon subject/object | Vicon segment |
|---|---|---|---|
| Robot 1 | local value | local value | local value |
| Robot 2 | local value | local value | local value |
| Robot 3 | local value | local value | local value |

Do **not** infer this mapping from list order.

## E. Create the local configuration

Copy the template:

```powershell
Copy-Item config/robot_setup.example.toml config/robot_setup.toml
```

or:

```bash
cp config/robot_setup.example.toml config/robot_setup.toml
```

Then edit:

- `vicon.server`
- `vicon.floor_plane`
- each `sphero_name`
- each `vicon_subject`
- each `vicon_segment`
- measured workspace limits and conservative soft margin

The real local file is ignored by Git.

## F. Verify the DataStream path — no robot commands

This project uses the **Vicon DataStream SDK**. Tracker's UDP Object Stream is optional and is **not required** for the swarm controller.

- [ ] Install/import `vicon_dssdk`.
- [ ] In Tracker, open **View → Connections**.
- [ ] Confirm the configured DataStream endpoint/host is the approved local value.

## G. Verify Vicon only — no robot commands

Run:

```bash
python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
```

Then:

- [ ] move Robot 1 by hand; only `robot-1` should move in software;
- [ ] repeat for Robots 2 and 3;
- [ ] rotate each robot and inspect yaw;
- [ ] move along the expected +X and +Y/+Z directions;
- [ ] briefly occlude markers and confirm occlusion is reported;
- [ ] verify positions are in millimetres;
- [ ] verify the software workspace matches the safe tracking volume.

**Do not enable closed-loop motion if any mapping is ambiguous.**

## H. Verify one Sphero at a time

Run the single-device and multi-device smoke tests:

```bash
python examples/01_single_sphero_smoke_test.py --config config/robot_setup.toml
python examples/02_multi_sphero_smoke_test.py --config config/robot_setup.toml
```

Keep speeds low and maintain a clear stop path.

## I. Calibrate Sphero heading to Vicon world coordinates

Run:

```bash
python examples/04_heading_calibration.py --config config/robot_setup.toml
```

The calibration measures Vicon displacement for two approximately orthogonal Sphero command headings.

- [ ] clear space around the robot;
- [ ] confirm the correct rigid body is tracking;
- [ ] confirm both calibration moves produce sensible displacement;
- [ ] repeat if mounting, wheel/chariot mechanics or marker geometry changed.

## J. Validate closed-loop motion

Single robot first:

```bash
python reference_controllers/single_chariot_vicon_circle.py
```

Check:

- [ ] commanded motion agrees with Vicon-world direction;
- [ ] stop/interrupt behaviour is safe;
- [ ] tracking remains stable;
- [ ] the robot stays inside conservative bounds.

## K. Validate the three-robot controller

Software-only dry run:

```bash
python reference_controllers/three_chariot_square_swarm.py --dry-run --timeout 8 --no-digital-twin
```

Then a conservative hardware run:

```bash
python reference_controllers/three_chariot_square_swarm.py --laps 1 --max-speed 160
```

Before starting:

- [ ] all three rigid bodies are visible;
- [ ] all three robot mappings are confirmed;
- [ ] the workspace is clear;
- [ ] boundaries are conservative;
- [ ] an operator is ready to stop the run;
- [ ] a fresh heading calibration is allowed to complete.

## If something looks wrong

Stop the robots and use the full [Vicon setup and reproduction workflow](vicon-setup.md) plus the [troubleshooting guide](troubleshooting.md).

The safest debugging order is:

**camera health → calibration → rigid-body identity → DataStream pose → Sphero identity → heading calibration → single robot → swarm**.
