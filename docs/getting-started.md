# Getting started

## 1. Create an environment

```bash
python -m venv .venv
python -m pip install -e ".[dev,docs]"
```

## 2. Check the software-only path

```bash
python -m sphero_vicon_swarm doctor
python -m sphero_vicon_swarm simulate --seconds 5
pytest
```

## 3. Create local hardware configuration

Copy `config/robot_setup.example.toml` to `config/robot_setup.toml` and insert your own Vicon host, device names, rigid-body names and workspace limits. The local configuration is gitignored.

## 4. Verify each subsystem independently

Run the examples in numerical order. Do not begin multi-robot closed-loop motion until the individual robot mapping and Vicon coordinate frame have both been verified.
