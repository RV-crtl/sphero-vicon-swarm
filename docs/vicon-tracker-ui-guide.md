# Vicon Tracker UI guide — actual screenshots + manufacturer-verified steps

This page uses **actual Vicon Tracker screenshots** from the lab material supplied with this project. It does **not** use a reconstructed or synthetic Tracker interface.

## Read the version labels first

| Evidence | Version | Purpose |
|---|---|---|
| Tracker lab screenshot | Tracker 4.0 | Shows the real interface used in the lab |
| DataStream crop | Tracker 4.0 | Shows the real Connections/Data Stream area |
| Calibration screenshot | Tracker 3.9 | Legacy lab visual reference only |
| Object-creation screenshot | Tracker 3.9 | Legacy lab visual reference only |
| Procedure text | Tracker 4.4 manufacturer guide | Current button names and sequence |

!!! warning "Screenshots and procedure are intentionally separated"
    A Tracker 3.9 screenshot is **not** presented as Tracker 4.4. Use the screenshots to recognize the real application, then follow the manufacturer procedure for the version installed on the workstation.

The current manufacturer procedure used here is the **Vicon Tracker 4.4 User Guide, 17 September 2025, Revision 1**.

---

## 1. Actual Tracker 4.0 lab interface

![Actual Tracker 4.0 lab interface](assets/vicon/tracker4-actual-overview-annotated.jpg)

This is an actual Tracker 4.0 lab screenshot. Site-specific network addresses were redacted before publication; the Tracker UI itself is unchanged.

The useful areas visible here are:

1. **View/menu area** — panels such as Tracking and Connections can be opened from the View menu when they are not already visible.
2. **3D View** — use this to confirm that the rigid object shown by Tracker follows the physical chariot you are moving.
3. **System Health Report** — use this before closed-loop motion to inspect tracking health.
4. **Connections / Data Stream** — use this to see whether a DataStream client has connected.
5. **UDP output settings** — visible in Tracker, but not used by this repository's Python Vicon adapter.

### What to do on this screen

Before running any robot command:

- confirm the expected cameras are online;
- verify at least one real marker/object appears in the 3D View;
- physically move one chariot and confirm the correct Tracker object moves;
- inspect System Health for obvious camera/calibration/tracking problems.

---

## 2. Actual Tracker 4.0 DataStream view

![Actual Tracker 4.0 DataStream/Connections view](assets/vicon/tracker4-actual-datastream-connections.jpg)

This crop comes from the same real Tracker 4.0 session.

For this project:

1. In Tracker, open **View → Connections** if the panel is hidden.
2. Start the repository's Vicon-only monitor:

   ```bash
   python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
   ```

3. Watch the **Data Stream** area in Tracker.
4. Confirm a client appears when Python connects.
5. Then move each chariot by hand and verify the software label that moves.

The repository uses `vicon_dssdk` / Vicon DataStream. It does **not** require enabling Tracker's UDP Object Stream.

---

## 3. System Health — manufacturer definitions

The right side of the actual Tracker 4.0 screenshot shows a real **System Health Report**.

Vicon Tracker 4.4 defines System Health as a default pane that consolidates key system metrics. The current manufacturer guide lists these sections:

- **Performance**
- **Calibration Details**
- **Centroid Connectivity**
- **Image Error**
- **Camera Temperatures**
- **Camera Accelerometers**
- **Auto Recover Camera Pose**
- **Auto Bias Handling**

### Performance

Vicon defines:

- **Latency** — elapsed time from the midpoint of the camera shutter interval until data is ready to be sent to a client.
- **Drop Frames** — unprocessed frames as a percentage of total frames.

Unexpected dropped frames or unstable latency should be investigated before running closed-loop control.

### Calibration Details

Use this to identify uncalibrated cameras and the age of the current calibration.

An old calibration is **not automatically bad**; judge it alongside tracking quality, camera movement, temperature change and image error.

### Centroid Connectivity

This is the proportion of moving 2D centroids that are successfully associated with tracked object markers.

Low connectivity can point toward:

- reflections;
- marker occlusion;
- poor object geometry;
- calibration drift;
- changed camera geometry.

### Image Error

Vicon defines Image Error as the pixel difference between observed 2D centroids and where reconstructed 3D points re-project into the camera image.

Tracker 4.4's System Health header reports cameras above a **1.0 pixel diagnostic threshold**. Treat that as a troubleshooting indicator, not as a universal project acceptance criterion.

Manufacturer reference: **Tracker 4.4 User Guide, “Understand System Health Report”, pp. 177–187**.

---

# Camera calibration

## 4. Actual legacy calibration UI from the lab material

![Actual Tracker 3.9 calibration interface](assets/vicon/tracker39-actual-calibrate-tab.jpg)

This is a real Tracker **3.9** screenshot from the supplied lab training material.

It is useful for recognizing the older **Calibrate** workflow, but **do not use its button locations as a Tracker 4.4 guide**.

Tracker 4.4 puts the current workflow in **Camera Calibration**.

---

## 5. Mask unwanted reflections — current manufacturer procedure

Vicon's procedure is to remove or cover unwanted reflective sources where practical **before** using masks.

For Tracker 4.x automatic masking:

1. Change the Workspace to a **Cameras** view.
2. In **System**, select the cameras to calibrate.
3. Go to **Camera Calibration → Masking**.
4. Click **Mask All**.
5. Watch the camera views while Tracker creates the masks.
6. Masked pixels are shown in blue.
7. When the unwanted reflections are covered, click **Stop**.
8. Inspect every camera view before moving on.

For a residual reflection, Vicon's Tracker 4.0 manual-mask procedure is:

1. select the affected camera;
2. open advanced controls under **Camera Calibration → Masking**;
3. click **Manual Mask Paint**;
4. **Alt+drag** a region;
5. press **E** to add it to the mask;
6. press **R** to remove a region from the mask;
7. click **Stop** when finished.

Manufacturer reference: **Vicon Tracker 4.0 — Mask cameras**.

---

## 6. Perform the wand wave — Tracker 4.4 manufacturer sequence

The current Tracker 4.4 guide states:

1. Complete camera masking first.
2. Go to **Camera Calibration → Wand Wave**.
3. Select the calibration object that matches the physical wand. Vicon's default example is **Active Wand v2**.
4. Click **Wave All**.
5. Tracker changes the control to **Stop** and displays **Camera Calibration Active**.
6. Wave the wand through the full useful capture volume, covering both **depth and height**.
7. Keep the wand markers visible to as many cameras as possible.
8. Watch the per-camera **Wand Count**:
   - the status changes toward green as enough data is collected;
   - low-count cameras are moved toward the top of the list.
9. With **Auto Stop** enabled, Tracker stops after enough data has been collected for each camera.
10. Review the per-camera **Image Error** status after calibration.

After this stage the cameras are calibrated **relative to one another**, but the volume origin has not yet been set.

Manufacturer reference: **Tracker 4.4 User Guide, “Perform a wand wave”, pp. 130–132**.

---

## 7. Set the volume origin — Tracker 4.4 manufacturer sequence

After the wand wave:

1. Change the Workspace to **3D View**.
2. Place the calibration device on the floor at the required origin and orient it to the required axes.
3. Go to **Camera Calibration → Volume Setup**.
4. Show the advanced parameters if needed.
5. Under **Set Volume Origin**, choose the correct calibration device.
6. Click **Start Set Origin**.
7. Wait until Tracker has enough data and the control becomes available.
8. Click **Set Origin**.
9. Verify the axes in the 3D View:
   - **X = red**
   - **Y = green**
   - **Z = blue**
10. Physically verify the floor, origin and positive directions before configuring the swarm workspace.

If the capture floor is not sufficiently level, Vicon documents a separate **Set Floor Plane** workflow after the origin is established.

Manufacturer reference: **Tracker 4.4 User Guide, “Set the volume origin”, pp. 134–139**.

---

# Rigid objects

## 8. Actual object-creation UI from the supplied training material

![Actual Tracker object-creation workflow](assets/vicon/tracker39-actual-object-workflow.jpg)

This is a real Tracker **3.9** object-creation screen from the supplied lab training material. Object names were redacted before publication.

It shows the real Tracker workspace used to select a marker constellation and create a rigid object. The current Tracker 4.4 controls are still in the **Tracking** panel, but the layout differs.

---

## 9. Create an object — Tracker 4.4 manufacturer sequence

Vicon Tracker 4.4 states that object tracking is configured in **View → Tracking**.

For best results, an object must be rigid and contain at least **four asymmetric markers**.

To create one:

1. Put the marked chariot inside the calibrated volume.
2. If its markers are not visible:
   - in **View Filters**, enable **Unlabeled Markers**;
   - in **Processing**, enable **Unlabeled Reconstructions**.
3. Select the unassigned marker trajectories:
   - **Ctrl + click** markers individually; or
   - **Alt + drag** a box around a group.
4. Select at least **four** trajectories; Vicon recommends **five or more**.
5. In the **Tracking** panel, type a unique name in the **Object** field.
6. Click **Create**.
7. Exit review/pause mode if necessary to see the new object's current pose.
8. Move the physical chariot and confirm the new Tracker object follows **only that chariot**.

Vicon notes that:

- the initial object origin is the mean point of its markers;
- its initial orientation is aligned to the global coordinate system on the creation frame;
- objects are stored as `.vsk` files.

Manufacturer reference: **Tracker 4.4 User Guide, “Create objects”, pp. 187–190**.

### Add a marker

1. Select the object.
2. Ctrl-select one unassigned marker.
3. Click **Add Marker**.

### Remove a marker

1. Select the marker.
2. Click **Remove Marker**.

Tracker does not allow the operation if it would leave the object with fewer than four markers.

---

# Handoff from Tracker to this repository

## 10. Record the exact object/device mapping

For every chariot, record:

| Physical chariot | Sphero/BLE name | Vicon object/subject | Vicon segment |
|---|---|---|---|
| Robot 1 | local value | local value | local value |
| Robot 2 | local value | local value | local value |
| Robot 3 | local value | local value | local value |

Do not infer mappings from list order.

Then copy the template:

```powershell
Copy-Item config/robot_setup.example.toml config/robot_setup.toml
```

and enter those values locally.

---

## 11. Verify Tracker before commanding robots

Run the Vicon-only monitor:

```bash
python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
```

With **no robot commands active**:

1. move physical robot 1 by hand;
2. confirm only software `robot-1` moves;
3. repeat for robots 2 and 3;
4. move along known world-axis directions;
5. rotate each object;
6. briefly occlude markers and observe the occlusion state.

Only after this passes should the Sphero/Vicon heading calibration be run.

---

## 12. Calibrate Sphero command heading against Vicon displacement

```bash
python examples/04_heading_calibration.py --config config/robot_setup.toml
```

This repository does **not** assume Vicon yaw equals the Sphero command heading. It measures the Vicon displacement created by approximately orthogonal Sphero commands and derives the mapping from the measured displacement.

---

## Manufacturer references used for this page

- **Vicon Tracker 4.4 User Guide**, 2025-09-17, Revision 1  
  https://help.vicon.com/download/attachments/376309877/Vicon%20Tracker%20User%20Guide.pdf
- **Vicon Tracker 4.0 — Mask cameras**  
  https://help.vicon.com/space/Tracker40/14190245
- **Vicon Tracker 4.4 — Add or remove a marker**  
  https://help.vicon.com/space/Tracker44/376309055
- **Vicon DataStream SDK documentation**  
  https://help.vicon.com/space/DSSDK113

See the [full Vicon reproduction workflow](vicon-setup.md) for the end-to-end sequence and stop criteria.
