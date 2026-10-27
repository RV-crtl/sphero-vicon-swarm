# Command reference

This page answers a practical operator question: **“What exactly will this command do?”**

Use the [end-to-end tutorial](end-to-end-tutorial.md) for sequence and context.

## Motion legend

| Level | Meaning |
|---|---|
| **NO MOTION** | does not command physical robots |
| **ZERO-SPEED** | connects to robots but sends speed 0 |
| **SHORT MOTION** | commands a brief physical movement |
| **CLOSED LOOP** | continuously commands a physical robot/controller |

---

## Package CLI

### doctor

~~~powershell
python -m sphero_vicon_swarm doctor
~~~

**Motion:** NO MOTION

Reports Python/environment information and whether optional Sphero/Vicon backends can be imported.

Use it immediately after installation.

---

### validate-config

~~~powershell
python -m sphero_vicon_swarm validate-config --config config/robot_setup.toml
~~~

**Motion:** NO MOTION

Parses/sanity-checks the TOML. It can report placeholders, but parsing alone does not prove physical identity mapping.

---

### simulate

~~~powershell
python -m sphero_vicon_swarm simulate --seconds 8
~~~

**Motion:** NO PHYSICAL MOTION

Runs the reusable package's simple hardware-free robot-motion simulation.

---

## Staged examples

### 01_single_sphero_smoke_test.py

~~~powershell
python examples/01_single_sphero_smoke_test.py --config config/robot_setup.toml --speed 60 --seconds 0.5
~~~

**Motion:** SHORT MOTION

What it does:

- loads the first configured robot;
- connects by its Sphero name;
- commands heading 0;
- clamps requested speed to 0–100;
- clamps duration to 0.1–1.5 s;
- closes the driver in finally/cleanup.

Defaults:

- speed 70;
- duration 0.7 s.

Use it only after you know the area in front of that robot is clear.

---

### 02_multi_sphero_smoke_test.py

~~~powershell
python examples/02_multi_sphero_smoke_test.py --config config/robot_setup.toml
~~~

**Motion:** ZERO-SPEED

Connects every configured Sphero and sends a different heading with speed 0.

Purpose: prove all BLE identities can be addressed without intentionally moving them.

---

### 03_vicon_pose_monitor.py

~~~powershell
python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
~~~

**Motion:** NO ROBOT MOTION

Reads/prints:

- software label;
- planar X/Y;
- yaw;
- occlusion.

Use this to prove the Sphero/Vicon mapping **before motors are enabled**.

Default duration: 10 s.

---

### 04_heading_calibration.py

~~~powershell
python examples/04_heading_calibration.py --config config/robot_setup.toml
~~~

**Motion:** SHORT MOTION, SEQUENTIAL

Default behaviour:

- processes all configured robots;
- pauses before each robot;
- moves only one robot at a time;
- commands heading 0, measures Vicon displacement;
- commands heading 90, measures Vicon displacement;
- fits HeadingBasis;
- writes artifacts/heading_calibration.json.

Useful options:

~~~text
--robot robot-2       calibrate one selected software label
--robot robot-1 --robot robot-3
                      calibrate several selected labels in supplied order
--speed 90            motion command, clamped 1..255
--seconds 0.8         command duration, clamped 0.2..5.0 s
--output PATH         JSON output path
--no-prompt           suppress per-robot operator pause
~~~

Do not use --no-prompt for an unfamiliar physical setup.

---

## Reference controllers

### single_chariot_vicon_circle.py

~~~powershell
python reference_controllers/single_chariot_vicon_circle.py --config config/robot_setup.toml
~~~

**Motion:** CLOSED LOOP

Uses the first configured robot.

Select another configured label:

~~~powershell
python reference_controllers/single_chariot_vicon_circle.py --config config/robot_setup.toml --robot robot-2
~~~

The controller:

1. connects Vicon;
2. connects the selected Sphero;
3. performs displacement calibration;
4. approaches/orbits the configured circle;
5. uses wrong-way detection;
6. stops/cleans up on exit.

This is the mandatory single-agent integration gate before a physical swarm.

---

### three_chariot_square_swarm.py — dry-run

~~~powershell
python reference_controllers/three_chariot_square_swarm.py --config config/robot_setup.toml --dry-run --timeout 8 --no-digital-twin
~~~

**Motion:** NO PHYSICAL MOTION

If the private config file is absent, dry-run can fall back to the public example TOML.

The dry simulator injects asymmetric response/stiction so the controller sees non-identical agents.

---

### three_chariot_square_swarm.py — hardware

~~~powershell
python reference_controllers/three_chariot_square_swarm.py --config config/robot_setup.toml --laps 1 --max-speed 140 --calibration-speed 180
~~~

**Motion:** CLOSED LOOP, MULTI-ROBOT

Important options:

| Option | Meaning |
|---|---|
| --config | shared TOML mapping |
| --side-mm | square side length, internally bounded |
| --laps | 0 = continuous; otherwise requested laps |
| --max-speed | **mission command cap**, including mission stiction pulses |
| --calibration-speed | startup displacement-calibration command |
| --timeout | optional wall-clock mission timeout; 0 means no timeout |
| --log | CSV log path |
| --reuse-calibration | explicitly reuse last verified reference calibration |
| --recalibrate | compatibility/forced fresh-calibration flag |
| --dry-run | use simulation rather than hardware |
| --no-digital-twin | disable Tk dashboard |

#### Critical distinction

**--max-speed does not set the startup calibration speed.**

Default startup calibration command is 255. Choose --calibration-speed deliberately for a new setup.

#### Fresh calibration

Fresh calibration is the default for hardware.

Previously measured calibration is reused only when explicitly requested with --reuse-calibration and available/valid.

---

## Release and maintenance commands

### Local release check

~~~powershell
python tools/release_check.py
~~~

**Motion:** NO PHYSICAL MOTION

It now checks:

- compilation of src, examples, reference controllers and tools;
- public example TOML validation;
- unit tests;
- privacy scan;
- advanced-controller dry-run.

Generated release-check artifacts are cleaned up afterward.

---

### Privacy scan

~~~powershell
python tools/privacy_scan.py .
~~~

**Motion:** NO MOTION

Run before publishing local changes.

---

## Recommended operator sequence

~~~text
doctor
  ↓
validate-config
  ↓
Vicon-only pose monitor
  ↓
single-Sphero smoke test
  ↓
multi-Sphero zero-speed test
  ↓
per-robot heading calibration
  ↓
single-chariot closed loop
  ↓
three-chariot dry run
  ↓
first conservative physical swarm
~~~

Never jump directly from installation to the live swarm on a new setup.
