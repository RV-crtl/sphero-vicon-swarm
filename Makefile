.PHONY: install dev test lint format typecheck docs privacy check simulate build

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
