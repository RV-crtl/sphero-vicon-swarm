# Vicon setup and reproduction workflow

This is the **end-to-end lab procedure** for reproducing the Vicon side of the Sphero swarm system.

If you are standing at the Tracker workstation, also keep these two pages open:

- [Vicon Tracker visual guide](vicon-tracker-ui-guide.md)
- [Vicon operator quick checklist](vicon-operator-checklist.md)

For the Python/network side, use:

- [Vicon DataStream SDK setup](vicon-datastream.md)

> The public repository deliberately excludes credentials, real device IDs, private IP addresses, saved lab configurations and vendor installers. Use the local laboratory SOP for those values.

---

## What this guide is trying to make reproducible

A new user should be able to:

1. start Tracker and verify the camera system;
2. decide whether the existing calibration is still credible;
3. recalibrate and set the world frame if required;
4. create one rigid object for each chariot;
5. verify the object identities physically;
6. configure the repository with the correct object/device mapping;
7. verify live DataStream output without commanding robots;
8. calibrate Sphero heading against the Vicon world frame;
9. validate one robot;
10. run the swarm conservatively.

The most important rule is:

> **Do not enable robot motion until Vicon object identity, coordinate direction, occlusion behaviour and workspace bounds have all been verified by hand.**

---

## 1. Start the Vicon system

Use the local laboratory procedure to power the Vicon camera network, host workstation and any approved local networking equipment.

Then:

1. Start **Vicon Tracker 4.x**.
2. Open the **System** panel.
3. Confirm that every camera expected for the capture volume is present.
4. Confirm the cameras are connected/contributing rather than missing or disabled.
5. Open a **3D View** and move a reflective marker through the volume.
6. Confirm reconstructed marker motion appears in the expected region.

If the expected cameras are not available, stop here and resolve the camera/network issue.

### Tracker 4.x orientation

![Tracker 4.x orientation map](assets/vicon/tracker4-overview.svg)

The four panels used most in this workflow are:

- **System**
- **Camera Calibration**
- **Tracking**
- **Connections**

The **System Health Report** is also important because it gives a quick view of calibration and tracking quality.

See [Vicon Tracker visual guide](vicon-tracker-ui-guide.md) for a click-map explanation.

---

## 2. Check System Health before deciding to recalibrate

Do not recalibrate automatically just because a calibration is old.

Instead, inspect the **System Health Report** and the actual tracking behaviour.

At minimum check:

### Performance

Watch:

- latency;
- dropped frames.

Unexpectedly high or unstable latency, or dropped frames during normal object tracking, should be investigated before closed-loop control.

### Calibration Details

Check that the enabled cameras expected to contribute are calibrated.

A camera that is enabled but uncalibrated should not be treated as valid tracking input.

### Centroid Connectivity

Tracker uses this to help indicate how well moving camera centroids are being associated with tracked object markers.

Poor connectivity can indicate:

- reflections;
- object occlusion;
- object geometry problems;
- calibration drift;
- a changed capture environment.

### Image Error

Tracker defines Image Error as the difference, in pixels, between observed 2D centroids and where the corresponding 3D points re-project into the camera image.

The Tracker 4.4 System Health Report flags cameras above an image-error threshold of **1.0 pixel**. Treat that as a diagnostic indicator rather than a universal pass/fail criterion: what matters is whether the system is stable and accurate enough for the application.

### Camera movement / temperature

If a camera has been bumped, moved, or the system has experienced a significant environmental change, recalibration may be warranted even if an old calibration file still loads.

---

## 3. Inspect the capture volume for unwanted reflections

Before calibration:

1. switch the Workspace to a **Cameras** view;
2. inspect each camera for bright points not associated with the calibration device;
3. physically remove or cover reflective sources where practical;
4. only mask reflections that cannot reasonably be removed;
5. confirm the actual robot working area is visible to multiple cameras.

Vicon recommends physically removing unwanted reflections where possible because masked pixels are intentionally excluded from tracking.

---

## 4. Calibrate the cameras when required

Use the current **Camera Calibration** panel.

![Tracker 4.x calibration click map](assets/vicon/tracker4-calibration-click-map.svg)

### 4.1 Mask persistent reflections

In **Camera Calibration → Masking**:

1. select the relevant cameras;
2. start automatic masking if appropriate;
3. inspect the result;
4. manually mask residual reflection regions only when required;
5. verify useful regions of the image have not been masked.

### 4.2 Select the correct wand

In **Camera Calibration → Wand Wave**, select the calibration object appropriate to the installed system.

Tracker 4.4 commonly shows **Active Wand v2** as the default, but use the wand configured for the actual lab system.

### 4.3 Perform the wand wave

1. Click **Wave All**.
2. Move the wand throughout the useful capture volume.
3. Cover the area **and height** in which the chariots will run.
4. Try to keep the wand visible to multiple cameras.
5. Continue until Tracker has collected sufficient coverage.
6. Allow Auto Stop to complete when enabled, or stop according to the current Tracker feedback.

Do not only wave the wand in the center of the room if the robots will travel near the edges.

### 4.4 Set the world origin

After the wand wave, the cameras are calibrated relative to one another, but the swarm still needs a meaningful global frame.

In **Camera Calibration → Volume Setup → Set Volume Origin**:

1. choose the approved calibration/origin object;
2. place it in the lab-approved physical location and orientation;
3. click **Start Set Origin**;
4. wait until Tracker has sufficient information;
5. click **Set Origin**;
6. inspect the displayed world axes.

Tracker's convention displays world axes using the standard red/green/blue axis colouring.

Physically verify:

- which direction is +X;
- which direction is +Y or +Z on the horizontal plane;
- which axis is vertical;
- whether the floor appears at the intended height.

### 4.5 Save the calibration

After validation, save the calibration using the laboratory's naming/versioning convention.

### 4.6 Using a saved calibration

A saved calibration can be useful **only if the camera geometry is still valid**.

Do not blindly load a historical calibration because it happens to exist.

Before accepting a saved calibration, confirm:

- cameras have not been moved;
- the expected cameras match the calibration;
- System Health is credible;
- object tracking is stable across the intended workspace;
- a known displacement is reconstructed sensibly.

If these checks fail, recalibrate.

---

## 5. Validate the calibrated volume

Before defining robot objects:

1. move a reflective marker through the central area;
2. move it near the planned workspace edges;
3. look for jumps or dropouts;
4. confirm the floor and positive axes;
5. if possible, compare one known real-world distance with the reconstructed distance;
6. inspect System Health again.

If tracking quality is poor at the edge of the intended workspace:

- improve coverage/calibration if possible;
- otherwise reduce the software workspace to the region that is genuinely reliable.

Do not use controller tuning to hide bad tracking.

---

## 6. Build a good marker constellation for each chariot

Tracker 4.4 requires at least four unassigned marker trajectories to create an object and notes that **five or more is recommended**.

For this project, each robot constellation should be:

- rigid;
- asymmetric;
- well spaced;
- mechanically secure;
- visible from the expected camera geometry;
- clearly different from the other robots.

Avoid:

- straight-line arrangements;
- symmetric rectangles that can look similar after rotation;
- three robots with almost identical marker spacing;
- markers that flex on loose bodywork;
- clusters where one marker routinely hides behind another.

A good constellation reduces object swapping and improves re-acquisition after partial occlusion.

---

## 7. Create a rigid object in Tracker

![Tracker 4.x object creation click map](assets/vicon/tracker4-object-click-map.svg)

For each chariot:

1. Place the robot in the capture volume.
2. Open the **Tracking** panel.
3. In **View Filters**, ensure **Unlabeled Markers** are visible.
4. If needed, in the **Processing** panel verify unlabeled reconstructions are enabled.
5. Select the robot's marker trajectories:
   - **Ctrl + click** to select individual markers; or
   - **Alt + drag** to box-select a group.
6. Select at least four markers; five or more is preferred.
7. In the **Tracking** panel's **Object** field, enter a unique name.
8. Click **Create**.
9. Move the robot by hand.
10. Confirm the new object follows only that physical robot.

### Add a marker

1. select the object;
2. Ctrl-select the unassigned marker;
3. click **Add Marker**.

### Remove a marker

1. select the marker;
2. click **Remove Marker**.

Tracker prevents removal if the object would be left with fewer than four markers.

### If objects are confused with one another

First change the physical marker geometry.

Software thresholds can help tracking, but mechanically distinct constellations are the better solution for multiple near-identical robots.

---

## 8. Save the object/tracking configuration

After each object has been created and physically verified, save the Tracker object/tracking configuration according to the current Tracker/lab workflow.

Do not rely on an object that only exists in the current unsaved session.

Use clear object names and avoid tying public code to a particular lab's historical naming scheme.

---

## 9. Verify robot identity manually

This is a required safety check.

For each robot:

1. disable commanded robot motion;
2. move physical robot 1 by hand;
3. confirm only the intended Tracker object moves;
4. repeat for robot 2;
5. repeat for robot 3;
6. record the mapping.

Record:

| Physical robot | Sphero/BLE device | Vicon subject/object | Vicon segment |
|---|---|---|---|
| Robot 1 | local value | local value | local value |
| Robot 2 | local value | local value | local value |
| Robot 3 | local value | local value | local value |

Never infer the mapping from the order in which devices were discovered.

---

## 10. Install the Vicon DataStream SDK

The swarm repository uses the **Vicon DataStream SDK**, not Tracker's UDP Object Stream.

Follow the dedicated guide:

[Vicon DataStream SDK setup](vicon-datastream.md)

The important points are:

- install the vendor SDK separately;
- install/import the Python `vicon_dssdk` package in the environment running this repository;
- use the local Tracker host plus DataStream port, normally `:801`;
- do **not** enable UDP merely because old lab notes mention UDP streaming.

Vicon's own documentation recommends DataStream when TCP/IP is available because the UDP object stream exposes only a smaller subset of data.

---

## 11. Create the local repository configuration

Copy the public template:

### Windows PowerShell

```powershell
Copy-Item config/robot_setup.example.toml config/robot_setup.toml
```

### macOS/Linux

```bash
cp config/robot_setup.example.toml config/robot_setup.toml
```

Edit the local file:

```toml
[vicon]
server = "TRACKER_HOST:801"
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
vicon_subject = "Robot_1"
vicon_segment = "Robot_1"
```

Repeat the robot block for each robot.

The real local configuration is ignored by Git.

### `floor_plane`

Use:

- `XY` when X/Y are the horizontal axes;
- `XZ` when X/Z are the horizontal axes.

Verify this physically rather than guessing.

---

## 12. Verify DataStream without commanding robots

Run:

```bash
python examples/03_vicon_pose_monitor.py \
  --config config/robot_setup.toml \
  --seconds 20
```

Expected output includes, for each robot:

- planar X in millimetres;
- planar Y in millimetres;
- yaw;
- occlusion state.

### Move-one-robot test

With the pose monitor running:

1. move robot 1 only;
2. confirm only `robot-1` moves in software;
3. repeat for robots 2 and 3;
4. rotate each robot;
5. move along physically known +X / +Y or +Z directions;
6. briefly occlude the markers and confirm occlusion is reported.

If any identity or axis mapping is wrong, fix it before continuing.

### Watch the Connections panel

In Tracker 4.x:

1. open **View → Connections**;
2. start the pose monitor;
3. confirm a DataStream client appears.

You do not need to enable the UDP Object Stream for this test.

---

## 13. Understand what the repository reads

The reusable adapter is:

```text
src/sphero_vicon_swarm/tracking/vicon.py
```

It:

1. creates a DataStream client;
2. connects to the configured host;
3. requests live frames;
4. enables segment data;
5. reads global translation;
6. reads global Euler rotation;
7. projects the configured floor plane into 2D;
8. returns `Pose2D(x_mm, y_mm, yaw_deg, occluded)`.

The control architecture therefore uses Vicon as navigation truth.

However, it does **not** assume that Vicon yaw and Sphero commanded heading are the same frame.

That frame relationship is measured next.

---

## 14. Calibrate Sphero command heading against Vicon displacement

Run:

```bash
python examples/04_heading_calibration.py --config config/robot_setup.toml
```

The calibration commands two approximately orthogonal headings and measures actual displacement in Vicon.

Conceptually:

```text
Sphero heading 0°  → measured Vicon vector e0
Sphero heading 90° → measured Vicon vector e90
```

Those measured vectors define the transformation used to convert desired Vicon-world motion into Sphero command heading.

Before calibration:

- clear the robot's path;
- confirm the correct rigid body is mapped;
- confirm stable Vicon tracking;
- start at conservative speed;
- be ready to stop the robot.

Repeat calibration after changes such as:

- swapping the Sphero;
- changing chariot mounting;
- changing wheel alignment;
- changing floor conditions significantly;
- moving the Sphero orientation in the carrier.

The full three-chariot reference controller performs a fresh calibration by default for hardware runs.

---

## 15. Validate one robot before three

Run the single-chariot reference controller first:

```bash
python reference_controllers/single_chariot_vicon_circle.py
```

Verify:

- Vicon motion is smooth;
- commanded world direction is physically sensible;
- stop/interruption stops motion;
- tracking loss does not create uncontrolled behaviour;
- workspace limits are conservative.

Do not proceed to the swarm until the one-robot test is credible.

---

## 16. Dry-run the swarm

Run:

```bash
python reference_controllers/three_chariot_square_swarm.py \
  --dry-run --timeout 8 --no-digital-twin
```

This validates the control software without BLE/Vicon hardware.

---

## 17. First physical swarm run

For the first live run:

```bash
python reference_controllers/three_chariot_square_swarm.py \
  --laps 1 --max-speed 160
```

Keep the initial run conservative.

Watch:

- all three Vicon poses;
- object identity;
- occlusion;
- pairwise spacing;
- workspace edges;
- formation error;
- stalled chariots/static friction;
- stop behaviour.

Keep an operator ready to interrupt the run.

---

## 18. Complete reproduction checklist

Before calling the setup reproducible:

- [ ] expected Vicon cameras are online;
- [ ] System Health is credible;
- [ ] unwanted reflections have been removed/masked;
- [ ] calibration is valid;
- [ ] origin/floor plane is known;
- [ ] coordinate directions have been verified physically;
- [ ] each robot has a unique rigid constellation;
- [ ] each Tracker object has been saved;
- [ ] each physical robot maps to exactly one Vicon object;
- [ ] each Sphero/BLE device maps to the correct Vicon object;
- [ ] `vicon_dssdk` imports;
- [ ] DataStream connection works;
- [ ] Vicon-only pose monitor works;
- [ ] units are millimetres;
- [ ] occlusion behaviour has been observed;
- [ ] workspace bounds are conservative;
- [ ] heading/displacement calibration works;
- [ ] single-robot closed-loop test works;
- [ ] software dry-run passes;
- [ ] physical operating area is clear;
- [ ] immediate stop path is available.

The shorter [operator checklist](vicon-operator-checklist.md) is intended for use at the workstation once this full guide is understood.

---

## Troubleshooting

### Tracker opens but some cameras are missing

- check power/network hardware;
- check the expected System panel camera list;
- check the local camera network interface;
- restart only according to the local laboratory SOP;
- do not proceed until the intended camera set is understood.

### Persistent bright points appear in camera views

Remove or cover reflective sources first.

Mask only reflections that cannot be physically removed.

### Wand calibration will not complete

Check:

- wand selection;
- wand visibility;
- camera coverage;
- masked areas;
- whether enough of the real working volume has been covered.

### Object will not create

Check:

- at least four unassigned trajectories are selected;
- five or more are preferable;
- markers are rigid;
- pattern is asymmetric;
- unlabeled markers/reconstructions are visible.

### Object swaps identity with another robot

Physically redesign the marker constellation so the patterns are more distinct.

Do not rely on software filtering alone to distinguish almost-identical rigid bodies.

### Python cannot import `vicon_dssdk`

See [DataStream SDK setup](vicon-datastream.md). Fix the Python/SDK installation before debugging controller code.

### Python imports the SDK but cannot connect

Check:

- Tracker is running;
- local host/address is correct;
- port is the DataStream port, normally 801;
- client and server can communicate across the approved lab network;
- firewall/network policy.

### Connection works but pose is wrong

Check:

- object name;
- segment name;
- `floor_plane`;
- axis direction;
- live object tracking;
- occlusion.

### Pose is correct but robot drives in the wrong direction

Run heading calibration again.

This repository intentionally does not assume Sphero heading and Vicon axes are aligned.

---

## Official Vicon references

This guide was cross-checked against current Vicon documentation:

- [Vicon Tracker documentation](https://help.vicon.com/page/tracker-docs)
- [Tracker 4.4 User Guide](https://help.vicon.com/download/attachments/376309877/Vicon%20Tracker%20User%20Guide.pdf)
- [Vicon DataStream SDK downloads](https://www.vicon.com/software/datastream-sdk/?section=downloads)
- [DataStream SDK 1.13 documentation](https://help.vicon.com/space/DSSDK113)
- [DataStream SDK Developer's Guide](https://help.vicon.com/download/attachments/726007858/Vicon%20DataStream%20SDK%20Developer%27s%20Guide.pdf)

---

## Related project documentation

- [Vicon Tracker visual guide](vicon-tracker-ui-guide.md)
- [Vicon DataStream SDK setup](vicon-datastream.md)
- [Vicon operator quick checklist](vicon-operator-checklist.md)
- [Getting started](getting-started.md)
- [Configuration](configuration.md)
- [Hardware setup](hardware-setup.md)
- [Architecture](architecture.md)
- [Control design](control-design.md)
- [Safety](safety.md)
- [Troubleshooting](troubleshooting.md)
- [Validation](validation.md)
