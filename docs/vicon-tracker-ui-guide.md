# Vicon Tracker visual guide — real UI screenshot atlas

Use this page when you are standing at the Tracker workstation and need to recognise **what screen/state you should be looking at**.

For the full first-time procedure, use the [end-to-end tutorial](end-to-end-tutorial.md). For a returning operator, use the [quick checklist](vicon-operator-checklist.md).

## Version rule

| Source | Version | Purpose |
|---|---:|---|
| Written procedure | Tracker 4.4 | current control names and workflow |
| Screenshots below | Tracker 4.1 | real Tracker 4 interface recognition |
| Vicon Help links | Tracker 4.4 / SDK 1.13 | manufacturer authority |

!!! warning "Do not treat screenshots as pixel-identical instructions"
    Tracker 4.x preserves the same broad panel/workspace model, but exact placement can change between point releases and customised layouts. Use the **control names** in the written procedure if your Tracker 4.4 workstation is arranged differently.

The screenshots are externally referenced from DASC Lab's public Tracker 4.1 setup documentation, pinned to source commit **c3241aa50284640d379de1acb5f87774c5d415a2**. They are not synthetic UI mockups.

---

# Camera Calibration

## 1. Before automatic masking

This is the **Camera Calibration workspace before Mask All is started**.

[![Tracker 4.1 Camera Calibration before masking](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/masking_initial.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

### What is actually visible

- left panel: **Masking**, **Wand Wave**, **Volume Setup**, **Calibration Healing**;
- Masking action: **Mask All**;
- Wand action: **Wave All**;
- origin action: **Start Set Origin**;
- main workspace: individual camera views.

### Use this screenshot when

You are trying to answer: **“Am I in the correct Camera Calibration workspace?”**

It is not a screenshot of completed masking.

---

## 2. Masking action / active state

[![Tracker 4.1 masking Mask All and Stop states](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/masking_mask_all.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

This image is specifically useful for **Masking**. It highlights **Mask All** and includes the active-state control becoming **Stop**.

### What to do

1. remove/cover reflective clutter physically;
2. select the cameras;
3. click **Mask All**;
4. watch mask regions form;
5. click **Stop**;
6. inspect every camera.

### What “good” looks like

The unwanted reflections are masked without unnecessarily masking useful measurement pixels.

---

## 3. 3-D view with no marker selection

[![Tracker 4.1 3-D view with cameras and no marker selection](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/masking_no_markers.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

This screenshot is a **3-D View orientation reference**, not the Cameras masking view.

It shows:

- the floor grid;
- camera/frustum geometry;
- the 3-D workspace;
- no marker cluster selected.

Use it to recognise the 3-D workspace before object/origin operations.

---

# Wand calibration

## 4. Wand Wave advanced settings

[![Tracker 4.1 Wand Wave settings close-up](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/wand_settings.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

This is intentionally a **close-up**, not a whole-window screenshot.

It shows:

- calibration object selection;
- **Auto Stop**;
- Auto Stop Minimum Frames;
- wand ratio/straightness tolerances;
- **Wave All**.

### Important

The wand/model shown belongs to the source laboratory. Select the calibration object that matches **your physical Vicon wand**.

---

## 5. Wand collection has just started

[![Tracker 4.1 Wand Wave at zero/initial collection](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/wand_initial.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

This full-window screenshot shows:

- **Camera Calibration Active**;
- Wand Wave running;
- per-camera table present;
- early/zero counts.

Use this image to recognise the **start of collection**, not the finished result.

---

## 6. Wand collection in progress

[![Tracker 4.1 Wand Wave in progress](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/wand_in_progress.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

This screenshot shows the state a new operator should expect while actively covering the volume:

- blue wand traces in camera panes;
- per-camera **Wand Count** values;
- calibration progress;
- different cameras accumulating different amounts of data.

### Operator action

Spend more time in volume regions associated with cameras that have lower counts. Cover the actual robot operating volume, not only the centre.

---

## 7. Wand calibration completed

[![Tracker 4.1 completed wand calibration results](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/wand_finished.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

This image shows a **completed calibration result**:

- per-camera counts;
- green result cells;
- **Image Error** values;
- no active wand trace collection.

Use this screenshot when checking: **“Did the wand stage actually finish?”**

For current Tracker 4.4 acceptance/diagnostic interpretation, use Tracker's System Health and current manufacturer documentation rather than copying another lab's numerical values.

---

# Volume origin

## 8. 3-D view before setting the origin

[![Tracker 4.1 initial Volume Setup 3-D view](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/origin_initial.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

This image shows:

- 3-D View selected;
- floor grid;
- camera/frustum geometry;
- **Start Set Origin** available;
- completed wand-calibration table still visible on the left.

This is the right visual reference for the state **before/around beginning origin placement**.

---

## 9. Start Set Origin state

[![Tracker 4.1 Start Set Origin highlighted](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/origin_pan_zoom.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

This screenshot specifically shows **Volume Setup / Start Set Origin** highlighted.

It is useful when a user asks: **“Which control starts the origin operation?”**

Place/orient the physical origin object first, then start the operation.

---

## 10. World geometry after setting the origin

[![Tracker 4.1 geometry after origin setup](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/origin_final.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

This image shows the camera geometry converging on the defined capture volume/floor region after origin setup.

### Physically verify

- X axis direction;
- Y axis direction;
- Z vertical;
- floor plane;
- a marker moved in known +X/+Y directions produces the expected coordinate sign.

Do not accept the origin solely because the screenshot “looks right”.

---

# Rigid-object creation

## 11. Tracking panel before selecting new markers

[![Tracker 4.1 Tracking panel before marker selection](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/object_initial.png)](https://dasc-lab.github.io/robot-framework/flylab/object.html)

This screenshot shows the **Tracking** workspace before creating the new object.

Visible elements include:

- object-name field;
- **Create** control;
- existing object list;
- 3-D View;
- zero selected markers.

Use it to confirm you have opened the correct panel.

---

## 12. Marker cluster selected

[![Tracker 4.1 selected five-marker rigid cluster](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/object_select.png)](https://dasc-lab.github.io/robot-framework/flylab/object.html)

This screenshot shows **five markers selected** in the 3-D View.

The orange/selection region is around the candidate marker cluster.

### Before clicking Create

Verify the selected markers all belong to the **same physical chariot**.

A mixed cluster can create a rigid object that appears valid for one frame but fails as soon as the robots move independently.

---

## 13. Name and create the object

[![Tracker 4.1 object name and Create control](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/object_create.png)](https://dasc-lab.github.io/robot-framework/flylab/object.html)

This screenshot specifically shows:

- the object-name field populated;
- **Create** highlighted;
- the same marker cluster ready for object creation.

After creation:

1. move the physical chariot by hand;
2. confirm only the new object follows;
3. record exact subject/segment names;
4. update the private TOML.

---

# DataStream / Connections

The repository communicates through **Vicon DataStream SDK**, not through Tracker's UDP Object Stream.

The actual connection path is:

~~~mermaid
flowchart LR
    A["Tracker tracked object"] --> B["DataStream server"]
    B --> C["vicon_dssdk Client"]
    C --> D["ViconTracker adapter"]
    D --> E["robot label -> Pose2D"]
~~~

For the actual current **View → Connections** panel, use Vicon's current Tracker documentation. The repository deliberately does not substitute a fake UI reconstruction where no suitable reusable real screenshot is available.

Run the real client and verify the connection instead:

~~~powershell
python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
~~~

Then check the Tracker Connections/Data Stream panel and move each physical object by hand.

---

# Visual-source provenance

These Tracker 4.1 UI captures come from DASC Lab's public robot-framework documentation at source commit:

~~~text
c3241aa50284640d379de1acb5f87774c5d415a2
~~~

Source pages:

- [DASC Lab calibration documentation](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)
- [DASC Lab object-creation documentation](https://dasc-lab.github.io/robot-framework/flylab/object.html)

Current procedure authority remains Vicon Tracker 4.4 documentation.

## Manufacturer references

- Tracker 4.4 User Guide: https://help.vicon.com/download/attachments/376309877/Vicon%20Tracker%20User%20Guide.pdf
- Tracker 4.4 Get to know Tracker: https://help.vicon.com/space/Tracker44/376307984
- Tracker 4.0 Mask cameras: https://help.vicon.com/space/Tracker40/14190245
- Tracker 4.4 Add/remove object marker: https://help.vicon.com/space/Tracker44/376309055
- DataStream SDK 1.13: https://help.vicon.com/space/DSSDK113

## Where to go next

- New user: [end-to-end tutorial](end-to-end-tutorial.md)
- Detailed Vicon procedure: [Vicon setup workflow](vicon-setup.md)
- Returning operator: [quick checklist](vicon-operator-checklist.md)
