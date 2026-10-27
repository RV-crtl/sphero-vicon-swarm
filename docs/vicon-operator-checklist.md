# Vicon operator quick checklist

Use this at the workstation **after reading the full [Vicon setup workflow](vicon-setup.md)**.

For actual UI screenshots and exact manufacturer button names, keep the [Tracker UI guide](vicon-tracker-ui-guide.md) open.

![Actual Tracker 4.0 lab interface](assets/vicon/tracker4-actual-overview-annotated.jpg)

## A. Start and verify Tracker

- [ ] Start the local Vicon workstation/camera network using the lab SOP.
- [ ] Open Vicon Tracker.
- [ ] Confirm the expected cameras are present in **System**.
- [ ] Move a reflective marker and confirm plausible reconstruction in **3D View**.
- [ ] Inspect **System Health Report** for obvious problems.

## B. If calibration is required

### Remove/mask reflections

- [ ] Remove or cover reflective sources where practical.
- [ ] Workspace → **Cameras**.
- [ ] Select the cameras in **System**.
- [ ] **Camera Calibration → Masking → Mask All**.
- [ ] Wait for unwanted light pixels to become masked/blue.
- [ ] Click **Stop**.
- [ ] Inspect every camera view.

### Wand wave

- [ ] **Camera Calibration → Wand Wave**.
- [ ] Select the correct physical calibration object.
- [ ] Click **Wave All**.
- [ ] Cover depth and height across the actual robot volume.
- [ ] Watch **Wand Count** and concentrate on low-count cameras.
- [ ] Let **Auto Stop** finish, or stop only after sufficient coverage.
- [ ] Review Image Error status.

### Origin

- [ ] Workspace → **3D View**.
- [ ] Place/orient the calibration device at the intended origin.
- [ ] **Camera Calibration → Volume Setup**.
- [ ] Under **Set Volume Origin**, select the correct device.
- [ ] Click **Start Set Origin**.
- [ ] When enabled, click **Set Origin**.
- [ ] Verify **X red / Y green / Z blue** physically.
- [ ] If required, use the separate **Set Floor Plane** workflow.

## C. Create each rigid object

![Actual legacy Tracker object-creation screen](assets/vicon/tracker39-actual-object-workflow.jpg)

*Actual Tracker 3.9 lab-training screenshot. Follow the current Tracker 4.4 control names below.*

- [ ] **View → Tracking**.
- [ ] Place the chariot in the calibrated volume.
- [ ] If required, enable **Unlabeled Markers** and **Unlabeled Reconstructions**.
- [ ] Select markers with **Ctrl + click** or **Alt + drag**.
- [ ] Select at least **4**; Vicon recommends **5+**.
- [ ] Enter a unique name in the **Object** field.
- [ ] Click **Create**.
- [ ] Move the chariot by hand and confirm only that object follows it.
- [ ] Use **Add Marker** / **Remove Marker** only if needed.
- [ ] Save the local Tracker object/setup.

## D. Record the mapping

| Physical chariot | Sphero/BLE name | Vicon object/subject | Vicon segment |
|---|---|---|---|
| Robot 1 | local value | local value | local value |
| Robot 2 | local value | local value | local value |
| Robot 3 | local value | local value | local value |

Never infer this from discovery order.

## E. Configure the repository

```powershell
Copy-Item config/robot_setup.example.toml config/robot_setup.toml
```

Enter:

- Tracker host/port;
- floor plane;
- each Sphero name;
- each Vicon object/subject;
- each segment;
- conservative measured workspace limits.

## F. Verify DataStream — no robot motion

![Actual Tracker 4.0 DataStream area](assets/vicon/tracker4-actual-datastream-connections.jpg)

- [ ] Install/import `vicon_dssdk`.
- [ ] Tracker → **View → Connections**.
- [ ] Run:

```bash
python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
```

- [ ] Confirm a DataStream client appears.
- [ ] Move one chariot at a time and verify software identity.
- [ ] Check axis direction.
- [ ] Check yaw.
- [ ] Briefly test occlusion.

## G. Verify the Spheros

```bash
python examples/01_single_sphero_smoke_test.py --config config/robot_setup.toml
python examples/02_multi_sphero_smoke_test.py --config config/robot_setup.toml
```

## H. Calibrate command heading vs Vicon displacement

```bash
python examples/04_heading_calibration.py --config config/robot_setup.toml
```

- [ ] clear space;
- [ ] verify the correct rigid object;
- [ ] verify both calibration displacements are sensible.

## I. One robot before three

```bash
python reference_controllers/single_chariot_vicon_circle.py
```

## J. Dry-run, then physical swarm

```bash
python reference_controllers/three_chariot_square_swarm.py --dry-run --timeout 8 --no-digital-twin
python reference_controllers/three_chariot_square_swarm.py --laps 1 --max-speed 160
```

Before live motion:

- [ ] all three objects are visible;
- [ ] mappings are confirmed;
- [ ] workspace is clear;
- [ ] boundaries are conservative;
- [ ] an operator can stop the run immediately.

## Debug in this order

**camera health → calibration → rigid-object identity → DataStream → Sphero identity → heading calibration → single robot → swarm**

For exact source/version provenance, see [Vicon procedure sources](vicon-procedure-sources.md).
