# Contributing

Contributions are welcome.

## Development setup

```bash
python -m venv .venv
python -m pip install -e ".[dev,docs]"
pre-commit install  # if pre-commit is installed
```

## Before opening a pull request

```bash
ruff check .
mypy src/sphero_vicon_swarm
pytest --cov=sphero_vicon_swarm
mkdocs build --strict
python tools/privacy_scan.py .
python reference_controllers/three_chariot_square_swarm.py --dry-run --timeout 4 --no-digital-twin
```

Keep hardware-dependent behaviour behind an adapter where possible. Add a hardware-free unit test for mathematical/control changes. Do not commit real IP addresses, Bluetooth identifiers, personal paths or raw logs containing local metadata.

For behaviour changes that affect physical motion, describe the test surface, robot/chariot configuration, speed limit, and whether the result was software-only, bench-tested or physically demonstrated.
