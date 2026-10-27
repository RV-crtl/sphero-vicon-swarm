# End-to-end tutorial — clean PC to first safe three-chariot run

This is the **primary hands-on tutorial** for a new user. Follow it in order. Each stage is a gate: do not move to the next stage until the current one passes.

!!! warning "Moving hardware"
    Later stages command physical robots. Keep the operating area clear, keep the terminal focused so **Ctrl+C** is immediately available, and verify every Sphero-to-Vicon mapping before closed-loop motion.

!!! info "Tracker screenshots and versions"
    The UI images on this page are **real Vicon Tracker 4.1 screenshots** from DASC Lab's public setup documentation. They are used for visual recognition because they clearly show the Tracker 4 interface. The written control names and workflow are checked against current **Tracker 4.4** documentation. Small button positions can differ between point releases.

## What you will prove

By the end of this tutorial you will have proved, in order:

1. the Python package and simulator work without hardware;
2. Tracker sees the expected cameras and has a trustworthy calibration;
3. the world origin and axes make physical sense;
4. each chariot has a distinct rigid object;
5. the local TOML maps each physical Sphero to the correct Vicon object;
6. Python reads the correct pose for every robot;
7. every Sphero can be addressed independently;
8. the Sphero command frame is measured against Vicon displacement for each robot;
9. one robot passes a closed-loop test;
10. the three-robot controller passes dry-run;
11. a conservative live swarm run can be started with known limits and a clear stop path.

~~~mermaid
flowchart LR
    A["Install + self-test"] --> B["Camera health"]
    B --> C["Mask + wand"]
    C --> D["World origin"]
    D --> E["Rigid objects"]
    E --> F["TOML mapping"]
    F --> G["Vicon-only pose"]
    G --> H["Sphero identity"]
    H --> I["Per-robot calibration"]
    I --> J["Single robot"]
    J --> K["Dry-run swarm"]
    K --> L["Live swarm"]
~~~

---

## 0. Physical pre-flight

Before opening Tracker:

- [ ] charge every robot;
- [ ] check chariot wheels rotate freely;
- [ ] check marker clusters are rigid and cannot twist;
- [ ] remove loose cables and unnecessary reflective clutter;
- [ ] define a clear physical operating area;
- [ ] make sure an operator can reach the robots;
- [ ] decide which terminal will remain focused for Ctrl+C;
- [ ] keep people out of the motion volume during tests.

Do not continue if the area is crowded or you cannot stop the robots quickly.

---

## 1. Clone and install the software

For the released workflow:

~~~powershell
git clone --branch v1.0.0 --depth 1 https://github.com/RV-crtl/sphero-vicon-swarm.git
cd sphero-vicon-swarm
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,docs]"
~~~

Install the public Sphero backend when hardware is required:

~~~powershell
python -m pip install -e ".[sphero]"
~~~

### Hardware-free acceptance test

~~~powershell
python -m sphero_vicon_swarm doctor
python -m sphero_vicon_swarm validate-config --config config/robot_setup.example.toml
python -m sphero_vicon_swarm simulate --seconds 8
pytest
python tools/privacy_scan.py .
~~~

**Pass:** imports work, the example config parses, simulated coordinates change, tests pass, and the privacy scan is clean.

If this fails, fix the Python environment before debugging Vicon or Bluetooth.

---

## 2. Create the private local configuration

Copy the public template:

~~~powershell
Copy-Item config/robot_setup.example.toml config/robot_setup.toml
~~~

The local file is gitignored.

### Vicon connection

~~~toml
[vicon]
server = "TRACKER_HOST:801"
floor_plane = "XY"
yaw_euler_index = 2
yaw_sign = 1.0
yaw_offset_deg = 0.0
~~~

Use the locally approved hostname/address. Never copy an address from an old screenshot.

### Workspace

~~~toml
[workspace]
x_min_mm = -2000.0
x_max_mm = 2000.0
y_min_mm = -2000.0
y_max_mm = 2000.0
soft_margin_mm = 300.0
~~~

These numbers must describe the **usable physical region**, not merely the maximum volume Tracker can see. Keep margin inside walls, tripods, weak coverage and other hazards.

### One robot entry

~~~toml
[[robots]]
label = "robot-1"
sphero_name = "YOUR_REAL_BLE_NAME"
vicon_subject = "YOUR_TRACKER_OBJECT"
vicon_segment = "YOUR_TRACKER_SEGMENT"
body_length_mm = 200.0
body_width_mm = 140.0
body_yaw_offset_deg = 0.0
~~~

Repeat for each robot.

**body_yaw_offset_deg** is only for footprint/digital-twin geometry if the Tracker segment axes do not match the long axis of the chassis. It is not a substitute for measured heading calibration.

Validate:

~~~powershell
python -m sphero_vicon_swarm validate-config --config config/robot_setup.toml
~~~

**Pass:** the file parses and no placeholder Sphero name remains.

---

# Part I — Vicon Tracker

## 3. Check camera health before recalibrating

Open Tracker. Confirm the expected camera set is present in **System** and inspect **System Health Report**.

Check:

- [ ] expected cameras are online;
- [ ] a reflective marker moved by hand reconstructs plausibly;
- [ ] no obvious dropped-frame or calibration fault is present;
- [ ] camera temperatures have stabilised enough for calibration at your site.

The correct camera count is your installed count; do not copy a count from another laboratory screenshot.

---

## 4. Open Camera Calibration

This is a real Tracker 4.1 calibration workspace **before masking begins**:

[![Tracker 4.1 Camera Calibration workspace before masking](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/masking_initial.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

Look for:

1. **Masking** on the left;
2. **Mask All**;
3. **Wand Wave** and **Wave All**;
4. **Volume Setup** and **Start Set Origin**;
5. one view per camera in the main workspace.

If your Tracker 4.4 panels are rearranged, follow the control names rather than pixel positions.

---

## 5. Mask unwanted reflections

Remove or cover reflective clutter physically first.

The next screenshot specifically identifies the masking action and the active **Stop** state:

[![Tracker 4.1 Mask All and active masking state](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/masking_mask_all.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

Procedure:

1. select cameras;
2. switch the Workspace to **Cameras**;
3. open **Camera Calibration → Masking**;
4. click **Mask All**;
5. watch unwanted pixels become blue mask regions;
6. click **Stop**;
7. inspect every camera.

**Pass:** environmental reflections that could become false 3-D reconstructions are removed or intentionally masked.

If one remains, use Tracker's manual-mask tools rather than ignoring it.

---

## 6. Configure the wand

This is a deliberate close-up of the **Wand Wave controls**:

[![Tracker 4.1 Wand Wave settings](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/wand_settings.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

Confirm:

- the selected calibration object matches your physical wand;
- Auto Stop is configured as intended;
- the wand parameters belong to your hardware;
- **Wave All** is the action you are about to start.

Do not copy another lab's wand model merely because it appears in the screenshot.

---

## 7. Perform the wand wave

At the beginning of collection the count can still be zero:

[![Tracker 4.1 initial Wand Wave collection state](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/wand_initial.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

Wave through the **entire useful robot volume**: near/far, left/right, different heights, edges and any regions with weaker camera coverage.

During collection the camera panes show wand traces and the left table accumulates counts:

[![Tracker 4.1 Wand Wave in progress with per-camera counts](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/wand_in_progress.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

Do not spend the whole calibration in the centre. Concentrate on cameras with lower counts.

After calibration the table reports the final counts and Image Error:

[![Tracker 4.1 completed wand calibration with Image Error results](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/wand_finished.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

**Pass:**

- collection completes;
- required cameras are calibrated;
- counts are adequate across the system;
- Image Error feedback does not identify an obvious bad camera;
- marker reconstruction is stable throughout the intended motion volume.

At this point cameras are calibrated relative to each other. The world frame still needs an origin.

---

## 8. Set the world origin

Switch to **3D View**. This image shows the real 3-D workspace after camera calibration and before the final origin is accepted:

[![Tracker 4.1 Volume Setup initial 3-D view](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/origin_initial.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

Place the origin/calibration object physically where you want the world origin and orient it deliberately.

Use **Camera Calibration → Volume Setup → Start Set Origin**:

[![Tracker 4.1 Start Set Origin collection](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/origin_pan_zoom.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

After setting it, inspect the final camera/world geometry:

[![Tracker 4.1 result after setting the volume origin](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/origin_final.png)](https://dasc-lab.github.io/robot-framework/flylab/calibration.html)

Physically verify:

- **X = red**;
- **Y = green**;
- **Z = blue**;
- positive X/Y point where expected;
- the floor plane is correct;
- your software workspace lies inside good tracking coverage.

**Pass:** moving a marker in a known direction produces the expected sign/change in coordinates.

---

## 9. Create rigid objects

Use an asymmetric marker constellation with at least four markers; five or more is preferable when practical.

Open **View → Tracking**. This is the Tracking panel before selecting a new marker set:

[![Tracker 4.1 Tracking panel before new-object selection](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/object_initial.png)](https://dasc-lab.github.io/robot-framework/flylab/object.html)

Select the markers belonging to **one physical chariot**. This screenshot shows exactly five selected markers:

[![Tracker 4.1 five-marker cluster selected](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/object_select.png)](https://dasc-lab.github.io/robot-framework/flylab/object.html)

Enter a unique name and click **Create**:

[![Tracker 4.1 object name field and Create control](https://raw.githubusercontent.com/dasc-lab/robot-framework/c3241aa50284640d379de1acb5f87774c5d415a2/docs/flylab/images/object_create.png)](https://dasc-lab.github.io/robot-framework/flylab/object.html)

Repeat for each chariot.

### Prove identity by hand

For every object:

1. move only that physical chariot;
2. confirm exactly one Tracker object follows;
3. record the exact subject and segment names;
4. put those names in the TOML.

Never infer identity from list order.

---

# Part II — DataStream

## 10. Install the Vicon DataStream SDK

Vicon currently publishes **DataStream SDK 1.13** for Tracker 4.x.

Typical Windows Python installation:

~~~powershell
python -m pip install "C:\Program Files\Vicon\DataStream SDK\Win64\Python\vicon_dssdk"
~~~

Verify:

~~~powershell
python -c "import vicon_dssdk; print('vicon_dssdk import: OK')"
python -m sphero_vicon_swarm doctor
~~~

If installation from Program Files fails on a recent Python version, use the vendor workaround described on the [DataStream SDK page](vicon-datastream.md).

---

## 11. Prove Vicon identity with no robot commands

Run:

~~~powershell
python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
~~~

Typical output has one line per configured label, coordinates, yaw and occlusion state.

With it running:

1. move robot 1 by hand — only robot-1 should change;
2. repeat for every robot;
3. move along known +X and +Y;
4. rotate each chassis;
5. briefly occlude a marker cluster.

**Pass:** identity, axis direction, yaw response and occlusion behaviour agree with the physical world.

If the wrong label moves, fix the TOML before doing anything with motors.

---

# Part III — Sphero identity and command frame

## 12. Move exactly one Sphero

~~~powershell
python examples/01_single_sphero_smoke_test.py --config config/robot_setup.toml --speed 60 --seconds 0.5
~~~

**Pass:** the intended first robot makes one short move and stops.

If another device moves, correct the BLE mapping.

---

## 13. Connect all configured Spheros

~~~powershell
python examples/02_multi_sphero_smoke_test.py --config config/robot_setup.toml
~~~

This connects each device and sends zero-speed identification commands.

**Pass:** every configured robot connects and no unexpected device is selected.

---

## 14. Measure the heading basis for every robot

Do not assume Sphero heading zero is aligned with Vicon +X or +Y.

The calibration example now processes **all configured robots sequentially** by default:

~~~powershell
python examples/04_heading_calibration.py --config config/robot_setup.toml
~~~

It pauses before each robot so you can confirm clear space.

For one label only:

~~~powershell
python examples/04_heading_calibration.py --config config/robot_setup.toml --robot robot-2
~~~

For each robot it measures heading 0 and heading 90 displacement, fits the two-dimensional basis, and reports which Sphero headings correspond to Vicon +X and +Y.

Measured results are written to **artifacts/heading_calibration.json**.

**Pass:** both legs have enough displacement and the basis is not close to collinear.

This JSON is diagnostic/reference evidence. The advanced controller performs its own startup calibration unless verified reuse is explicitly requested.

---

# Part IV — Closed-loop validation

## 15. One chariot before three

The single-chariot controller now uses the same TOML mapping as the examples:

~~~powershell
python reference_controllers/single_chariot_vicon_circle.py --config config/robot_setup.toml
~~~

Choose a specific configured label if needed:

~~~powershell
python reference_controllers/single_chariot_vicon_circle.py --config config/robot_setup.toml --robot robot-2
~~~

Watch for:

- stable Vicon visibility;
- credible calibration displacement;
- motion in the requested world direction;
- no persistent wrong-way detector;
- clean Ctrl+C stop.

**Pass:** one chariot completes the closed-loop milestone without identity/frame ambiguity.

---

## 16. Run the advanced controller without hardware

~~~powershell
python reference_controllers/three_chariot_square_swarm.py ^
  --config config/robot_setup.toml ^
  --dry-run ^
  --timeout 8 ^
  --no-digital-twin
~~~

In PowerShell, run the command on one line or replace the caret continuation with the PowerShell backtick.

Dry-run deliberately includes asymmetric heading/speed response and loaded-chariot stiction.

If the private config is absent, dry-run only can fall back to the public example configuration.

**Pass:** no exception, a log is produced, and cleanup is clean.

---

## 17. Understand the two speed controls

The advanced controller intentionally separates two different limits.

### Mission command cap — --max-speed

This caps ordinary mission commands **and stiction/breakaway pulses during the swarm mission**.

### Startup displacement calibration — --calibration-speed

This is the pre-run movement command used to measure the Sphero-to-Vicon mapping. Default is **255** because the original loaded chariots required decisive displacement.

That default is deliberately strong. It is not the same as the mission cap.

If your setup can calibrate reliably at a lower command, lower it explicitly.

---

## 18. First physical three-chariot run

Before starting:

- [ ] all Vicon objects visible;
- [ ] identity mapping physically checked;
- [ ] measured workspace conservative;
- [ ] pose monitor passed;
- [ ] single-Sphero test passed;
- [ ] per-robot heading test passed;
- [ ] single-chariot closed loop passed;
- [ ] advanced dry-run passed;
- [ ] enough clear travel exists for startup calibration;
- [ ] operator has the terminal and Ctrl+C;
- [ ] operating area is empty.

Example conservative first mission:

~~~powershell
python reference_controllers/three_chariot_square_swarm.py --config config/robot_setup.toml --laps 1 --max-speed 140 --calibration-speed 180
~~~

If calibration command 180 does not produce enough displacement on a loaded chassis, **do not blindly increase it**. First check friction, battery, available travel, marker tracking and the reason the calibration failed.

At startup the controller now prints the config file, Vicon server, workspace, mission cap and calibration command.

---

## 19. Watch the right telemetry

The advanced controller reports/logs:

- mission phase, side and lap;
- virtual reference position;
- centroid position and velocity;
- formation RMS;
- pair/body clearance;
- workspace-edge clearance;
- each robot's pose and velocity;
- target and rail/cross-track errors;
- command heading and speed;
- learned breakaway/rolling-floor values;
- learned drive gain;
- stiction kick count.

The digital twin is a diagnostic view, not a replacement for watching the real robots.

---

## 20. Stop conditions

Stop immediately if:

- the wrong physical robot moves;
- Vicon identity swaps or tracking remains occluded;
- coordinates appear mirrored;
- a robot persistently drives opposite the intended path;
- a chassis repeatedly approaches a physical boundary;
- body separation looks unsafe;
- Bluetooth loss makes behaviour unpredictable;
- the operator no longer understands/confidently predicts the controller state.

Use Ctrl+C first. Physically intervene only when safe.

---

# Final acceptance checklist

A new setup is ready for experimental use only when:

- [ ] software-only tests pass;
- [ ] Tracker camera health is acceptable;
- [ ] masking, wand calibration and origin are verified;
- [ ] every rigid object has been physically identified;
- [ ] TOML mapping matches the hardware;
- [ ] Vicon-only pose monitor passes;
- [ ] one-Sphero test passes;
- [ ] multi-Sphero addressing passes;
- [ ] every robot's displacement calibration passes;
- [ ] single-chariot closed loop passes;
- [ ] three-chariot dry-run passes;
- [ ] workspace and stop path are clear;
- [ ] live-run mission and calibration caps were chosen deliberately.

# Debug in this order

**camera health → camera calibration → world origin → rigid-object identity → TOML mapping → DataStream → Sphero identity → heading calibration → single robot → dry-run swarm → live swarm**

Use [Troubleshooting](troubleshooting.md) for symptom-specific diagnosis.

Once you already understand the workflow, use the [Operator quick checklist](vicon-operator-checklist.md) as the bench-side condensed version.

Use the [Tracker visual guide](vicon-tracker-ui-guide.md) as the screenshot atlas.
