# Release checklist

- [ ] `python tools/release_check.py` passes.
- [ ] `mkdocs build --strict` passes.
- [ ] No local `config/robot_setup.toml` is staged.
- [ ] No raw experimental logs or videos containing private metadata are staged.
- [ ] Any controller change has an appropriate test or documented hardware validation.
- [ ] Version in `pyproject.toml` and `src/sphero_vicon_swarm/__init__.py` matches the tag.
- [ ] Changelog includes user-visible changes.
- [ ] Tag uses semantic versioning, e.g. `v1.0.0`.
