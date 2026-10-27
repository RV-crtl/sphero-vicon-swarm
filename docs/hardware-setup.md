# Hardware setup

This page covers the **physical preparation** that should be complete before any closed-loop robot command is allowed.

For the full software + Vicon + hardware sequence, use the [end-to-end tutorial](end-to-end-tutorial.md).

## Minimum equipment

- compatible Sphero robot(s);
- rigid wheeled carrier/chariot if reproducing loaded behaviour;
- Bluetooth-capable control computer;
- Vicon Tracker system;
- rigid reflective-marker constellation on each chariot;
- calibration wand/origin object appropriate to the installed Vicon system;
- clear, measured operating area.

## Chariot mechanical inspection

Before every first run after a hardware change:

- check every wheel turns freely;
- check no wheel, body panel or cable rubs the floor;
- check the Sphero is seated consistently;
- check the Sphero cannot rotate unexpectedly relative to the carrier;
- check marker posts are rigid;
- check the marker constellation has not bent or twisted;
- check batteries are sufficiently charged;
- remove debris from the floor.

A controller cannot compensate reliably for a wheel that is physically jammed or a marker cluster that moves relative to the chassis.

## Marker constellation

A useful rigid object should be:

- rigid;
- asymmetric;
- visible from multiple camera directions;
- physically distinguishable from the other chariots.

Vicon recommends at least four marker trajectories for object creation; five or more is preferable when practical.

Avoid a perfectly symmetric marker layout. Symmetry makes identity/orientation ambiguity more likely.

## Vicon segment axis versus chassis axis

The Vicon segment orientation does not necessarily point along the physical long axis of the chariot.

The configuration field:

```toml
body_yaw_offset_deg = 0.0
```

exists for **physical footprint geometry/digital-twin orientation**.

Do not use it to fix steering. Steering-frame alignment is learned from measured displacement in the heading-calibration stage.

## Measure the physical footprint

Record the maximum physical dimensions, including anything that can collide.

```toml
body_length_mm = 200.0
body_width_mm = 140.0
```

If robots differ, record each robot's own dimensions. The advanced three-chariot reference controller uses the largest configured footprint as a conservative common collision box.

## Define the usable operating area

After the Vicon world origin is set, determine the region where:

- tracking is stable;
- cameras have useful coverage;
- robots cannot hit walls/furniture/tripods;
- the operator can safely observe and stop the test.

Then choose bounds **inside** that region.

Do not define software bounds by measuring the room alone. They are control bounds, so tracking quality and physical hazards both matter.

## Robot identity table

Before motion, make a table like this locally:

| Software label | Physical chariot | BLE/Sphero name | Vicon subject | Vicon segment |
|---|---|---|---|---|
| robot-1 | Chariot A | local value | local value | local value |
| robot-2 | Chariot B | local value | local value | local value |
| robot-3 | Chariot C | local value | local value | local value |

Prove the mapping rather than trusting labels:

1. run the Vicon-only pose monitor;
2. move one chariot by hand;
3. confirm one software label changes;
4. repeat;
5. run the Sphero smoke tests and confirm the intended device responds.

## Before any commanded motion

- [ ] workspace clear;
- [ ] Vicon objects visible;
- [ ] local TOML validated;
- [ ] robot/object identity physically verified;
- [ ] Ctrl+C terminal focused;
- [ ] operator can reach the robots;
- [ ] first movement speed chosen deliberately;
- [ ] calibration travel clearance available.

## After changing hardware

Re-run the relevant validation if you change:

- Sphero robot;
- carrier/chariot;
- wheel alignment;
- marker geometry;
- marker mounting;
- floor surface;
- Vicon object definition;
- world origin;
- battery condition enough to materially change breakaway behaviour.

Do not reuse historical calibration/learning blindly after a physical change.
