# Vicon Tracker 4.0 + Sphero swarm — reproducible setup

This is the **operator-level reproduction procedure** for the Vicon side of the project.

It combines three clearly separated sources:

- **Vicon manufacturer procedure** — official Vicon Tracker/DataStream documentation;
- **RAS lab procedure** — the Tracker 4.0 checklist supplied with the project;
- **Project procedure** — the steps required by this repository's Python/Vicon/Sphero software.

Nothing on this page should be read as a substitute for the Vicon manual. Where a step is specific to the local RAS lab, it is identified as such. Private credentials, private network addresses and restricted-network information are intentionally not published.

## 0. Read this before touching the robots

The supplied lab checklist is for **Vicon Tracker 4.0**.

If the workstation is running a different Tracker release:

- use the manufacturer documentation for that version;
- do not assume a control is in the same place;
- retain the same verification logic: healthy cameras → valid calibration → correct rigid-body identity → verified DataStream pose → heading calibration → one robot → swarm.

For actual screenshots of the supplied lab UI, see the **[Tracker 4.0 actual-UI guide](vicon-tracker-ui-guide.md)**.

---

## 1. Start the Vicon system — RAS lab procedure

The supplied RAS checklist records this startup sequence:

1. Start/login to the dedicated Vicon workstation using the local laboratory procedure.
2. Verify the Vicon camera-network hardware is powered.
3. Verify any local equipment required for the lab's streaming/network arrangement is powered and isolated in accordance with local network policy.
4. Open **Vicon Tracker 4.0**.
5. Open **System**.
6. Confirm that **all cameras expected for that laboratory setup are active** before proceeding.
7. In the 3D view, move a reflective marker through the working volume and confirm that reconstructed marker points are visible.

The old checklist names a particular number of cameras and local networking devices. Those values are intentionally not treated as universal requirements in this public guide.

![Actual Tracker interface](assets/vicon/tracker-ui-actual-sanitized.jpg)

*Real screenshot from the supplied lab material; private/local connection values redacted only.*

### Stop condition

Do not continue if:

- one or more expected cameras are missing;
- Tracker reports a camera/system fault;
- marker reconstruction is unstable;
- the intended robot volume is not adequately visible.

---

## 2. Prepare the capture volume — Vicon manufacturer procedure

Vicon's Tracker 4.0 guidance should be followed for the exact masking/calibration process.

Manufacturer source:

**https://help.vicon.com/space/Tracker40/14190245**

The important manufacturer principle is to deal with unwanted reflections before calibration. Physically removing/covering unwanted reflective sources is preferable when practical; masking is used where unwanted reflections cannot be removed.

For this project:

1. Clear the intended chariot operating area.
2. Remove or cover avoidable reflective items.
3. Inspect camera views for persistent false reflections.
4. Apply masking only as required by the Vicon procedure.
5. Ensure masking does not remove useful parts of the volume in which the robots will operate.

Do not copy a mask from an old setup blindly if cameras or the physical volume have changed.

---

## 3. Calibrate cameras and establish the world frame — Vicon manufacturer procedure

Use Vicon's **Tracker 4.0 calibration/origin procedure**:

**https://help.vicon.com/space/Tracker40/14189152**

Do not substitute a locally invented click sequence for that manufacturer page.

At a high level the calibration task is:

1. use the calibration object/wand specified for the installed Vicon system;
2. collect calibration observations across the **actual volume the chariots will use**;
3. allow Tracker to solve the camera calibration;
4. establish the world origin/floor frame using the lab-approved Vicon origin procedure;
5. save the resulting setup/calibration;
6. verify tracking quality throughout the intended robot workspace.

### Project-specific validation after calibration

After completing the Vicon procedure:

- move a marker/object along the expected positive world axes and identify the horizontal motion plane;
- confirm the reconstructed units are consistent with millimetres;
- check the centre and edges of the planned swarm workspace;
- record which Vicon axes correspond to horizontal motion.

The project supports either `XY` or `XZ` as the horizontal plane. **Do not guess this value.**

---

## 4. Create one rigid Vicon object per chariot — RAS lab procedure

The supplied Tracker 4.0 checklist states that each object should use a rigid marker constellation with **at least four markers**, arranged so the pattern is asymmetric, visible, unique and reasonably well spaced.

For each chariot:

1. attach the rigid marker constellation;
2. place the chariot in the capture volume;
3. pause capture with **Spacebar** if required by the lab workflow;
4. open **View → Tracking**;
5. select the markers belonging to that object using **Ctrl + left-click** in the 3D view;
6. in **Tracking → Setup**, enter a clear object name;
7. choose **Create**;
8. confirm the object appears in the object list and tracks the chariot;
9. use **Add Marker** / **Remove Marker** if the object definition needs correction;
10. save the Tracker configuration.

See the **[actual Tracker UI guide](vicon-tracker-ui-guide.md)** for screenshots from the supplied lab system.

### Mandatory identity test

This is a project safety/reproducibility step:

1. move Robot 1 by hand while Robots 2 and 3 remain still;
2. confirm only Robot 1's Vicon object changes;
3. repeat for Robots 2 and 3;
4. record the exact object/subject and segment names.

Do not rely on object-list order.

---

## 5. Install/configure the Vicon DataStream SDK — project + manufacturer

This repository reads Vicon data through the **Vicon DataStream SDK Python bindings** (`vicon_dssdk`).

It does **not** require the older local UDP Object Stream workflow in order to run the Python controller.

Read:

**[Vicon DataStream setup](vicon-datastream.md)**

and the official Vicon DataStream SDK documentation for your installed SDK release:

**https://help.vicon.com/space/DSSDK113**

The repository adapter is:

```text
src/sphero_vicon_swarm/tracking/vicon.py
```

It connects to the configured DataStream server, requests live frames and reads:

- global segment translation;
- global Euler rotation;
- occlusion state.

---

## 6. Create the local project configuration

Copy the template.

### Windows PowerShell

```powershell
Copy-Item config/robot_setup.example.toml config/robot_setup.toml
```

### macOS/Linux

```bash
cp config/robot_setup.example.toml config/robot_setup.toml
```

Then set the **local** values.

```toml
[vicon]
server = "127.0.0.1:801"
floor_plane = "XY"
yaw_euler_index = 2
yaw_sign = 1.0
yaw_offset_deg = 0.0

[[robots]]
label = "robot-1"
sphero_name = "YOUR_DEVICE_NAME"
vicon_subject = "Robot 1"
vicon_segment = "Robot 1"
```

Repeat the robot block for each chariot.

The example values are placeholders. Use the values from your local Tracker/Sphero setup.

The real `config/robot_setup.toml` is ignored by Git.

---

## 7. Verify the Vicon stream before commanding any Sphero

Run:

```bash
python examples/03_vicon_pose_monitor.py \
  --config config/robot_setup.toml \
  --seconds 20
```

Expected output for each robot includes:

- planar X position;
- planar Y position;
- yaw;
- occlusion flag.

### Physical verification

With the pose monitor running:

1. move Robot 1 by hand;
2. confirm only `robot-1` changes substantially;
3. repeat for each robot;
4. rotate each robot and inspect the yaw response;
5. move a robot along each horizontal world axis and confirm the coordinate sign;
6. briefly occlude a rigid body and observe the occlusion state.

If any mapping is wrong, fix the TOML configuration **before enabling BLE motion**.

---

## 8. Verify Sphero communication separately

Run the staged smoke tests:

```bash
python examples/01_single_sphero_smoke_test.py \
  --config config/robot_setup.toml
```

then:

```bash
python examples/02_multi_sphero_smoke_test.py \
  --config config/robot_setup.toml
```

Confirm each software robot label commands the intended physical Sphero.

---

## 9. Calibrate Sphero heading to the measured Vicon world frame

Run:

```bash
python examples/04_heading_calibration.py \
  --config config/robot_setup.toml
```

The calibration does not assume that Sphero heading 0° equals Vicon +X.

It:

1. records the initial Vicon position;
2. commands a short move at one Sphero heading;
3. measures the resulting Vicon displacement;
4. repeats for an approximately orthogonal heading;
5. builds the transformation from Sphero command headings to Vicon-world direction.

Clear sufficient space before this test.

Recalibrate after meaningful mechanical/mounting changes.

---

## 10. Validate one closed-loop robot

Before the three-chariot controller, run the single-chariot milestone:

```bash
python reference_controllers/single_chariot_vicon_circle.py
```

Verify:

- Vicon pose remains stable;
- commanded world direction matches physical direction;
- interrupt/stop behaviour works;
- the robot remains inside conservative workspace bounds.

---

## 11. Run the three-robot controller in software first

```bash
python reference_controllers/three_chariot_square_swarm.py \
  --dry-run --timeout 8 --no-digital-twin
```

A successful dry run does **not** prove the physical system is ready; it confirms the software path can execute without the hardware interfaces.

---

## 12. Physical three-robot run

For an initial live run:

```bash
python reference_controllers/three_chariot_square_swarm.py \
  --laps 1 --max-speed 160
```

Before starting:

- all three Vicon objects must be visible and correctly mapped;
- the workspace must be clear;
- the software workspace limits must fit inside the reliable Vicon volume;
- an operator must have an immediate stop path;
- the controller's fresh calibration sequence must complete successfully.

Do not reuse a historical calibration merely because it existed on a previous day.

---

## 13. Reproduction acceptance checklist

A repeat user should be able to demonstrate all of the following before claiming the setup is reproduced:

- [ ] expected Vicon cameras are active;
- [ ] manufacturer calibration procedure completed or existing calibration independently validated;
- [ ] world origin and horizontal plane confirmed;
- [ ] each chariot has a unique rigid object;
- [ ] Tracker setup saved;
- [ ] each physical robot maps to exactly one intended Vicon object;
- [ ] DataStream Python client receives stable poses;
- [ ] coordinates/axis signs confirmed by hand;
- [ ] occlusion behaviour observed;
- [ ] each Sphero identity verified separately;
- [ ] heading/displacement calibration completed;
- [ ] single-robot closed-loop behaviour validated;
- [ ] three-robot dry run completed;
- [ ] physical workspace and stop path checked.

---

## Sources and traceability

### Manufacturer

- Vicon Tracker 4.0 documentation: https://help.vicon.com/space/Tracker40
- Tracker 4.0 masking guidance: https://help.vicon.com/space/Tracker40/14190245
- Tracker 4.0 calibration/origin guidance: https://help.vicon.com/space/Tracker40/14189152
- Vicon DataStream SDK documentation: https://help.vicon.com/space/DSSDK113

### Supplied lab material

The local steps for Tracker 4.0 startup, **System**, **View → Tracking**, marker selection, **Create**, **Add Marker**, **Remove Marker**, saving object definitions and the lab UI screenshots come from the RAS Vicon checklist/material supplied with this project.

### Project

Repository-specific commands, configuration format, Vicon adapter behaviour and heading-calibration logic come from this repository itself.

This separation is intentional: it makes clear which instructions are manufacturer-defined, which are local lab practice and which are part of the swarm software.
