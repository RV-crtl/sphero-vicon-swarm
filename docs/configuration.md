# Configuration

The project separates **shareable code** from **site-specific configuration**. A new user should have one private TOML file that describes the local Vicon connection, physical workspace and robot identity mapping.

`config/robot_setup.example.toml` is safe to commit. Copy it to `config/robot_setup.toml`; the local file is ignored by Git.

```powershell
Copy-Item config/robot_setup.example.toml config/robot_setup.toml
```

## Configuration ownership

| Setting | Lives in TOML? | Why |
|---|---:|---|
| Vicon host/port | yes | site-specific network value |
| floor plane / yaw convention | yes | local coordinate convention |
| physical workspace | yes | must match measured safe area |
| Sphero BLE name | yes | hardware identity |
| Vicon subject/segment | yes | tracking identity |
| body dimensions | yes | collision/visualisation geometry |
| body yaw offset | yes | local segment-to-chassis geometry |
| reusable control law | no | belongs in source |
| measured learning/calibration state | runtime artifact | should not be committed blindly |

## Vicon

```toml
[vicon]
server = "TRACKER_HOST:801"
floor_plane = "XY"
yaw_euler_index = 2
yaw_sign = 1.0
yaw_offset_deg = 0.0
```

- **server** — Tracker/DataStream host plus port.
- **floor_plane** — `XY` or `XZ`.
- **yaw_euler_index** — Euler component used as planar heading.
- **yaw_sign** and **yaw_offset_deg** — optional convention correction.

Do not change yaw fields merely to compensate for a robot that travels sideways. Sphero-command to Vicon-world alignment is measured separately.

## Workspace

```toml
[workspace]
x_min_mm = -2000.0
x_max_mm = 2000.0
y_min_mm = -2000.0
y_max_mm = 2000.0
soft_margin_mm = 300.0
```

Measure these values in Tracker after the world origin has been set.

The configured rectangle should be **smaller than the physical/tracked volume**. Keep the soft margin inside walls, camera tripods, furniture, weak tracking zones and any area an operator cannot safely allow a robot to enter.

## Controller defaults

```toml
[controller]
control_hz = 50.0
command_hz = 20.0
max_speed_cmd = 160
formation_radius_mm = 220.0
square_side_mm = 1500.0
```

These are reusable-library defaults. The standalone advanced reference controller contains additional research-controller parameters and exposes selected runtime overrides through its CLI.

## Robots

Each entry maps **one physical robot** to **one Vicon object**.

```toml
[[robots]]
label = "robot-1"
sphero_name = "YOUR_REAL_BLE_NAME"
vicon_subject = "YOUR_TRACKER_OBJECT"
vicon_segment = "YOUR_TRACKER_SEGMENT"
body_length_mm = 200.0
body_width_mm = 140.0
body_yaw_offset_deg = 0.0
```

### label

Stable software label used in logs and examples.

### sphero_name

Exact discoverable BLE/device name used by the Sphero backend.

### vicon_subject / vicon_segment

Must match Tracker exactly. Confirm identity by moving **one physical chariot at a time** while the Vicon-only monitor is running.

### body_length_mm / body_width_mm

Physical footprint used by the reusable configuration and by the advanced controller's conservative collision geometry.

### body_yaw_offset_deg

Rotation from the Vicon segment yaw axis to the physical long axis of the chassis **for footprint geometry/digital-twin display**.

This is not steering calibration. Steering uses measured displacement.

## One configuration path for examples and reference controllers

The staged examples, the single-chariot controller and the advanced three-chariot controller now all accept:

```text
--config config/robot_setup.toml
```

The single controller can additionally choose a configured label:

```powershell
python reference_controllers/single_chariot_vicon_circle.py --config config/robot_setup.toml --robot robot-2
```

The advanced controller uses the first three configured robots and rejects placeholder Sphero names for a hardware run. Dry-run may fall back to the public example file when the private config is absent.

## Environment overrides

Environment variables remain useful for automation and temporary experiments. They override matching TOML identity/network values.

Supported identity/network examples include:

- `VICON_SERVER`;
- `VICON_FLOOR_PLANE`;
- `SPHERO_1_NAME`, `SPHERO_2_NAME`, `SPHERO_3_NAME`;
- matching `VICON_*_SUBJECT` and `VICON_*_SEGMENT`.

The advanced controller also accepts:

- `AO_X_MIN_MM`, `AO_X_MAX_MM`;
- `AO_Y_MIN_MM`, `AO_Y_MAX_MM`;
- `BOUNDARY_EXTENSION_MM`.

For normal hands-on use, prefer the TOML so the complete mapping is inspectable in one place.

## Validate before motion

```powershell
python -m sphero_vicon_swarm validate-config --config config/robot_setup.toml
```

Then prove the mapping with **no robot commands**:

```powershell
python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
```

Move each physical chariot by hand and confirm only the intended software label changes.

For the complete sequence, see the [end-to-end tutorial](end-to-end-tutorial.md).
