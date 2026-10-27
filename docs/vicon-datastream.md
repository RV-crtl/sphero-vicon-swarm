# Vicon DataStream SDK setup

The Sphero/Vicon swarm reads live poses through Vicon's **DataStream SDK**, using the Python module `vicon_dssdk`.

This page explains the software/network side after Tracker can already see and track the rigid objects.

## What this repository actually uses

The live data path is:

```text
Vicon Tracker
   │
   │ TCP/IP DataStream (normally port 801)
   ▼
vicon_dssdk.ViconDataStream.Client
   │
   ▼
src/sphero_vicon_swarm/tracking/vicon.py
   │
   ▼
Pose2D(x_mm, y_mm, yaw_deg, occluded)
   │
   ▼
heading calibration + controller
```

The repository does **not** require the Tracker UDP Object Stream.

Vicon documents UDP as a reduced object-data path for situations where DataStream cannot be used; if TCP/IP DataStream is available, Vicon recommends using the DataStream SDK.

## 1. Install the SDK

Download the current DataStream SDK from Vicon:

https://www.vicon.com/software/datastream-sdk/?section=downloads

Do not commit the Vicon installer or vendor binaries into this repository.

As of DataStream SDK 1.13, Python support is supplied with the SDK installation/source package. Follow Vicon's installer instructions for your platform.

### Windows Python installation pattern

After installing the SDK, the Python package is normally found under a path similar to:

```text
C:\Program Files\Vicon\DataStream SDK\Win64\Python\vicon_dssdk
```

Install it into the exact Python environment that will run this repository:

```powershell
python -m pip install "C:\Program Files\Vicon\DataStream SDK\Win64\Python\vicon_dssdk"
```

If the SDK installer/package location differs, use the actual installed path.

### SDK 1.13 Python note

Vicon's DataStream SDK 1.13 release notes document a known issue where the supplied install batch file can fail for some recent Python 3 installations. Vicon's workaround is to run the batch file with suitable permissions or copy the package to a user-writable location before installing.

For this project, explicitly installing the `vicon_dssdk` package with the intended interpreter is preferable because it makes the environment unambiguous.

## 2. Confirm the Python package imports

Run:

```bash
python -c "import vicon_dssdk; print('vicon_dssdk import: OK')"
```

If this fails, do not debug the swarm controller yet. Fix the SDK/Python installation first.

You can also run:

```bash
python -m sphero_vicon_swarm doctor
```

to inspect the optional hardware backends visible to the current environment.

## 3. Determine the Tracker host

The local configuration expects:

```toml
[vicon]
server = "HOST_OR_IP:801"
```

Examples:

```toml
server = "localhost:801"
```

when the client runs on the Tracker computer, or:

```toml
server = "TRACKER_HOSTNAME:801"
```

when the client is on another permitted machine.

Use the local lab's approved hostname/address. Do not copy an old private address from a screenshot or previous user's configuration.

## 4. Verify Tracker is providing live data

![Actual Vicon Tracker 4.0 Connections/DataStream panel](assets/vicon/tracker4-actual-datastream-connections.jpg)

*Actual Tracker 4.0 lab screenshot, cropped from the supplied lab material. The site-specific client address is redacted. The highlighted Data Stream area is the interface used by this repository.*

Tracker must be running with live tracking available.

In Tracker 4.x:

1. open **View → Connections**;
2. leave that panel visible;
3. start the repository's pose monitor;
4. confirm a DataStream client appears.

Run:

```bash
python examples/03_vicon_pose_monitor.py \
  --config config/robot_setup.toml \
  --seconds 20
```

The repository's adapter:

- creates a `ViconDataStream.Client`;
- connects to the configured host;
- requests server-push mode when available;
- keeps a small buffer;
- enables segment data;
- gets one frame at a time;
- requests global segment translation and Euler rotation.

## 5. Expected pose-monitor output

You should see output similar to:

```text
robot-1: (  120.4, -340.2) yaw= 91.3 occ=False
robot-2: ( -515.0,  225.9) yaw=182.7 occ=False
robot-3: (  612.7,  -55.1) yaw=271.0 occ=False
```

The values above are examples only.

The important checks are:

- positions change smoothly when a chariot is moved;
- values are in millimetres;
- only the intended robot label responds to that physical robot;
- the horizontal axes agree with `floor_plane`;
- occlusion changes to `True` when tracking is intentionally lost.

## 6. Verify subject and segment names

The adapter calls:

```python
client.GetSegmentGlobalTranslation(vicon_subject, vicon_segment)
client.GetSegmentGlobalRotationEulerXYZ(vicon_subject, vicon_segment)
```

Therefore the configured names must match Tracker exactly.

A typical robot section is:

```toml
[[robots]]
label = "robot-1"
sphero_name = "YOUR_DEVICE_NAME"
vicon_subject = "Robot_1"
vicon_segment = "Robot_1"
```

The subject and segment are often the same for a simple Tracker rigid object, but do not assume this if your Tracker setup differs.

## 7. DataStream port vs UDP settings

The default DataStream endpoint commonly uses port **801**.

Do not confuse this with the **UDP Object Stream** settings visible in Tracker's Connections panel.

For this repository:

| Interface | Required? | Purpose |
|---|---:|---|
| Vicon DataStream SDK | **Yes** | Full live pose client used by the Python code |
| Tracker UDP Object Stream | No | Optional reduced object-data broadcast |
| OSC | No | Not used |
| VRPN | No | Not used |

If someone enables UDP anyway, it does not make the repository use UDP; the Python code still connects through `vicon_dssdk`.

## 8. Network troubleshooting

### `vicon_dssdk` imports but the connection fails

Check:

- Tracker is running;
- the configured hostname/address is correct;
- the client machine can reach the Tracker host;
- local firewall policy allows the connection;
- the DataStream port is not being confused with UDP output configuration;
- you are using the correct network interface for the lab.

Do not publish private lab addresses in issues, screenshots or commits.

### Connection succeeds but no useful pose appears

Check:

- the object is active in Tracker;
- the object name matches the TOML file;
- the segment name matches;
- Tracker is receiving live frames;
- the marker constellation is actually tracking;
- occlusion state;
- System Health Report.

### Pose is correct but steering is wrong

That is normally **not** a DataStream problem.

Run the repository's heading/displacement calibration:

```bash
python examples/04_heading_calibration.py --config config/robot_setup.toml
```

The project intentionally calibrates the Sphero command frame against measured Vicon displacement rather than assuming the two frames align.

## 9. Why the repo uses a buffer of one

The reusable adapter attempts to use server-push streaming and `SetBufferSize(1)`.

For control, recent pose is more useful than a queue of stale poses. A small buffer helps avoid controlling the robot from old frames when the consumer falls behind.

This is separate from Vicon's Tracker processing latency; watch Tracker's **System Health Report → Performance** as well.

## Official references

- [Vicon DataStream SDK downloads](https://www.vicon.com/software/datastream-sdk/?section=downloads)
- [DataStream SDK 1.13 documentation](https://help.vicon.com/space/DSSDK113)
- [DataStream SDK Developer's Guide](https://help.vicon.com/download/attachments/726007858/Vicon%20DataStream%20SDK%20Developer%27s%20Guide.pdf)
- [Tracker 4.4 User Guide](https://help.vicon.com/download/attachments/376309877/Vicon%20Tracker%20User%20Guide.pdf)
