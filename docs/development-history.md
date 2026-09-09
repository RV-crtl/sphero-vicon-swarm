# Development history

The project evolved incrementally rather than beginning with a large multi-agent controller.

## Stage 1 — one robot

Basic BLE connection, heading and speed commands established the minimum controllable unit.

## Stage 2 — multiple robots

Three independently addressed robots were connected and controlled, exposing practical issues such as connection ordering and robot-specific behaviour.

## Stage 3 — Vicon only

The motion-capture stream was separated from motion control. This verified rigid-body names, coordinate axes, units and occlusion behaviour before closing the loop.

## Stage 4 — Sphero/Vicon integration

Measured displacement under known Sphero heading commands established the transformation between the command frame and the Vicon world frame.

## Stage 5 — closed-loop single-chariot motion

The controller used Vicon position as truth for trajectory acquisition and path correction.

## Stage 6 — controller experiments

P, PD and PID variants were tested. Their behaviour highlighted non-repeatable plant characteristics and different breakaway thresholds between chariots.

## Stage 7 — three-chariot trajectory control

The system was extended to a compact formation following a square reference with per-robot calibration, measured-state correction, boundary handling, collision safeguards, logging and a live digital twin.

The repository keeps this progression visible because it provides useful debugging checkpoints for anyone reproducing the setup.
