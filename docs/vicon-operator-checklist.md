# Vicon Tracker 4.0 — bench-side reproduction checklist

This is a **condensed operator checklist**. It deliberately does not replace Vicon's manufacturer documentation.

For screenshots and explanations, use:

- [Actual Tracker UI guide](vicon-tracker-ui-guide.md)
- [Full Vicon reproduction procedure](vicon-setup.md)
- [DataStream SDK setup](vicon-datastream.md)

## Before calibration

- [ ] Open the dedicated Vicon workstation using the local lab procedure.
- [ ] Confirm Vicon camera-network hardware is powered.
- [ ] Open **Vicon Tracker 4.0**.
- [ ] Open **System** and confirm every expected camera is active.
- [ ] Move a reflector through the working volume and confirm marker reconstruction.
- [ ] Stop if camera/system health is not credible.

## Calibration

- [ ] Follow Vicon's Tracker 4.0 masking instructions: https://help.vicon.com/space/Tracker40/14190245
- [ ] Follow Vicon's Tracker 4.0 calibration/origin instructions: https://help.vicon.com/space/Tracker40/14189152
- [ ] Cover the **actual chariot workspace**, not only the centre of the volume.
- [ ] Confirm the world origin and horizontal plane after calibration.
- [ ] Save the validated Tracker setup.

## Create each chariot object

Using the supplied RAS Tracker 4.0 lab procedure:

- [ ] use a rigid, asymmetric, unique marker constellation with at least four markers;
- [ ] place one chariot in the visible volume;
- [ ] open **View → Tracking**;
- [ ] select its markers using **Ctrl + left-click**;
- [ ] in **Tracking → Setup**, enter the object name and choose **Create**;
- [ ] correct the definition with **Add Marker** / **Remove Marker** if required;
- [ ] move the chariot by hand and confirm the intended object follows it;
- [ ] save the setup.

## Verify identity before robot motion

- [ ] move Robot 1 only → only Robot 1 Vicon object changes;
- [ ] repeat for Robot 2;
- [ ] repeat for Robot 3;
- [ ] record exact Sphero device ↔ Vicon object/segment mappings.

## Configure the repository

```powershell
Copy-Item config/robot_setup.example.toml config/robot_setup.toml
```

or:

```bash
cp config/robot_setup.example.toml config/robot_setup.toml
```

Set the local:

- [ ] DataStream server;
- [ ] horizontal `floor_plane`;
- [ ] Sphero device names;
- [ ] Vicon subject/object names;
- [ ] Vicon segment names;
- [ ] conservative workspace limits.

## Vicon only

```bash
python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
```

- [ ] move each robot by hand and verify the correct software pose;
- [ ] check axis signs;
- [ ] check yaw response;
- [ ] check occlusion reporting;
- [ ] do not continue if mappings are ambiguous.

## Sphero only

```bash
python examples/01_single_sphero_smoke_test.py --config config/robot_setup.toml
python examples/02_multi_sphero_smoke_test.py --config config/robot_setup.toml
```

- [ ] verify each software label commands the intended physical Sphero.

## Heading calibration

```bash
python examples/04_heading_calibration.py --config config/robot_setup.toml
```

- [ ] clear space;
- [ ] verify the correct Vicon object is tracking;
- [ ] confirm both calibration displacements are sensible.

## One robot

```bash
python reference_controllers/single_chariot_vicon_circle.py
```

- [ ] verify world direction;
- [ ] verify stopping;
- [ ] verify conservative workspace containment.

## Three robots — software first

```bash
python reference_controllers/three_chariot_square_swarm.py --dry-run --timeout 8 --no-digital-twin
```

## Three robots — physical

```bash
python reference_controllers/three_chariot_square_swarm.py --laps 1 --max-speed 160
```

- [ ] all three Vicon objects visible;
- [ ] all mappings verified;
- [ ] workspace clear;
- [ ] stop path available;
- [ ] fresh calibration completes.

## Debugging order

If something fails, debug in this order:

**camera/system health → Vicon calibration → rigid-body identity → DataStream pose → Sphero identity → heading calibration → one robot → swarm**

That order prevents software/controller tuning from hiding a basic tracking or identity problem.
