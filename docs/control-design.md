# Control design

## Vicon as navigation truth

The loaded chariot can slip, rotate or move differently from the ideal Sphero body model. External Vicon position therefore provides the most useful reference for closed-loop planar motion.

## Per-robot heading calibration

Each robot is calibrated independently by measuring Vicon displacement under known Sphero heading commands. This avoids assuming a shared frame offset or sign convention across chariots.

## P / PD / PID experiments

Proportional, proportional-derivative and PID-style corrections were explored during development. They were useful for understanding overshoot, cross-track correction and damping, but a single fixed set of gains was not consistently transferable between runs. Observed causes included different breakaway thresholds, rolling resistance, battery state, mounting geometry and run-to-run mechanical variation.

The public controller therefore treats fixed PID as **one optional technique**, not as the identity of the project. The stronger reusable principles are:

- use measured external state;
- calibrate every robot independently;
- separate path geometry from robot actuation;
- use feed-forward motion plus bounded corrections;
- slow or hold path progression when measured error is too large;
- keep boundary/collision handling outside the nominal controller;
- log enough state to diagnose failures after the run.

This does not imply PID is unsuitable for Sphero systems. It means the experiments did not justify publishing one universal set of gains for all loaded chariots and operating conditions.
