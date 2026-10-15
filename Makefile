.PHONY: install dev test lint format format-check typecheck docs privacy simulate check build audit preflight

install:
	python -m pip install -e .

dev:
	python -m pip install -e ".[dev,docs]"

test:
	pytest --cov=sphero_vicon_swarm --cov-report=term-missing

lint:
	ruff check .

format:
	ruff check --fix .
	ruff format .

format-check:
	ruff format --check .

typecheck:
	mypy src/sphero_vicon_swarm

docs:
	mkdocs build --strict

privacy:
	python tools/privacy_scan.py .

simulate:
	python -m sphero_vicon_swarm simulate --seconds 8

check:
	python tools/release_check.py

build:
	python -m build

audit:
	pip-audit . --strict --progress-spinner off

preflight:
	ruff format --check .
	ruff check .
	mypy src/sphero_vicon_swarm
	pytest
	python tools/privacy_scan.py .
	mkdocs build --strict
	python reference_controllers/three_chariot_square_swarm.py --dry-run --timeout 2 --no-digital-twin
	python -m build
