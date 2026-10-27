# Vicon setup and reproduction workflow

This is the **end-to-end lab procedure** for reproducing the Vicon side of the Sphero swarm system.

The UI instructions on this page use two evidence types:

- **current Vicon manufacturer procedure** for Tracker 4.4; and
- **real Tracker 4.1 application screenshots** in the [Tracker visual guide](vicon-tracker-ui-guide.md), used for visual recognition.

The old supplied lab captures were removed from the public tree because their resolution was too low for dependable button-by-button instruction. Real Tracker 4.1 UI screenshots from DASC Lab's public documentation are used instead, with written procedure checked against Tracker 4.4.

> Site-specific credentials, addresses and network policy are intentionally excluded. Follow the local laboratory SOP for those items.

---

## 1. Start Tracker and verify the camera system

The supplied local checklist records the practical start-up sequence as:

1. start the dedicated workstation and Vicon camera-network equipment;
2. open **Vicon Tracker**;
3. use the **System** panel to confirm the expected camera set is active;
4. use the 3D workspace to confirm reflective markers are being reconstructed.

The local checklist happened to expect eight cameras in that installation. **Eight is not a Vicon requirement**; the correct count is the number installed and expected at the site.

!!! tip "Need the screen layout?"
    Open the [Tracker UI guide](vicon-tracker-ui-guide.md). It now includes full-resolution real Tracker 4.1 screenshots alongside current Tracker 4.4 operating steps.

[![Real Vicon Tracker 4.1 Camera Calibration interface](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/masking_initial.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

*Real Tracker 4.1 UI. Written setup steps below follow Tracker 4.4 terminology.*

Before continuing:

- all expected cameras should be present;
- moving a reflective marker should produce plausible motion in the 3D View;
- there should be no obvious unexplained tracking instability.

---

## 2. Inspect System Health

Tracker 4.4's manufacturer guide defines **System Health Report** as a default pane for evaluating overall system performance.

Use it to inspect:

- **Performance** — latency and dropped frames;
- **Calibration Details** — calibration state and uncalibrated cameras;
- **Centroid Connectivity** — how successfully moving 2D centroids are associated with tracked object markers;
- **Image Error** — pixel difference between measured 2D centroids and reprojected reconstructed 3D points;
- camera temperature and accelerometer information where available.

Tracker 4.4 reports cameras above a **1.0 pixel Image Error diagnostic threshold** in the section header. Treat that as a diagnostic flag, not as a universal project accuracy specification.

Do not recalibrate merely because a calibration is old. Recalibrate when the actual evidence supports it, such as:

- cameras have moved;
- cameras are uncalibrated;
- tracking quality is poor;
- connectivity/image error indicates a problem;
- environmental change has materially affected the system.

Manufacturer reference: **Tracker 4.4 User Guide, pp. 177–187**.

---

## Camera calibration

### 3. Remove or mask unwanted reflections

[![Real Tracker 4.1 masking / Cameras view](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/masking_initial.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

Vicon explicitly recommends **physically removing or covering unwanted reflections first** because masking prevents those camera pixels from contributing to 3D tracking.

Current Tracker 4.x manufacturer sequence:

1. remove unnecessary reflective objects from the capture volume;
2. change the Workspace to **Cameras** view;
3. in **System**, select the cameras to calibrate;
4. go to **Camera Calibration → Masking**;
5. click **Mask All**;
6. Tracker changes the control to **Stop** while automatic masking is active;
7. masked pixels appear blue in the camera views;
8. when unwanted reflections have been covered, click **Stop**;
9. inspect every camera view before proceeding.

If automatic masking misses a reflection, Vicon's Tracker 4.0 manual-mask procedure is:

1. select one camera;
2. expose the advanced Masking controls;
3. click **Manual Mask Paint**;
4. **Alt+drag** a region;
5. press **E** to add it to the mask;
6. press **R** to remove a selected region;
7. click **Stop** to apply the mask.

Manufacturer reference:  
https://help.vicon.com/space/Tracker40/14190245

---

### 4. Perform the wand wave

[![Real Tracker 4.1 wand calibration in progress](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/wand_in_progress.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

[![Real Tracker 4.1 calibration completed](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/wand_finished.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

The current Tracker 4.4 manufacturer sequence is:

1. finish masking first;
2. go to **Camera Calibration → Wand Wave**;
3. select the calibration object that matches the physical wand;
4. click **Wave All**;
5. Tracker changes the control to **Stop** and displays **Camera Calibration Active**;
6. wave the wand through the full useful volume, covering both **depth and height**;
7. keep the wand markers visible to as many cameras as practical;
8. watch **Wand Count** for each camera;
9. concentrate on cameras with the lowest count;
10. with **Auto Stop** enabled, allow Tracker to stop when sufficient data has been collected;
11. inspect the camera **Image Error** status after the wand wave.

After the wand wave, the cameras are calibrated **relative to each other**, but the volume origin has not yet been set.

Manufacturer reference: **Tracker 4.4 User Guide, pp. 130–132**.

---

### 5. Set the volume origin

[![Real Tracker 4.1 Volume Setup view](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/origin_pan_zoom.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

Tracker 4.4 manufacturer sequence:

1. change the Workspace to **3D View**;
2. place the calibration device on the floor where the origin should be;
3. orient it in the desired world-axis direction;
4. go to **Camera Calibration → Volume Setup**;
5. show advanced parameters if required;
6. under **Set Volume Origin**, choose the appropriate calibration device;
7. click **Start Set Origin**;
8. wait until Tracker has collected enough information;
9. click **Set Origin**;
10. verify the displayed axes:
    - **X = red**
    - **Y = green**
    - **Z = blue**

Physically verify that the axes and origin make sense for the robot workspace before entering any software workspace bounds.

If the physical floor is not adequately represented after setting the origin, Tracker provides a separate **Set Floor Plane** workflow. In Tracker 4.4, the Volume Setup controls include **Start Set Floor Plane** and a **Height offset (mm)**; the manufacturer default height offset is 7 mm.

Manufacturer reference: **Tracker 4.4 User Guide, pp. 134–147**.

---

### 6. Save and validate the calibration

Save the calibration using the lab's normal naming/version convention.

Before accepting it for robot control:

1. move a marker through the centre of the intended workspace;
2. repeat near the planned workspace edges;
3. look for jumps, dropouts or implausible coordinates;
4. verify the physical positive-axis directions;
5. re-check System Health.

Do not widen the software workspace into a region where tracking is poor.

---

## Rigid-body creation

### 7. Build a distinct marker constellation

Vicon Tracker 4.4 states that, for best results, an object should be rigid and contain **at least four asymmetric markers**.

For these three similar chariots:

- make each constellation physically distinct;
- avoid symmetric layouts;
- keep markers rigidly attached;
- space markers so that several remain visible from typical camera directions;
- use five or more markers where practical, because Vicon recommends five or more trajectories during object creation.

---

### 8. Create the object in Tracker

[![Real Tracker 4.1 marker selection](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/object_select.png)](https://dasc-lab.github.io/robot-framework/flylab/object.html)

[![Real Tracker 4.1 Tracking panel object creation](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/object_create.png)](https://dasc-lab.github.io/robot-framework/flylab/object.html)

The current Tracker 4.4 manufacturer sequence is:

1. open **View → Tracking**;
2. place the marked chariot in the calibrated volume;
3. if markers are not visible:
   - enable **Unlabeled Markers** in **View Filters**;
   - enable **Unlabeled Reconstructions** in **Processing**;
4. select unassigned marker trajectories:
   - **Ctrl + click** individual markers; or
   - **Alt + drag** a selection box;
5. select at least four trajectories; Vicon recommends **five or more**;
6. in the **Tracking** panel, type a unique name in the **Object** field;
7. click **Create**;
8. leave review/pause mode if necessary to see the current pose;
9. move that physical chariot by hand and confirm only the intended object follows it.

Vicon notes that the new object's initial origin is the mean point of its markers and its initial orientation is aligned with the global coordinate system on the creation frame.

Manufacturer reference: **Tracker 4.4 User Guide, pp. 187–190**.

#### Add a marker

1. select the object;
2. hold **Ctrl** and select one unassigned marker;
3. click **Add Marker**.

#### Remove a marker

1. select the marker;
2. click **Remove Marker**.

Tracker prevents removal if the object would be left with fewer than four markers.

Manufacturer reference:  
https://help.vicon.com/space/Tracker44/376309055

---

### 9. Verify object identity before software integration

For each chariot:

1. stop all commanded robot motion;
2. move one physical chariot by hand;
3. confirm exactly one Tracker object follows it;
4. repeat for every chariot;
5. record the exact object/subject name.

Do not infer identity from list order.

---

## DataStream and software handoff

### 10. Install the Vicon DataStream SDK

The repository uses Vicon **DataStream SDK** via the Python module `vicon_dssdk`.

Vicon's current DataStream SDK release is **1.13** and supports Tracker 4.x. Vicon's 1.13 release notes also document a Python-install issue on some recent Python 3 installations: the supplied batch install may need to be run as administrator, or the package can be copied to a user-writable folder before installation.

Use the dedicated [DataStream SDK setup page](vicon-datastream.md).

---

### 11. Create the local configuration

Copy:

```powershell
Copy-Item config/robot_setup.example.toml config/robot_setup.toml
```

Then set the local values:

```toml
[vicon]
server = "TRACKER_HOST:801"
floor_plane = "XY"

[[robots]]
label = "robot-1"
sphero_name = "YOUR_DEVICE_NAME"
vicon_subject = "YOUR_TRACKER_OBJECT"
vicon_segment = "YOUR_TRACKER_SEGMENT"
```

The public template intentionally contains no real lab addresses or device identifiers.

Vicon's Python quick-start documentation uses `localhost:801` in its DataStream connection example; this repository follows the same host-and-port convention.

---

### 12. Verify DataStream with **no robot commands**

```mermaid
flowchart LR
    MON["Python Vicon-only monitor"] --> SDK["vicon_dssdk"]
    SDK --> TRACKER["Tracker DataStream server"]
    TRACKER --> CONN["View -> Connections -> Data Stream"]
    TRACKER --> POSE["live subject / segment pose"]
```

1. In Tracker, open **View → Connections**.
2. Run:

```bash
python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
```

3. Confirm a DataStream client appears.
4. Move robot 1 by hand; only software `robot-1` should move.
5. Repeat for robots 2 and 3.
6. Move along known world-axis directions.
7. rotate the bodies and inspect yaw;
8. briefly occlude a constellation and observe the occlusion flag.

Do not enable closed-loop motion if identity, axes or tracking quality are ambiguous.

---

### 13. Verify the Sphero devices

Run the staged Sphero smoke tests:

```bash
python examples/01_single_sphero_smoke_test.py --config config/robot_setup.toml
python examples/02_multi_sphero_smoke_test.py --config config/robot_setup.toml
```

Keep speeds low and maintain a direct stop path.

---

### 14. Calibrate Sphero heading against measured Vicon displacement

Run:

```bash
python examples/04_heading_calibration.py --config config/robot_setup.toml
```

The project deliberately does **not** assume that Vicon yaw equals the Sphero command-heading frame.

The calibration measures Vicon displacement produced by approximately orthogonal Sphero commands and derives the command/world mapping from those measured vectors.

---

### 15. Validate one robot before the swarm

```bash
python reference_controllers/single_chariot_vicon_circle.py
```

Check that:

- Vicon tracking remains stable;
- commanded motion is physically sensible;
- the robot stays inside conservative bounds;
- interruption/stop behaviour is safe.

---

### 16. Dry-run, then run the physical swarm

Software-only first:

```bash
python reference_controllers/three_chariot_square_swarm.py --dry-run --timeout 8 --no-digital-twin
```

Then one conservative physical lap:

```bash
python reference_controllers/three_chariot_square_swarm.py --laps 1 --max-speed 160
```

The hardware reference controller performs a fresh heading calibration by default.

---

## Evidence and source policy

The procedure above was built from:

1. **the supplied local Vicon checklist and training material** for site workflow context;
2. **Vicon Tracker 4.4 User Guide** for current calibration, System Health and object-creation procedure;
3. **Vicon Tracker 4.0 masking documentation** where the lab software/version-specific procedure is relevant;
4. **Vicon DataStream SDK documentation** for Python/DataStream setup;
5. the repository's own source code for the project-specific Python commands and data path;
6. **DASC Lab's public Tracker 4.1 setup documentation** for high-resolution visual references, pinned to source commit `c3241aa50284640d379de1acb5f87774c5d415a2`.

See [Vicon procedure sources](vicon-procedure-sources.md) for the exact provenance table.
