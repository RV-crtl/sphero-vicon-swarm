# Getting started

The safest path is to verify the software-only workflow first, then enable hardware one subsystem at a time.

## 1. Get a stable release

For a reproducible installation, clone the tagged release rather than an arbitrary development commit:

```bash
git clone --branch v1.0.0 --depth 1 https://github.com/RV-crtl/sphero-vicon-swarm.git
cd sphero-vicon-swarm
```

You can also download the wheel and source distribution from the GitHub Releases page. Cloning the repository is recommended when you want the examples, configuration template and reference controllers alongside the package.

## 2. Create an isolated environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

Install the software and developer validation tools:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev,docs]"
```

## 3. Check the software-only path

```bash
python -m sphero_vicon_swarm doctor
python -m sphero_vicon_swarm validate-config --config config/robot_setup.example.toml
python -m sphero_vicon_swarm simulate --seconds 8
pytest
python tools/privacy_scan.py .
```

These steps require no Sphero or Vicon hardware.

## 4. Create local hardware configuration

Copy `config/robot_setup.example.toml` to `config/robot_setup.toml` and insert your own Vicon host, device names, rigid-body names and workspace limits. The local configuration is gitignored.

Windows PowerShell:

```powershell
Copy-Item config/robot_setup.example.toml config/robot_setup.toml
```

macOS/Linux:

```bash
cp config/robot_setup.example.toml config/robot_setup.toml
```

## 5. Install the optional hardware backend

For the public Sphero BLE backend:

```bash
python -m pip install -e ".[sphero]"
```

The Vicon DataStream SDK and its Python bindings are vendor software and are not redistributed by this project. Install the SDK separately for your platform.

## 6. Verify each subsystem independently

Run the staged examples in numerical order:

```bash
python examples/01_single_sphero_smoke_test.py --config config/robot_setup.toml
python examples/02_multi_sphero_smoke_test.py --config config/robot_setup.toml
python examples/03_vicon_pose_monitor.py --config config/robot_setup.toml
python examples/04_heading_calibration.py --config config/robot_setup.toml
```

Do not begin multi-robot closed-loop motion until the individual robot mapping, Vicon coordinate frame, operating-area bounds and stop path have all been verified.

## 7. Move to closed-loop control

Start with the single-chariot reference controller, then use the three-chariot controller in dry-run mode before commanding real motion.

```bash
python reference_controllers/single_chariot_vicon_circle.py
python reference_controllers/three_chariot_square_swarm.py --dry-run --timeout 8 --no-digital-twin
```

See the hardware, Vicon, safety and troubleshooting documentation before a physical multi-robot run.
