# Configuration

The project intentionally separates **shareable code** from **site-specific configuration**.

`config/robot_setup.example.toml` is safe to commit. `config/robot_setup.toml` is ignored and is where real values belong.

## Vicon

- `server`: host/IP and DataStream port.
- `floor_plane`: `XY` or `XZ` depending on the motion-capture convention.
- `yaw_euler_index`: Euler component representing planar heading.
- `yaw_sign` / `yaw_offset_deg`: optional coordinate convention adjustment.

## Workspace

Use measured physical bounds in millimetres. Keep a conservative soft margin inside walls, tripods, furniture and areas where Vicon coverage degrades.

## Robots

Each robot entry maps one BLE device to one Vicon subject and segment. Never infer this mapping from list order during a live run; explicitly verify it.

## Environment overrides

`VICON_SERVER`, `SPHERO_1_NAME`, `SPHERO_2_NAME`, `SPHERO_3_NAME`, and matching `VICON_*_SUBJECT` / `VICON_*_SEGMENT` variables are supported for temporary runs and automation.

## Standalone reference-controller overrides

The standalone three-chariot reference controller also accepts `AO_X_MIN_MM`, `AO_X_MAX_MM`, `AO_Y_MIN_MM`, `AO_Y_MAX_MM` and `BOUNDARY_EXTENSION_MM` through the environment. These values are intentionally not committed as measured site data.
