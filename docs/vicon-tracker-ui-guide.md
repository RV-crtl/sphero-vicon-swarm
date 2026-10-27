# Vicon Tracker 4.0 — actual lab UI guide

This page uses **real screenshots of the Vicon Tracker interface from the lab material supplied with this project**. The screenshots are not mock-ups or reconstructed interfaces. Private/local connection values have been redacted; the Tracker controls and layout are otherwise unchanged.

> **Version scope**
>
> The supplied RAS lab checklist identifies the workstation software as **Vicon Tracker 4.0**. Menu positions can change between Tracker releases. If the installed version is not 4.0, use the Vicon manufacturer documentation for that exact release rather than assuming every control is in the same place.

## Full Tracker interface

![Actual Vicon Tracker lab interface](assets/vicon/tracker-ui-actual-sanitized.jpg)

*Actual Vicon Tracker lab screenshot. Only private/local connection values were redacted.*

The screenshot is useful for orientation before following the procedure:

- the **3D view** is where reconstructed markers and tracked objects are observed;
- the left-side panels are used for setup/configuration;
- the right-side **System Health** information is used to assess the state of the capture system;
- a tracked rigid body appears in the 3D view once an object has been created and recognised.

## Left-side controls

![Actual Tracker left-side controls](assets/vicon/tracker-ui-actual-left-panel.jpg)

*Crop from the same real Tracker screenshot.*

The supplied lab checklist gives these Tracker 4.0 operator actions:

1. Open **Vicon Tracker 4.0**.
2. Open **System** and confirm the expected cameras are active before continuing.
3. To work with tracked objects, use **View → Tracking**.
4. The Tracker 4.0 lab procedure uses the **Tracking** tab's **Setup** area to name and create an object.
5. Save the configuration after the object definitions are complete.

These are **lab-checklist steps**, not invented replacements for the Vicon manual. For calibration and version-specific UI details, use the manufacturer references at the end of this page.

## 3D tracking view

![Actual Tracker 3D view](assets/vicon/tracker-ui-actual-3d-view.jpg)

*Actual 3D tracking area cropped from the supplied lab screenshot.*

In the supplied lab procedure:

- unlabeled reflective-marker reconstructions are selected in the 3D view;
- **Ctrl + left mouse button** is used to select the markers that belong to one rigid body;
- the marker pattern must be rigid, asymmetric, visually distinguishable from the other robots and sufficiently well spaced;
- after object creation, the tracked constellation is shown in the 3D view.

### What to verify here

Before allowing the controller to command a robot:

1. Move **only one chariot** by hand.
2. Confirm that only its intended Tracker object follows the motion.
3. Repeat for every chariot.
4. Rotate each chariot and confirm the rigid body remains continuously tracked.
5. Move the robot toward the intended operating-area edges and check that tracking remains stable.
6. Briefly create a controlled occlusion and confirm the software can observe the resulting tracking/occlusion state.

If object identity is ambiguous, stop and correct the rigid-body definitions before running the swarm.

## System Health view

![Actual Tracker System Health view](assets/vicon/tracker-ui-actual-system-health.jpg)

*Actual System Health area cropped from the supplied lab screenshot.*

Use the manufacturer documentation for the meaning and acceptance criteria of health/calibration indicators. Do not invent local thresholds from a screenshot.

For this project the practical rule is:

> If Tracker reports an unhealthy camera/calibration state, or if reconstructed motion is visibly unstable, **do not proceed to closed-loop robot control**.

## Actual object/tracking view

![Actual Tracker object/tracking view](assets/vicon/tracker-ui-actual-object-view.jpg)

*Real Vicon Tracker object/tracking screenshot from the supplied lab material. It is included here so a future user can compare the live workstation to an actual Tracker interface rather than a redrawn mock-up.*

## Object creation — Tracker 4.0 lab procedure

The unfinished RAS checklist supplied with the project records the following physical workflow:

1. Put a rigid, unique marker constellation on the object.
2. Pause capture with **Spacebar** when required by the lab workflow.
3. Open **View → Tracking**.
4. Place the object in the visible capture volume.
5. In the 3D view, select the object's reconstructed markers using **Ctrl + left-click**.
6. In the **Tracking** tab under **Setup**, give the object a name and choose **Create**.
7. Confirm the object appears in the object list.
8. If necessary, use **Add Marker** or **Remove Marker** in the Tracking setup controls to correct the object definition.
9. Move the object by hand and verify that the tracked constellation follows the intended physical body.
10. Save the configuration.

The lab checklist also records that Tracker can reject an invalid marker selection with a message such as **“Cannot create an object at this time.”** If that occurs, re-check that the selected points belong to one rigid body and form a suitable constellation.

## Manufacturer procedure takes precedence

The steps above preserve the supplied RAS Tracker 4.0 procedure. For camera masking, camera calibration, origin setup, health indicators and any UI differences, use Vicon's documentation for the installed Tracker release.

### Official Vicon references

- **Vicon Tracker 4.0 documentation:** https://help.vicon.com/space/Tracker40
- **Tracker 4.0 reflection/camera masking guidance:** https://help.vicon.com/space/Tracker40/14190245
- **Tracker 4.0 calibration/origin guidance:** https://help.vicon.com/space/Tracker40/14189152
- **Vicon Tracker user guides/downloads:** https://help.vicon.com/

## Continue the reproduction workflow

After Tracker is healthy and the rigid bodies have been created:

1. [Configure the DataStream connection](vicon-datastream.md).
2. [Map Vicon objects to Sphero devices](configuration.md).
3. Run the Vicon-only pose monitor.
4. Perform heading/displacement calibration.
5. Validate one robot before running the swarm.

See the [full Vicon reproduction procedure](vicon-setup.md).
