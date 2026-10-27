# Troubleshooting

Debug **from the earliest failed layer**. Do not compensate for an identity or calibration error by tuning the controller.

## Fast diagnosis map

| Symptom | Most likely layer | First check |
|---|---|---|
| no camera data | Vicon/system | System + System Health |
| false markers | masking/environment | reflections/masks |
| coordinates mirrored | origin/axis config | world axes + floor_plane |
| wrong software robot moves by hand | TOML/Vicon mapping | subject/segment |
| wrong Sphero moves | BLE mapping | sphero_name |
| robot travels sideways | heading basis | re-run displacement calibration |
| robot will not break away | mechanics/friction/battery | wheels + calibration movement |
| overshoots after breakaway | drive response | mission cap / learned gain |
| sudden correction after occlusion | tracking | visibility/stale pose |
| dry-run fails | software/controller | traceback + release check |
| live swarm diverges but single robot works | multi-robot controller/geometry | body dimensions, slots, bounds |

## Vicon DataStream import fails

Run:

```powershell
python -c "import vicon_dssdk; print('OK')"
```

If it fails, fix the SDK installation before touching controller code.

Check that the package was installed into the **same Python environment** used to run the repository.

## Tracker Connect fails

Check:

- Tracker running;
- configured host/port;
- network/firewall policy;
- correct machine/environment;
- DataStream SDK installation.

## Connect works but no pose appears

Check:

- Tracker object is tracking;
- subject name exact;
- segment name exact;
- object visible;
- live frames available.

Run the Vicon-only monitor and do not command motors.

## Wrong software label moves when I push a chariot

The TOML mapping is wrong or the wrong Tracker object was recorded.

Fix identity first.

Do not solve this with a label rename in a log or with controller tuning.

## Robot moves sideways, mirrored or at a strange angle

Re-run:

```powershell
python examples/04_heading_calibration.py --config config/robot_setup.toml --robot robot-1
```

Also verify:

- Vicon +X/+Y physically;
- floor_plane;
- correct subject/segment;
- enough calibration displacement.

Do not assume Vicon yaw equals the Sphero command heading.

## Calibration displacement too small

Check in this order:

1. wheel/chariot binding;
2. battery;
3. floor debris;
4. Sphero properly seated;
5. commanded device is the intended robot;
6. available travel clearance;
7. calibration speed.

Increase calibration command only after mechanical causes are ruled out.

## Advanced controller says max speed 140 but calibration looks stronger

Expected if **--calibration-speed** is still higher.

The controller separates:

- mission cap: --max-speed;
- startup displacement calibration: --calibration-speed.

Mission stiction pulses are capped by the mission cap.

## Robot does not move at low mission command

Loaded chariots can have a significant static-friction threshold.

The advanced controller detects Vicon-confirmed stiction and can use a short breakaway pulse. If this happens frequently, inspect mechanics and battery rather than simply raising gains.

## Robot accelerates too much after breakaway

Inspect:

- --max-speed;
- learned drive gain;
- rolling-floor value;
- stiction kick history;
- physical friction change.

Do not reuse learned state blindly after a mechanical change.

## One robot behaves differently

Check:

- battery;
- wheel alignment;
- carrier loading;
- Sphero seating;
- marker/chassis geometry;
- calibration evidence;
- learned response state.

Robot-to-robot variation is one reason the architecture keeps calibration per robot.

## Vicon position jumps

Check:

- marker occlusion;
- rigid-object definition;
- accidental similar marker constellation;
- camera coverage;
- DataStream freshness.

Stop if identity/state is not trustworthy.

## Object swaps identity

Improve physical marker uniqueness and rigidity. Verify only one object follows each chassis during hand movement.

Do not run a swarm when subject identity can swap.

## BLE commands drop or lag

BLE is not hard real-time.

Reduce unnecessary command rate, move away from RF congestion where practical, and verify device connection quality.

Do not increase controller frequency to compensate blindly.

## Oscillation near path/target

Inspect:

- cross-track error;
- velocity estimate;
- command heading;
- drive gain;
- correction magnitude;
- mechanical variation.

Separate a controller issue from a frame/mapping issue first.

## Boundary recovery activates unexpectedly

Verify:

- world origin;
- configured x/y bounds;
- floor_plane;
- body dimensions;
- body_yaw_offset_deg.

Remember the bounds are in Vicon-world millimetres.

## Dry-run works, hardware does not

Dry-run proves software structure, not physical equivalence.

Next check:

1. Vicon identity;
2. Sphero identity;
3. heading calibration;
4. mechanical breakaway;
5. physical workspace;
6. BLE reliability.

## Digital twin looks wrong

First decide whether **tracking data** is wrong or only the **drawn body orientation** is wrong.

If pose position is correct but the rectangle is rotated relative to the real chassis, check body_yaw_offset_deg.

Do not change steering calibration just to rotate the visual footprint.

## After an exception

The drivers/controllers attempt to stop in cleanup paths, but always verify physically that the robots have stopped.

Save the traceback/log before rerunning.

## Still stuck?

Run the workflow again from the last known passing gate in the [end-to-end tutorial](end-to-end-tutorial.md).

The intended debug order is:

**camera health → calibration → origin → rigid-object identity → TOML → DataStream → BLE identity → heading calibration → single robot → dry-run → live swarm**.
