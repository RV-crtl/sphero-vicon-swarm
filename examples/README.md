# Staged examples

Run these in numerical order on a new setup. Each stage isolates one layer of the system so a configuration or coordinate-frame problem is found before it becomes a moving-robot problem.

1. `01_single_sphero_smoke_test.py` — one BLE connection and short motion.
2. `02_multi_sphero_smoke_test.py` — all configured robots, independently addressed.
3. `03_vicon_pose_monitor.py` — Vicon only; no robot commands.
4. `04_heading_calibration.py` — one robot; learn Sphero-heading ↔ Vicon-world mapping from measured displacement.

Use a cleared operating area and conservative speed settings.
