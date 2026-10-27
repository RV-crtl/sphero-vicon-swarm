# Vicon setup and reproduction workflow

This page is the practical, step-by-step path for reproducing the Vicon side of the Sphero swarm system.

It is intended to answer a simple question:

> If I walk into a lab with the robots, Vicon Tracker and this repository, what do I do first, and what do I verify before I run the swarm?

Site-specific credentials, private IP addresses and restricted-network details are deliberately not stored in this public repository. Use the local laboratory operator instructions for those items.

## Overview

Follow the stages in this order:

1. Start the Vicon workstation and confirm the camera system is healthy.
2. Check the capture volume and remove unwanted reflections.
3. Calibrate the cameras if required and establish the volume origin.
4. Create one rigid Vicon object for each robot/chariot.
5. Save the Tracker configuration.
6. Configure the robot-to-Vicon mappings in `config/robot_setup.toml`.
7. Verify live Vicon pose streaming without commanding a robot.
8. Verify the correct rigid body moves when each physical robot is moved.
9. Calibrate the mapping from Sphero command headings to Vicon-world displacement.
10. Run a single-robot closed-loop test.
11. Run the three-robot controller first in dry-run mode, then at low speed on hardware.

Do not skip directly to multi-robot motion.

---

## 1. Start Tracker and confirm the camera system

On the dedicated Vicon workstation:

1. Power the Vicon camera network and any required local streaming/network equipment according to the laboratory procedure.
2. Open **Vicon Tracker 4.x**.
3. Open the **System** panel.
4. Confirm that every camera expected in the capture volume is connected and contributing.
5. In the 3D view, confirm that reconstructed markers are visible when reflective markers are moved through the working volume.
6. Check that the camera count is what you expect before continuing.

If one or more cameras are missing, stop here and fix the camera/network issue before creating objects or running the swarm.

### Basic Tracker navigation

In the 3D view:

- left-drag rotates the view;
- right-drag zooms;
- the time-bar/play controls can pause and resume live capture;
- reconstructed unlabeled markers are visible as points before they are assigned to an object.

Tracker UI details vary slightly between minor versions, so use the current Vicon Tracker documentation if a control has moved.

---

## 2. Check the capture volume before calibration

Before calibrating, remove unnecessary reflective objects from the capture volume where practical.

Unwanted reflections can be reconstructed as false markers and reduce calibration or tracking quality.

For a full calibration:

1. Switch to a **Cameras** view.
2. Inspect the views for unwanted reflections.
3. Physically remove or cover reflective sources where possible.
4. If a reflection cannot be removed, use Tracker's camera masking tools.
5. Confirm that the required working volume is visible to multiple cameras.

Vicon recommends physical removal of unwanted reflections rather than masking when possible.

---

## 3. Calibrate the Vicon cameras

If the system is already calibrated and the laboratory procedure confirms that the calibration is valid, you can proceed to the validation checks below.

Recalibrate if cameras have moved, calibration is reported invalid, tracking quality is poor, or the local laboratory procedure requires a fresh calibration.

### 3.1 Mask unwanted reflections

In **Camera Calibration**:

1. Select all cameras.
2. Use the masking workflow to remove persistent unwanted reflections.
3. Confirm the masks do not hide useful parts of the capture volume.

### 3.2 Perform the wand wave

1. In **Camera Calibration**, select the correct calibration wand for the system.
2. Start **Wave All**.
3. Move the wand throughout the usable capture volume.
4. Cover the height and area in which the chariots will actually move.
5. Continue until Tracker has collected enough frames for all cameras.
6. Stop the wand wave if it does not stop automatically.
7. Review the calibration result and image-error/status indicators.

The cameras are calibrated relative to each other after the wand wave, but the world origin still needs to be established.

### 3.3 Set the volume origin

Use the laboratory's calibration object or approved origin procedure.

The origin should be placed consistently relative to the floor and operating area so that:

- the horizontal motion plane is known;
- the positive axes are known;
- the floor height is sensible;
- the swarm workspace can be expressed in millimetres in the same frame.

If the laboratory uses a fixed calibration object, use the saved local procedure for positioning it.

### 3.4 Validate the calibration

Before creating robot objects:

1. Confirm all required cameras report calibrated/healthy status.
2. Place a marker or known object at several positions in the working volume.
3. Confirm reconstructed motion is smooth and spatially plausible.
4. Confirm the floor plane and axis directions.
5. If possible, check a known physical distance against Tracker's reconstructed distance.
6. Check tracking at the edges of the intended swarm area, not only in the centre.

If tracking degrades badly near a boundary, reduce the software workspace rather than relying on poor-quality edge data.

Official Vicon references:

- Tracker camera masking: https://help.vicon.com/space/Tracker40/14190245
- Tracker calibration/origin guidance: https://help.vicon.com/space/Tracker40/14189152

---

## 4. Create a tracked object for each chariot

Each robot needs its own rigid, asymmetric marker constellation.

For this project, use **at least four markers per rigid body**, arranged so that the pattern is:

- rigid;
- asymmetric;
- unique from the other robots;
- visible from the camera geometry;
- physically well-spaced on the chariot.

Avoid giving multiple robots near-identical constellations.

### Create an object in Tracker

For each robot:

1. Place the chariot in the visible Vicon volume.
2. Pause live capture if required by your Tracker workflow.
3. Open the **Tracking** panel.
4. Identify the unlabeled marker constellation belonging to that chariot.
5. Hold **Ctrl** and left-click each marker belonging to the object.
6. Enter a clear object name.
7. Click **Create**.
8. Confirm the new object appears in the object list.
9. Resume tracking and move the chariot by hand.
10. Confirm the yellow/tracked constellation follows only that physical chariot.

If Tracker refuses to create the object, re-check that the marker pattern is rigid, sufficiently asymmetric and that the selected markers belong to the same body.

### Add or remove a marker

If required:

1. Select the object.
2. Ctrl-select a marker to add and use **Add Marker**.
3. Select an existing object marker and use **Remove Marker** to remove it.

Keep enough markers for robust tracking.

### Save the Tracker setup

After all robot objects are tracking correctly, save the Tracker configuration/object setup using the local laboratory convention.

Do not rely on an unsaved temporary object definition.

---

## 5. Record the exact Vicon object names

The software does not guess which Vicon rigid body belongs to which Sphero.

Record, for each robot:

- Sphero/BLE device name;
- Vicon subject/object name;
- Vicon segment name;
- physical chariot identity.

Then explicitly verify the mapping by moving one robot at a time and observing which Vicon object changes.

A wrong mapping can make a controller command the wrong robot from another robot's pose data.

---

## 6. Create the local software configuration

Copy the public template:

### Windows PowerShell

```powershell
Copy-Item config/robot_setup.example.toml config/robot_setup.toml
```

### macOS/Linux

```bash
cp config/robot_setup.example.toml config/robot_setup.toml
```

Edit `config/robot_setup.toml`.

Example:

```toml
[vicon]
server = "127.0.0.1:801"
floor_plane = "XY"
yaw_euler_index = 2
yaw_sign = 1.0
yaw_offset_deg = 0.0

[workspace]
x_min_mm = -2000.0
x_max_mm = 2000.0
y_min_mm = -2000.0
y_max_mm = 2000.0
soft_margin_mm = 300.0

[[robots]]
label = "robot-1"
sphero_name = "YOUR_DEVICE_NAME"
vicon_subject = "Robot 1"
vicon_segment = "Robot 1"

[[robots]]
label = "robot-2"
sphero_name = "YOUR_DEVICE_NAME"
vicon_subject = "Robot 2"
vicon_segment = "Robot 2"

[[robots]]
label = "robot-3"
sphero_name = "YOUR_DEVICE_NAME"
vicon_subject = "Robot 3"
vicon_segment = "Robot 3"
```

Replace the placeholders with the local values from Tracker and the Sphero devices.

The real configuration file is ignored by Git.

### Choosing `floor_plane`

Use:

- `XY` when horizontal motion is represented by Vicon X and Y;
- `XZ` when horizontal motion is represented by Vicon X and Z.

Do not assume this. Verify it by moving a chariot by hand and watching the coordinates.

---

## 7. Verify Vicon streaming before enabling motion

Install the vendor Vicon DataStream SDK Python bindings for the host machine.

The repository expects the Python module:

```text
vicon_dssdk
```

Then run:

```bash
python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
```

Expected result: each configured robot repeatedly prints:

- planar X position in millimetres;
- planar Y position in millimetres;
- yaw;
- occlusion state.

### Manual mapping test

With the pose monitor running:

1. Move **robot 1 only** by hand.
2. Confirm only the `robot-1` software pose changes substantially.
3. Repeat for robot 2.
4. Repeat for robot 3.
5. Rotate each robot and inspect the reported yaw.
6. Move each robot toward the intended workspace limits and confirm coordinate direction and magnitude.
7. Briefly occlude the markers and confirm occlusion is reported.

If any robot name, subject or segment is wrong, fix the configuration before proceeding.

---

## 8. Understand what the software reads from Vicon

The reusable Vicon adapter is:

```text
src/sphero_vicon_swarm/tracking/vicon.py
```

At runtime it:

1. connects to the configured Vicon server;
2. requests live frames;
3. reads each configured segment's global translation;
4. reads its global Euler rotation;
5. projects the configured floor plane into 2D;
6. reports a `Pose2D` for each robot.

The swarm controller therefore uses Vicon as the external navigation truth.

The controller does **not** depend on the Vicon yaw angle to infer the Sphero command frame. Steering-frame alignment is calibrated from measured displacement.

---

## 9. Calibrate Sphero heading against Vicon displacement

The Sphero command heading and the Vicon world frame are not assumed to be aligned.

Run:

```bash
python examples/04_heading_calibration.py --config config/robot_setup.toml
```

The calibration performs two short commanded moves approximately 90 degrees apart and measures the resulting Vicon displacement.

Conceptually:

```text
Sphero heading 0 deg  -> measured Vicon displacement e0
Sphero heading 90 deg -> measured Vicon displacement e90
```

These two measured vectors define the robot's command-heading basis in the Vicon world frame.

Before running calibration:

- clear space around the robot;
- start at a conservative speed;
- verify Vicon tracking is stable;
- verify the correct Vicon object maps to the robot being commanded.

The full three-chariot reference controller performs its own fresh calibration by default before a hardware mission.

---

## 10. Validate one robot before the swarm

Run the single-chariot milestone before the three-robot controller:

```bash
python reference_controllers/single_chariot_vicon_circle.py
```

Observe:

- whether commanded world directions produce the expected physical directions;
- whether Vicon position changes smoothly;
- whether the robot remains inside the intended workspace;
- whether stopping the program stops the robot;
- whether occlusion or bad tracking produces safe behaviour.

Do not move to multi-robot operation until the single-robot path is credible.

---

## 11. Validate the three-robot controller without hardware motion

Run:

```bash
python reference_controllers/three_chariot_square_swarm.py \
  --dry-run --timeout 8 --no-digital-twin
```

This exercises the control architecture without BLE or Vicon hardware.

Use it to verify that the software installation and controller start-up are healthy before a live run.

---

## 12. Run the physical swarm conservatively

For the first physical run, use one lap and a conservative maximum command:

```bash
python reference_controllers/three_chariot_square_swarm.py \
  --laps 1 --max-speed 160
```

The hardware controller defaults to a **fresh calibration** rather than silently reusing an old one.

During the run, watch:

- each robot's Vicon pose;
- formation quality;
- workspace boundaries;
- pairwise spacing;
- marker occlusion;
- whether any chariot stalls because of static friction;
- whether the controller stops all robots on interruption.

Keep an operator ready to stop the run.

---

## 13. Reproduction checklist

Before calling the setup reproducible, confirm all of the following:

- [ ] all expected Vicon cameras are online;
- [ ] calibration is valid for the working volume;
- [ ] the world origin/floor plane is known;
- [ ] each chariot has a unique rigid marker constellation;
- [ ] all Vicon objects have been saved;
- [ ] object names exactly match the local TOML configuration;
- [ ] moving one physical robot changes only its intended software pose;
- [ ] Vicon units are millimetres;
- [ ] workspace axis directions have been checked by hand;
- [ ] occlusion behaviour has been observed;
- [ ] the Vicon-only pose monitor works;
- [ ] heading/displacement calibration works;
- [ ] single-robot closed-loop motion has been checked;
- [ ] dry-run of the three-robot controller passes;
- [ ] physical workspace is clear and boundaries are conservative;
- [ ] an immediate stop path is available.

---

## Troubleshooting

### No camera data

- confirm camera/network power;
- confirm Tracker sees the expected cameras;
- confirm the host is using the correct Vicon network interface;
- do not proceed until all required cameras are contributing.

### Markers visible but object will not create

- use a rigid constellation;
- use at least four well-spaced markers;
- make the pattern asymmetric;
- ensure only markers belonging to that object are selected.

### Object jumps between robots

The constellations are probably too similar, partially occluded, or incorrectly defined. Redesign the marker patterns so each rigid body is unique.

### Python cannot connect to Vicon

- verify the Tracker/DataStream endpoint;
- verify the vendor DataStream SDK and Python bindings are installed;
- verify `server` in the local TOML file;
- run the Vicon pose monitor before any controller.

### Coordinates appear mirrored or use the wrong horizontal plane

Verify `floor_plane`, axis directions and yaw settings in the configuration. Do not compensate blindly in controller gains.

### Robot moves in an unexpected direction even though Vicon coordinates are correct

Run the heading calibration again. The Sphero command frame and Vicon world frame are intentionally calibrated rather than assumed.

### Tracking degrades near the operating-area edge

Reduce the software workspace and/or improve Vicon coverage. Do not rely on low-quality edge tracking for boundary recovery.

---

## Related project documentation

- [Getting started](getting-started.md)
- [Configuration](configuration.md)
- [Hardware setup](hardware-setup.md)
- [Architecture](architecture.md)
- [Control design](control-design.md)
- [Safety](safety.md)
- [Troubleshooting](troubleshooting.md)
- [Validation](validation.md)
