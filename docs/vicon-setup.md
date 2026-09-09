# Vicon setup

Vicon is used as the external position reference.

## Recommended verification

- Rigid-body translation should be stable when stationary.
- Units should be millimetres.
- Confirm whether the floor plane is `XY` or `XZ`.
- Move one physical chariot by hand and confirm that only its expected subject moves.
- Rotate it and confirm the yaw convention before using yaw for footprint visualisation.
- Check occlusion behaviour at the edge of the operating area.

Run `examples/03_vicon_pose_monitor.py` before any closed-loop motion.

The control architecture does not require the Vicon yaw angle to define Sphero steering; displacement calibration is used for that transformation. This reduces dependence on how the rigid-body axes were created.
