# Safety

This repository can command physical robots. Treat every hardware run as a moving-equipment experiment.

The software contains safeguards, but it is **not safety-certified** and no collision/boundary algorithm replaces a clear physical test area and an attentive operator.

## Safety model

The project uses several layers:

1. **operator control** — clear volume, terminal focus, Ctrl+C and physical access;
2. **identity validation** — prove Sphero ↔ Vicon mapping before motion;
3. **tracking validation** — reject ambiguous/occluded/stale state;
4. **workspace bounds** — keep software motion inside a conservative area;
5. **body separation** — reduce/redirect motion when physical boxes approach;
6. **command shaping** — heading/speed rate limits and bounded corrections;
7. **cleanup** — stop robots in finally/context cleanup paths.

A fault in one layer should not be treated as permission to remove the other layers.

## Pre-run gate

Do not start a live multi-robot run until:

- [ ] software-only checks pass;
- [ ] Vicon camera/calibration health is acceptable;
- [ ] each rigid object has been physically identified;
- [ ] TOML mapping has been verified with the Vicon-only monitor;
- [ ] Sphero identity has been verified;
- [ ] heading calibration has been measured;
- [ ] single-chariot validation has passed;
- [ ] advanced dry-run has passed;
- [ ] workspace is clear;
- [ ] an operator owns the stop action.

## Ctrl+C and terminal focus

Before a physical test, click/focus the terminal in which the controller is running.

Do not hide the terminal behind another full-screen application if Ctrl+C is the primary software stop.

If a GUI/digital twin is open, it is diagnostic—not the emergency stop.

## Tracking loss

An occluded or stale pose is not a valid state estimate.

If tracking remains invalid:

- stop or hold robot commands;
- do not issue a large correction based on the last good pose;
- restore tracking/identity first.

Never “tune through” a Vicon identity problem.

## Boundary policy

Configure bounds inside the safe physical region.

Boundary recovery exists to reduce risk when a robot approaches the software edge. It is not permission to put an obstacle directly on the boundary.

Leave real physical margin outside the configured operating rectangle.

## Collision/separation policy

The advanced controller accounts for body footprint and uses separation corrections, but:

- body geometry is still an approximation;
- Vicon latency exists;
- BLE command latency exists;
- wheel/chariot mechanics vary.

Do not deliberately test contact at normal mission speed.

## Speed semantics in the advanced controller

Two separate values matter.

### --max-speed

Mission command cap. It now caps normal mission commands **and mission stiction/breakaway pulses**.

### --calibration-speed

Startup displacement-calibration command. Default is 255 because the original loaded platform needed strong movement to obtain a useful measured basis.

That default is intentionally strong.

For a new setup, choose calibration speed based on:

- available travel clearance;
- measured breakaway behaviour;
- whether lower commands produce enough displacement;
- tracking quality.

Do not assume a conservative mission cap also limits startup calibration.

## Calibration clearance

The advanced controller uses travel and boundary guards during calibration, but still provide ample physical clearance before every calibration leg.

If a robot cannot move far enough to obtain a valid measurement at a safe command, fix the mechanical/setup problem before increasing torque blindly.

## Stiction pulses

A loaded chariot may not move at ordinary rolling commands. The advanced controller can apply a short Vicon-confirmed breakaway pulse when it detects that a robot is stationary despite a meaningful request.

Mission pulses are capped by **--max-speed**.

Do not defeat this cap by manually increasing constants for a first run.

## Physical intervention

If software control becomes unreliable:

1. request a software stop if safe;
2. wait for motion to cease where possible;
3. physically intervene only when you can do so without entering the path of a moving robot.

## Stop conditions

Stop if:

- the wrong robot moves;
- Vicon identity is ambiguous;
- persistent occlusion occurs;
- coordinate axes appear wrong;
- a robot moves persistently opposite the intended path;
- boundary behaviour is not credible;
- robots approach unsafe separation;
- Bluetooth becomes unreliable;
- the operator cannot explain the current behaviour.

## After a stop

Do not immediately restart.

Record:

- what stage/phase failed;
- which robot;
- Vicon state;
- command state;
- workspace/separation values;
- whether a hardware/configuration change preceded the fault.

Then debug from the earliest failed layer.

The [end-to-end tutorial](end-to-end-tutorial.md) defines the recommended validation order.
