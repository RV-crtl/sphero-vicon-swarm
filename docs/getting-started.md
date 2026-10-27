# Getting started

If this is your **first time with the system**, use the **[end-to-end tutorial](end-to-end-tutorial.md)**. It includes real Tracker screenshots, physical pre-flight checks, pass/fail criteria, DataStream identity checks, per-robot calibration, single-robot validation and the first conservative swarm run.

This page is the shorter software-first installation path.

## 1. Get a versioned release

```bash
git clone --branch v1.0.0 --depth 1 https://github.com/RV-crtl/sphero-vicon-swarm.git
cd sphero-vicon-swarm
```

A tagged release is preferable to an arbitrary development commit when you need reproducibility.

## 2. Create an isolated environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev,docs]"
```

For Sphero hardware:

```bash
python -m pip install -e ".[sphero]"
```

## 3. Prove the hardware-free path

```bash
python -m sphero_vicon_swarm doctor
python -m sphero_vicon_swarm validate-config --config config/robot_setup.example.toml
python -m sphero_vicon_swarm simulate --seconds 8
pytest
python tools/privacy_scan.py .
```

Do not debug Bluetooth or Vicon until these pass.

## 4. Create the private hardware configuration

Windows:

```powershell
Copy-Item config/robot_setup.example.toml config/robot_setup.toml
```

macOS/Linux:

```bash
cp config/robot_setup.example.toml config/robot_setup.toml
```

Fill in:

- Vicon host/port;
- floor plane/yaw convention where required;
- measured workspace;
- Sphero BLE names;
- Vicon subject/segment names;
- body dimensions and optional body-yaw geometry offset.

See [Configuration](configuration.md).

## 5. Install Vicon DataStream

The Vicon DataStream SDK is vendor software and is not redistributed by this repository.

Install the current SDK/Python bindings into the same virtual environment, then run:

```bash
python -c "import vicon_dssdk; print('vicon_dssdk: OK')"
python -m sphero_vicon_swarm doctor
```

See [DataStream SDK setup](vicon-datastream.md).

## 6. Validate in stages

```bash
python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml --seconds 20
python examples/01_single_sphero_smoke_test.py --config config/robot_setup.toml --speed 60 --seconds 0.5
python examples/02_multi_sphero_smoke_test.py --config config/robot_setup.toml
python examples/04_heading_calibration.py --config config/robot_setup.toml
```

The heading example now calibrates configured robots sequentially by default.

## 7. One robot, then three

Single robot:

```bash
python reference_controllers/single_chariot_vicon_circle.py --config config/robot_setup.toml
```

Advanced dry-run:

```bash
python reference_controllers/three_chariot_square_swarm.py --config config/robot_setup.toml --dry-run --timeout 8 --no-digital-twin
```

Only after the staged gates pass should you consider a live multi-robot run.

## 8. Before the first live run

Read:

- [End-to-end tutorial](end-to-end-tutorial.md)
- [Hardware setup](hardware-setup.md)
- [Safety](safety.md)
- [Validation](validation.md)
- [Troubleshooting](troubleshooting.md)

The advanced controller separates the **mission cap** (`--max-speed`) from the **startup displacement-calibration command** (`--calibration-speed`). Understand both before hardware motion.
