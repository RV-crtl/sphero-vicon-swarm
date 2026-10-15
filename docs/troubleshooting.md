# Troubleshooting

## Robot does not move at low command

Loaded chariots can have a substantial static-friction threshold. Measure breakaway behaviour rather than increasing gains blindly.

## Robot moves sideways or mirrored

Re-run displacement-based heading calibration. Check that the Vicon subject/segment matches the physical robot.

## One robot behaves differently every run

Check battery state, wheel alignment, chariot loading, floor debris, mounting slippage and whether old calibration values are being reused.

## Oscillation near a target

Reduce aggressive position correction, increase damping carefully, slow the arrival profile, and inspect measured velocity. Avoid treating a stationary-point controller as a complete trajectory controller.

## Vicon position jumps

Check marker occlusion, rigid-body definition and stream freshness. Do not command large corrective motion from a clearly invalid frame.

## BLE drops commands

Reduce command rate. BLE is not a hard-real-time transport and excessive command frequency can reduce reliability.
