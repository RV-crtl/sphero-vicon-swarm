# Vicon Tracker UI guide — actual lab screenshots

This page deliberately uses **real Vicon Tracker screenshots**, not reconstructed or synthetic UI drawings.

## Version/source legend

| Material | Version | How it is used here |
|---|---|---|
| Sanitized lab screenshot below | **Tracker 4.0** | Actual interface used in the lab; private network addresses are redacted |
| Legacy calibration screenshot below | **Tracker 3.9** | Actual older training material; included only to help identify the legacy calibration layout |
| Procedure text | **Vicon manufacturer documentation** | Current Tracker 4.4 where available; Tracker 4.0 documentation for the lab-version-specific masking/origin workflow |

!!! warning "Do not mix versions blindly"
    Tracker 3.9, 4.0, 4.3 and 4.4 do not have identical layouts. The screenshots below are labeled by version. When a control has moved, follow the linked Vicon documentation for the version installed on the workstation.

---

## 1. Actual Tracker 4.0 lab interface

![Actual Vicon Tracker 4.0 lab interface with private addresses redacted](assets/vicon/tracker4-actual-overview-annotated.jpg)

This is an **actual Tracker 4.0 screenshot from the lab material supplied with this project**. The only edits are callouts and redaction of site-specific addresses.

The numbered items show the parts of Tracker used by this project:

1. **View menu** — use this to open panels such as **Tracking**, **Connections**, and calibration-related views.
2. **3D View** — use this to verify that a tracked rigid body follows the physical chariot you move.
3. **System Health Report** — use this to inspect tracking-system health before commanding robots.
4. **Connections / DataStream** — a DataStream client appears here when the repository connects to Tracker.
5. **UDP output** — visible in Tracker, but **not required by this repository**. The Python code uses Vicon DataStream SDK.

The screenshot also shows a tracked chariot in the 3D View. That is the level of visual confirmation you should obtain before running closed-loop control.

---

## 2. Actual Tracker 4.0 DataStream/Connections panel

![Actual Tracker 4.0 DataStream Connections panel](assets/vicon/tracker4-actual-datastream-connections.jpg)

This crop is from the same real Tracker 4.0 session.

For this repository:

1. Start Tracker and ensure the rigid objects are tracking.
2. Open the **Connections** panel.
3. Start the Python pose monitor:

   ```bash
   python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
   ```

4. Watch the **Data Stream** connection area.
5. A client should appear when the Python process connects.
6. The project uses the normal DataStream endpoint, conventionally **port 801**.

The UDP Object Stream controls shown lower in Tracker are a separate output mechanism. They are not used by `src/sphero_vicon_swarm/tracking/vicon.py`.

See [DataStream SDK setup](vicon-datastream.md).

---

## 3. Manufacturer calibration workflow — Tracker 4.4/current

The steps below follow the **Vicon Tracker 4.4 User Guide**, not an invented reconstruction.

### 3.1 Remove or mask unwanted reflections

Vicon's Tracker 4.0 masking documentation says to **physically remove or cover unwanted reflective sources where practical before masking**.

For automatic masking in Tracker 4.x:

1. Remove unnecessary reflective objects from the capture volume.
2. Select the **Cameras** view.
3. In the **System** panel, select all cameras.
4. In **Camera Calibration → Masking**, click **Mask All**.
5. Wait until unwanted light pixels have been masked.
6. Click **Stop**.
7. Inspect each camera view and confirm the unwanted reflections have been eliminated.

If automatic masking misses a reflection, Vicon's Tracker 4.0 procedure is:

1. select a single camera;
2. open **Camera Calibration → Masking** and show the advanced controls;
3. click **Manual Mask Paint**;
4. **Alt+drag** to select an area;
5. press **E** to add the selection to the mask;
6. press **R** to remove a selection;
7. click **Stop** to apply changes.

Manufacturer source: [Vicon Tracker 4.0 — Mask cameras](https://help.vicon.com/space/Tracker40/14190245).

### 3.2 Perform the wand wave

The current Tracker 4.4 user guide specifies:

1. complete camera masking first;
2. in **Camera Calibration → Wand Wave**, display the advanced properties if required;
3. select the correct calibration object/wand;
4. click **Wave All**;
5. wave the wand throughout the **actual capture volume**, covering depth and height;
6. keep the wand visible to as many cameras as possible;
7. watch the **Wand Count** feedback — it moves from red toward green as enough data is captured;
8. allow **Auto Stop** to finish when enabled, or stop manually after sufficient coverage.

Manufacturer source: [Vicon Tracker 4.4 User Guide](https://help.vicon.com/download/attachments/376309877/Vicon%20Tracker%20User%20Guide.pdf), camera-calibration section (wand-wave procedure).

### 3.3 Set the volume origin

The Tracker 4.4 manufacturer procedure is:

1. place the calibration device in the required origin position/orientation;
2. in **Camera Calibration → Volume Setup**, show the advanced parameters;
3. under **Set Volume Origin**, select the appropriate calibration device;
4. click **Start Set Origin**;
5. wait until Tracker has enough information and the control becomes available;
6. click **Set Origin**;
7. verify the displayed world axes:
   - **X = red**
   - **Y = green**
   - **Z = blue**
8. physically verify that the chosen origin and axes make sense for the robot workspace.

Manufacturer source: [Vicon Tracker 4.4 User Guide](https://help.vicon.com/download/attachments/376309877/Vicon%20Tracker%20User%20Guide.pdf), volume-origin procedure.

Do not “fix” a wrong Vicon world frame later by randomly swapping controller signs. Establish the coordinate frame deliberately, then configure `floor_plane`, yaw convention, and the repository's displacement calibration.

---

## 4. Actual legacy Tracker 3.9 calibration UI

![Actual Tracker 3.9 calibration tab from local training material](assets/vicon/tracker39-actual-calibrate-tab.jpg)

This is an **actual Tracker 3.9 screenshot from the supplied lab training material**.

It is included because older local notes may still refer to the **Calibrate** tab and **Create Camera Masks**. That terminology/layout belongs to Tracker 3.9.

Do **not** use this image as a pixel-perfect guide for Tracker 4.x. In Tracker 4.x, use the **Camera Calibration** panel and the manufacturer steps above.

Vicon's own Tracker 3.9 documentation describes the legacy Resources pane as containing **System**, **Calibrate**, **Objects**, and **Recording** tabs:
[Vicon Tracker 3.9 — Resources pane](https://help.vicon.com/space/Tracker39/14057713).

---

## 5. Creating a rigid object — manufacturer Tracker 4.4 procedure

The Tracker 4.4 User Guide gives the following object-creation procedure.

### Marker geometry

For best results, the object should be rigid and use an asymmetric marker arrangement.

Tracker 4.4 requires you to select **at least four unassigned marker trajectories**; Vicon's 4.4 guide says **five or more is recommended**.

### Create the object

1. Place the chariot, with its reflective markers attached, inside the calibrated capture volume.
2. If the markers are not visible in the 3D View:
   - in **View Filters**, enable **Unlabeled Markers**;
   - in the **Processing** panel, ensure **Enable Unlabeled Reconstructions** is selected.
3. Select the marker trajectories:
   - hold **Ctrl** and click markers individually; or
   - hold **Alt** and drag a selection box around the marker group.
4. In the **Tracking** panel, enter a **unique object name** in the **Object** field.
5. Click **Create**.
6. Move the physical chariot by hand and confirm the newly created object follows **only that chariot**.
7. Save the Tracker setup/object preset according to the local lab procedure.

Manufacturer source: [Vicon Tracker 4.4 User Guide](https://help.vicon.com/download/attachments/376309877/Vicon%20Tracker%20User%20Guide.pdf), “Create objects”, p.190 in the 2025-09-17 revision.

### Add or remove a marker

Vicon's Tracker 4.4 procedure is:

**Add**
1. select the object in the **Tracking** panel or 3D View;
2. hold **Ctrl** and select the marker;
3. click **Add Marker**.

**Remove**
1. select the marker;
2. click **Remove Marker**.

Tracker will not allow removal if the object would be left with fewer than four markers.

Manufacturer source: [Vicon Tracker 4.4 — Add or remove a marker](https://help.vicon.com/space/Tracker44/376309055).

---

## 6. Local lab checklist vs manufacturer procedure

The supplied local checklist independently confirms the practical Tracker 4.0 workflow used in the lab:

- open **View → Tracking**;
- place the marked object in the capture area;
- select the object's visible markers with **Ctrl + left-click**;
- name the object in the Tracking panel;
- click **Create**;
- use **Add Marker** / **Remove Marker** when required;
- save the configuration.

Where the local checklist and newer Vicon 4.4 documentation differ in layout or terminology, this project follows the **manufacturer documentation for the installed Tracker version**.

---

## 7. System Health — what the real Tracker panel means

The actual Tracker 4.0 screenshot at the top of this page shows the **System Health Report**.

Vicon's System Health documentation defines the relevant metrics as follows.

### Performance

- **Latency** — elapsed time from the midpoint of the camera shutter interval until data is ready for a client.
- **Drop Frames** — unprocessed frames as a percentage of total frames.

If latency or dropped frames change unexpectedly during a run, stop and investigate rather than assuming the controller is at fault.

### Calibration Details

Use this to check calibration state and identify uncalibrated cameras. Vicon explicitly notes that calibration age alone does not prove a calibration is bad.

### Centroid Connectivity

This reflects how well moving 2D centroids are associated with tracked object markers. Poor values can be consistent with issues such as reflections, occlusion, changed object geometry, or calibration drift.

### Image Error

Vicon defines Image Error as the pixel distance between observed 2D centroids and the reprojection of reconstructed 3D points into the camera image.

Tracker's System Health UI flags cameras above the configured diagnostic threshold (the Tracker 4.1 documentation describes a 1.0-pixel header threshold). Treat this as a diagnostic signal, not a universal pass/fail specification for every experiment.

Manufacturer source: [Vicon Tracker — Understand System Health Report](https://help.vicon.com/space/Tracker41/14323303).

---

## 8. What to press for this repository, end to end

Once Tracker itself is healthy:

### A. Verify the Vicon client

```bash
python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
```

Then physically move each chariot one at a time and verify the correct software label changes.

### B. Verify Sphero identity

```bash
python examples/01_single_sphero_smoke_test.py --config config/robot_setup.toml
python examples/02_multi_sphero_smoke_test.py --config config/robot_setup.toml
```

### C. Calibrate Sphero heading against measured Vicon displacement

```bash
python examples/04_heading_calibration.py --config config/robot_setup.toml
```

### D. Run one robot closed-loop

```bash
python reference_controllers/single_chariot_vicon_circle.py
```

### E. Dry-run the swarm

```bash
python reference_controllers/three_chariot_square_swarm.py --dry-run --timeout 8 --no-digital-twin
```

### F. First physical swarm run

```bash
python reference_controllers/three_chariot_square_swarm.py --laps 1 --max-speed 160
```

The full sequence and stop criteria are in [Vicon setup and reproduction workflow](vicon-setup.md).

---

## Manufacturer references

- [Tracker 4.4 User Guide](https://help.vicon.com/download/attachments/376309877/Vicon%20Tracker%20User%20Guide.pdf)
- [Tracker 4.0 — Mask cameras](https://help.vicon.com/space/Tracker40/14190245)
- [Tracker 4.0 — Scale calibration and set a fixed origin](https://help.vicon.com/space/Tracker40/14189152)
- [Tracker 4.4 — Add or remove a marker](https://help.vicon.com/space/Tracker44/376309055)
- [Tracker 4.1 — Understand System Health Report](https://help.vicon.com/space/Tracker41/14323303)
- [Tracker 3.9 — Resources pane (legacy layout)](https://help.vicon.com/space/Tracker39/14057713)
- [Vicon DataStream SDK documentation](https://help.vicon.com/space/DSSDK113)
