# Control design

This page explains **why the controller is structured the way it is**, including the distinction between the reusable package and the feature-rich three-chariot reference controller.

## 1. Vicon is navigation truth

A Sphero inside a loaded wheeled chariot is not an ideal planar actuator. The realised motion depends on:

- static friction;
- rolling friction;
- wheel alignment;
- battery state;
- chassis loading;
- internal stabilisation;
- quantised BLE speed/heading commands.

The controller therefore trusts measured Vicon displacement for navigation rather than dead-reckoning from the commanded Sphero heading.

## 2. Do not reduce calibration to one yaw offset

A simple approach would be:

```text
sphero_heading = world_heading + constant_offset
```

The project deliberately does not assume that is sufficient.

Instead, it measures the world displacement produced by two approximately orthogonal Sphero commands.

Let:

```text
v0  = measured unit world vector for Sphero heading 0°
v90 = measured unit world vector for Sphero heading 90°
```

A desired world vector w is represented by:

```text
w ≈ a v0 + b v90
~~~

and the internal Sphero command angle is recovered from the measured coefficients.

This accommodates rotation, sign changes and imperfect non-orthogonality better than assuming a single shared frame offset.

## 3. Why calibration is per robot

Even nominally identical chariots can differ.

Calibration is therefore stored/learned per robot rather than copied across the group.

The staged example now calibrates configured robots one at a time and produces inspectable JSON evidence.

## 4. P / PD / PID experiments

P, PD and PID-style corrections were useful development experiments for:

- cross-track convergence;
- damping;
- overshoot;
- responsiveness;
- disturbance recovery.

The experiments did **not** justify publishing one universal set of fixed gains for all loaded chariots and runs.

That is an engineering conclusion, not a statement that PID is intrinsically unsuitable.

The final architecture keeps the reusable ideas:

- measured external state;
- per-robot calibration;
- feed-forward reference motion;
- bounded feedback correction;
- independent physical safety layers;
- measured/observable runtime telemetry.

## 5. State estimation

The advanced controller estimates planar velocity from a short history of accepted Vicon poses.

It also filters/guards against physically implausible jumps.

A state is not accepted simply because Tracker returned a number.

## 6. Moving-reference square trajectory

The advanced controller uses a continuously moving square reference rather than repeatedly stopping at mathematically exact corner points.

Conceptually:

```text
square path
   |
   v
virtual reference point moving along active side
   |
   +--> formation slot for robot 1
   +--> formation slot for robot 2
   +--> formation slot for robot 3
```

An ahead robot can wait/slow rather than reversing aggressively toward an old target.

## 7. Formation control

Each robot receives a fixed relative slot around the group reference.

The controller combines:

- common reference motion;
- relative slot correction;
- small separation correction;
- boundary correction.

Corrections are bounded so one robot is not allowed to choose an arbitrary unrelated trajectory during nominal square motion.

## 8. Body-aware separation

The robots are not points.

The controller uses a rectangular chassis approximation plus margins and computes body clearance.

As clearance decreases, allowed motion is progressively restricted.

The configuration includes body length/width and optional segment-to-body yaw offset.

## 9. Boundary handling

Software workspace bounds are loaded from local configuration.

Boundary handling uses **body edge clearance**, not only the centroid.

The outer physical test area should still be larger than the configured control rectangle.

## 10. Stiction detection

A loaded chariot can receive a legitimate motion request without moving.

The advanced controller uses Vicon to detect this condition:

- requested vector is meaningful;
- measured displacement remains small;
- measured speed remains low;
- condition persists long enough;
- no recovery mode forbids the pulse.

Only then can it issue a short breakaway command.

## 11. Mission cap now also caps stiction pulses

During the mission:

```text
pulse_command <= --max-speed
```

This makes the user-facing mission cap meaningful for ordinary commands **and breakaway pulses**.

## 12. Startup calibration is a separate command

The advanced controller's startup displacement calibration uses **--calibration-speed**.

Default is 255 because the original loaded chariots required decisive movement for enough displacement to fit the basis.

This is intentionally separate from mission speed.

A new setup can lower calibration speed, but only if the measured displacement remains adequate and there is clear travel space.

## 13. Rolling-floor / drive-gain learning

After breakaway, the robot may need a minimum rolling command to avoid immediately sticking again.

The controller tracks a bounded learned rolling floor.

It also estimates the relationship between command and measured speed while the robot is already moving, rather than permanently assuming one fixed mm/s-per-command value.

## 14. Course verification

Static two-axis calibration identifies the command basis, but physical chassis mechanics can create a systematic travelling-course error.

The advanced controller therefore performs additional Vicon-based course verification and can learn a bounded course correction.

## 15. Collision bumper

Separation is treated as a short-range physical safety correction rather than as a general flocking force.

The square/formation objective remains dominant until physical clearance becomes small.

## 16. ILC / persistent learning

The advanced controller can persist bounded learning terms such as:

- per-side heading trim;
- cruise scale;
- formation trim;
- drive response;
- breakaway/rolling behaviour.

These values are physical-experiment state.

Do not commit/reuse them blindly after changing the robot, chariot, floor, wheel alignment or marker geometry.

## 17. Telemetry

A serious control test should be explainable after it happens.

The controller records enough fields to inspect:

- reference;
- centroid;
- formation;
- body/boundary clearances;
- per-robot state;
- command;
- calibration/learning state;
- stiction events.

The digital twin presents many of the same signals live.

## 18. What “good control” means here

The objective is not maximum speed or maximum controller complexity.

A strong run is:

- correctly identified;
- correctly calibrated;
- bounded;
- observable;
- repeatable;
- recoverable;
- clear about limitations.

For test gates and commands, see [Validation](validation.md). For hands-on operation, use the [end-to-end tutorial](end-to-end-tutorial.md).
