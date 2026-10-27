# Vicon DataStream SDK — project setup

This project uses the **Vicon DataStream SDK** to read Tracker data from Python.

The project does **not** depend on Vicon's UDP Object Stream for its normal Python control path.

## Source of truth

Use the Vicon manufacturer documentation for the SDK version installed on the host:

- Vicon DataStream SDK documentation: https://help.vicon.com/space/DSSDK113
- Vicon support/downloads: https://www.vicon.com/support/software-downloads/

Do not redistribute the Vicon SDK installer from this repository.

## What the repository expects

The Python adapter imports:

```python
from vicon_dssdk import ViconDataStream
```

and creates:

```python
client = ViconDataStream.Client()
client.Connect(config.server)
```

The implementation is in:

```text
src/sphero_vicon_swarm/tracking/vicon.py
```

## Install the SDK

Install the Vicon DataStream SDK using the vendor installer/instructions appropriate to the workstation and installed Tracker/SDK release.

Then ensure the Python environment can import `vicon_dssdk`.

Test:

```bash
python -c "import vicon_dssdk; print('vicon_dssdk import: OK')"
```

If that import fails, stop. The swarm software cannot read live Vicon frames until the SDK Python bindings are available to the same interpreter running the project.

## Configure the endpoint

In the local, gitignored file:

```toml
[vicon]
server = "127.0.0.1:801"
```

The value above is an **example only**.

Use the host/endpoint required by the local Vicon workstation/network arrangement and the installed DataStream SDK configuration.

Private lab addresses must not be committed to Git.

## Verify with the repository's Vicon-only monitor

Before enabling any robot motion:

```bash
python examples/03_vicon_pose_monitor.py \
  --config config/robot_setup.toml \
  --seconds 20
```

The monitor uses the same reusable `ViconTracker` adapter as the project.

It requests frames and reports the configured robots':

- planar position;
- yaw;
- occlusion state.

## Why UDP Object Stream is not part of the normal project path

Some older/local Vicon notes describe configuring Tracker's UDP Object Stream. That is a separate output mechanism.

The swarm repository uses the DataStream SDK API directly. Therefore:

- do not enable/configure UDP merely because an old checklist mentions it;
- only configure UDP if another local application genuinely requires it;
- do not copy an old UDP address into the project TOML file.

This distinction is important when reproducing the work: the controller's Vicon dependency is the **DataStream SDK**, not a custom UDP parser.

## Troubleshooting

### `ModuleNotFoundError: vicon_dssdk`

The SDK Python bindings are not installed/visible to this Python interpreter.

Check:

```bash
python -c "import sys; print(sys.executable)"
```

Then install/configure the Vicon bindings for that interpreter according to Vicon's SDK instructions.

### SDK imports but cannot connect

Check, in this order:

1. Tracker is running.
2. The Vicon camera/system network is healthy.
3. The local DataStream endpoint is correct.
4. Host firewall/network policy permits the connection.
5. The host and Tracker/DataStream SDK versions are compatible.
6. A manufacturer SDK example can connect before blaming the swarm controller.

### Connection works but a robot is missing

That is usually an object-name/mapping issue rather than a DataStream transport issue.

Check:

- `vicon_subject`;
- `vicon_segment`;
- that the object is present/tracked in Tracker;
- that the exact configured spelling matches Tracker.

## Next step

Once the Vicon-only monitor is stable, continue with the [full Vicon reproduction procedure](vicon-setup.md), then perform [heading calibration](control-design.md).
