# Vicon operator quick checklist

!!! info "Bench-side use"
    Use this page after reading the full [Vicon setup workflow](vicon-setup.md). The screenshots below are real Tracker 4.1 captures for visual recognition; the written procedure uses current Tracker 4.4 terminology.

## A. Start and verify Tracker

- [ ] Start the local Vicon workstation/camera network using the lab SOP.
- [ ] Open **Vicon Tracker**.
- [ ] Confirm the expected cameras are present in **System**.
- [ ] Move a reflective marker and confirm plausible reconstruction in **3D View**.
- [ ] Inspect **System Health Report** for obvious problems.

## B. If calibration is required

### Remove/mask reflections

[![Tracker 4.1 Mask All and active masking state](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/masking_mask_all.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

*Use this reference for the **Mask All → Stop** masking action. The [visual guide](vicon-tracker-ui-guide.md) shows the complete screenshot sequence.*

- [ ] Remove or cover reflective sources where practical.
- [ ] Workspace → **Cameras**.
- [ ] Select the cameras in **System**.
- [ ] **Camera Calibration → Masking → Mask All**.
- [ ] Wait for unwanted light pixels to become masked/blue.
- [ ] Click **Stop**.
- [ ] Inspect every camera view.

### Wand wave

[![Tracker 4.1 Wand Wave in progress](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/wand_in_progress.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

*Real full-window Tracker 4.1 calibration in progress. The Wand Wave controls are visible at left; Wand Count and Image Error are shown below them.*

[![Tracker 4.1 calibration completed](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/wand_finished.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

*Real full-window Tracker 4.1 post-calibration view with completed counts and image-error results.*

- [ ] **Camera Calibration → Wand Wave**.
- [ ] Select the correct physical calibration object.
- [ ] Click **Wave All**.
- [ ] Cover depth and height across the actual robot volume.
- [ ] Watch **Wand Count** and concentrate on low-count cameras.
- [ ] Let **Auto Stop** finish, or stop only after sufficient coverage.
- [ ] Review **Image Error** status.

### Origin

[![Tracker 4.1 Volume Setup / Start Set Origin](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/origin_pan_zoom.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

*Real Tracker 4.1 **Start Set Origin** state. This is the origin action, not the completed-origin result.*

- [ ] Workspace → **3D View**.
- [ ] Place/orient the calibration device at the intended origin.
- [ ] **Camera Calibration → Volume Setup**.
- [ ] Under **Set Volume Origin**, select the correct device.
- [ ] Click **Start Set Origin**.
- [ ] When enabled, click **Set Origin**.
- [ ] Verify **X red / Y green / Z blue** physically.
- [ ] If required, use the separate **Set Floor Plane** workflow.

## C. Create each rigid object

[![Tracker 4.1 marker selection in 3D View](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/object_select.png)](https://dasc-lab.github.io/robot-framework/flylab/object.html)

*Real Tracker 4.1 3D View with an asymmetric marker cluster selected.*

[![Tracker 4.1 Tracking panel object creation](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/object_create.png)](https://dasc-lab.github.io/robot-framework/flylab/object.html)

*Real Tracker 4.1 Tracking panel showing the object-name field and **Create** control.*

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

~~~mermaid
flowchart LR
    A["Tracker"] --> B["DataStream"]
    B --> C["vicon_dssdk"]
    C --> D["pose monitor"]
~~~

*Architecture diagram, not a Tracker UI screenshot. Verify the actual connection in **View → Connections → Data Stream**.*

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
- [ ] calibrate each intended robot sequentially;
- [ ] verify both displacement legs are sensible for each robot;
- [ ] confirm `artifacts/heading_calibration.json` was written.

## I. One robot before three

```bash
python reference_controllers/single_chariot_vicon_circle.py --config config/robot_setup.toml
```

## J. Dry-run, then physical swarm

```bash
python reference_controllers/three_chariot_square_swarm.py --config config/robot_setup.toml --dry-run --timeout 8 --no-digital-twin
python reference_controllers/three_chariot_square_swarm.py --config config/robot_setup.toml --laps 1 --max-speed 140 --calibration-speed 180
```

Before live motion:

- [ ] understand that `--max-speed` is the mission/stiction-pulse cap;
- [ ] choose `--calibration-speed` deliberately for the available clearance;
- [ ] all three objects are visible;
- [ ] mappings are confirmed;
- [ ] workspace is clear;
- [ ] boundaries are conservative;
- [ ] an operator can stop the run immediately.

## Debug in this order

<div class="sv-codeflow">
<strong>camera health → calibration → rigid-object identity → DataStream → Sphero identity → heading calibration → single robot → swarm</strong>
</div>

For a first-time setup, follow the [end-to-end tutorial](end-to-end-tutorial.md) rather than this condensed checklist.

For exact screenshot states and version notes, see the [Tracker visual guide](vicon-tracker-ui-guide.md) and [Vicon procedure sources](vicon-procedure-sources.md).
