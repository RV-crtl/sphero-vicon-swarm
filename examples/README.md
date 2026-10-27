# Staged examples

Run these in numerical order on a new hardware setup. Each stage isolates one layer so an identity, configuration or coordinate-frame problem is found before it becomes a multi-robot motion problem.

| Stage | Script | Motion? | What it proves |
|---|---|---:|---|
| 1 | `01_single_sphero_smoke_test.py` | short move | first configured BLE device is the intended robot |
| 2 | `02_multi_sphero_smoke_test.py` | zero speed | all configured Spheros can be independently addressed |
| 3 | `03_vicon_pose_monitor.py` | **no robot motion** | Vicon subject/segment identity, axes, yaw and occlusion |
| 4 | `04_heading_calibration.py` | sequential short moves | Sphero command headings are measured against Vicon displacement for every selected robot |

## Recommended sequence

```powershell
python examples/01_single_sphero_smoke_test.py --config config/robot_setup.toml --speed 60 --seconds 0.5
python examples/02_multi_sphero_smoke_test.py --config config/robot_setup.toml
python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
python examples/04_heading_calibration.py --config config/robot_setup.toml
```

The calibration example processes **all configured robots sequentially by default** and pauses before each robot moves. To calibrate one label only:

```powershell
python examples/04_heading_calibration.py --config config/robot_setup.toml --robot robot-2
```

Measured results are saved to `artifacts/heading_calibration.json`.

!!! important
    The heading-calibration JSON is reference/diagnostic evidence. The feature-rich three-chariot controller performs its own startup calibration unless verified calibration reuse is explicitly requested.

For the complete new-user procedure, including Tracker screenshots and pass/fail criteria, use **[the end-to-end tutorial](../docs/end-to-end-tutorial.md)**.
