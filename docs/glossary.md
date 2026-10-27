# Glossary

Terms used throughout the repository.

## BLE

Bluetooth Low Energy. The transport used by the public Sphero backend.

## body yaw offset

A configured rotation used to draw/evaluate the physical chassis footprint relative to the Vicon segment yaw axis. It is **not** the Sphero steering calibration.

## breakaway command

A short stronger command used to overcome static friction when Vicon confirms that a loaded chariot is not moving despite a meaningful motion request.

## calibration speed

The advanced controller's startup displacement-calibration command set by `--calibration-speed`. It is separate from the mission speed cap.

## centroid

Average position of the group of robots. The advanced controller uses the measured group centroid as a key formation/trajectory state.

## chariot

The wheeled carrier/platform containing or driven by a Sphero robot.

## course correction

An additional measured travelling-direction correction learned after the basic two-vector heading basis when physical mechanics produce systematic course error.

## DataStream SDK

Vicon's client SDK used by this repository to read live subject/segment pose from Tracker.

## digital twin

Live diagnostic visualisation of measured robot pose and internal controller state. It is an observability tool, not a safety system.

## floor plane

The two coordinate components treated as the planar robot workspace. The reusable configuration supports XY or XZ.

## heading basis

Two measured world displacement vectors produced by Sphero heading 0° and 90°. The controller uses them to transform a desired Vicon-world direction into a Sphero command heading.

## ILC

Iterative Learning Control. In the advanced controller, bounded persisted per-side/path learning terms can be updated from previous run behaviour.

## Image Error

A Vicon calibration/system-health metric relating measured image centroids to reprojected reconstructed 3-D positions. Interpret it using current Vicon documentation rather than copying another laboratory's thresholds blindly.

## mission cap

The advanced controller's `--max-speed` limit for normal mission commands. Mission stiction/breakaway pulses are also capped by it.

## occluded

Tracker/DataStream state indicating the requested segment/measurement is not currently visible/reliably reconstructed.

## rigid object / subject

A tracked body defined from a rigid marker constellation in Tracker. Repository configuration maps it to a software robot label.

## rolling floor

A learned bounded command level that helps a loaded chariot continue rolling after breakaway rather than immediately sticking again.

## segment

A named rigid-body segment within the Vicon subject/object hierarchy. The DataStream calls require both subject and segment names.

## slot

Desired relative location of one robot in the three-robot formation.

## stiction

Static friction. A robot can receive a non-zero command while the loaded chariot remains stationary until sufficient torque is produced.

## System Health Report

Tracker pane used to inspect system/calibration health such as performance, calibration status and image-related diagnostics.

## Vicon world frame

Coordinate frame defined by the Tracker volume origin. Software workspace limits are expressed in this frame.

## Wand Count

Per-camera calibration data count accumulated during the wand-wave stage.

## workspace

Configured software operating rectangle in Vicon-world millimetres. It should sit conservatively inside the physically safe, well-tracked area.
