import math
import os
import time
from dataclasses import dataclass
from typing import Optional, Tuple

from vicon_dssdk import ViconDataStream

from spherov2 import scanner
from spherov2.sphero_edu import SpheroEduAPI, EventType
from spherov2.types import Color


# ============================================================
# Vicon Closed-Loop Circle Controller
# One Sphero BOLT+ carrying a chariot
# ============================================================
#
# Objective:
#   Start from anywhere, drive to a 10 cm diameter circle, then orbit around it
#   slowly while using Vicon feedback to correct the path.
#
# Main fixes compared with the previous version:
#   1. Does not trust Vicon yaw for Sphero heading.
#   2. Calibrates Sphero heading 0 and 90 using actual Vicon displacement.
#   3. Converts Vicon-world motion vectors into Sphero headings using that calibration.
#   4. Stops if Vicon shows the chariot is moving away instead of toward the target.
#   5. Uses slower, chariot-safe motion.
# ============================================================


# ------------------------------------------------------------
# Sphero settings
# ------------------------------------------------------------

SPHERO_NAME = os.getenv("SPHERO_1_NAME", "YOUR_DEVICE_NAME")

SCAN_TIMEOUT_S = 15
CONNECT_RETRIES = 4
CONNECT_RETRY_DELAY_S = 2.0


# ------------------------------------------------------------
# Vicon settings
# ------------------------------------------------------------

VICON_SERVER = os.getenv("VICON_SERVER", "127.0.0.1:801")

SUBJECT_NAME = "Chariot 1"
SEGMENT_NAME = "Chariot 1"

# Most Vicon labs use X/Y as floor plane and Z as vertical.
# If your Vicon floor plane is X/Z, change this to "XZ".
FLOOR_PLANE = "XY"


# ------------------------------------------------------------
# Circle settings
# ------------------------------------------------------------
#
# Vicon units are normally millimetres.
# 10 cm diameter = 100 mm diameter = 50 mm radius.
#
# TARGET_MODE options:
#   "fixed"          -> use CIRCLE_CENTER_X_MM, CIRCLE_CENTER_Y_MM
#   "relative_start" -> create the circle relative to the starting Vicon position
#
# If you have a marked circle on the floor, use "fixed".
# If you just want the chariot to start anywhere and make a circle nearby,
# use "relative_start".

TARGET_MODE = "fixed"

CIRCLE_CENTER_X_MM = 0.0
CIRCLE_CENTER_Y_MM = 0.0

RELATIVE_CENTER_OFFSET_X_MM = 0.0
RELATIVE_CENTER_OFFSET_Y_MM = 350.0

CIRCLE_DIAMETER_MM = 100.0
CIRCLE_RADIUS_MM = CIRCLE_DIAMETER_MM / 2.0

ORBIT_CLOCKWISE = False


# ------------------------------------------------------------
# Mission settings
# ------------------------------------------------------------

CONTROL_DT_S = 0.12
MISSION_TIME_S = 180.0

ARRIVAL_TOLERANCE_MM = 18.0
ORBIT_TOLERANCE_MM = 25.0

PRINT_STATUS_EVERY_S = 0.4


# ------------------------------------------------------------
# Chariot-safe motion settings
# ------------------------------------------------------------

APPROACH_SPEED = 34
ORBIT_SPEED = 20
RECOVERY_SPEED = 26

MIN_MOVING_SPEED = 14
MAX_SPEED = 42

MAX_TURN_RATE_DEG_S = 45.0
MAX_ACCEL_PER_S = 55.0
MAX_DECEL_PER_S = 90.0

COLLISION_ESCAPE_TIME_S = 0.9
COLLISION_ESCAPE_SPEED = 22


# ------------------------------------------------------------
# Calibration settings
# ------------------------------------------------------------

CALIBRATION_SPEED = 45
CALIBRATION_MAX_TIME_S = 2.2
CALIBRATION_MIN_DISPLACEMENT_MM = 45.0

# If actual movement is opposite to the commanded target direction,
# the program stops instead of continuing to run away.
WRONG_WAY_DOT_LIMIT = -0.35
WRONG_WAY_GRACE_TIME_S = 1.5


# ------------------------------------------------------------
# Circle controller tuning
# ------------------------------------------------------------

RADIAL_GAIN = 0.9
TANGENTIAL_GAIN = 0.65
LOOKAHEAD_ANGLE_DEG = 14.0

MIN_VECTOR_NORM = 1e-6


# ------------------------------------------------------------
# Basic maths
# ------------------------------------------------------------

def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def normalise_angle_180(angle: float) -> float:
    return (angle + 180.0) % 360.0 - 180.0


def normalise_angle_360(angle: float) -> float:
    return angle % 360.0


def angle_error_deg(target: float, current: float) -> float:
    return normalise_angle_180(target - current)


def vector_norm(x: float, y: float) -> float:
    return math.hypot(x, y)


def unit_vector(x: float, y: float) -> Tuple[float, float]:
    mag = math.hypot(x, y)

    if mag < MIN_VECTOR_NORM:
        return 0.0, 1.0

    return x / mag, y / mag


def world_vector_to_heading_deg(vx: float, vy: float) -> float:
    """
    Uses Sphero-style heading convention:
        0 deg   = +Y direction
        90 deg  = +X direction
        180 deg = -Y direction
        270 deg = -X direction
    """
    return math.degrees(math.atan2(vx, vy))


def sphero_heading_to_local_vector(heading_deg: float) -> Tuple[float, float]:
    """
    Local Sphero heading vector:
        heading 0   -> local +Y
        heading 90  -> local +X
    """
    rad = math.radians(heading_deg)
    return math.sin(rad), math.cos(rad)


# ------------------------------------------------------------
# Data classes
# ------------------------------------------------------------

@dataclass
class Pose2D:
    x_mm: float
    y_mm: float
    raw_x_mm: float
    raw_y_mm: float
    raw_z_mm: float
    occluded: bool = False


@dataclass
class MotionState:
    cmd_heading_deg: float = 0.0
    cmd_speed: float = 0.0
    collision_until: float = 0.0
    collision_heading_deg: float = 0.0


@dataclass
class HeadingCalibration:
    """
    v0 = measured Vicon-world unit vector when Sphero command heading is 0 deg
    v90 = measured Vicon-world unit vector when Sphero command heading is 90 deg
    """
    v0x: float
    v0y: float
    v90x: float
    v90y: float


# ------------------------------------------------------------
# Vicon
# ------------------------------------------------------------

def connect_vicon() -> ViconDataStream.Client:
    client = ViconDataStream.Client()

    print("Connecting to Vicon server...")
    client.Connect(VICON_SERVER)
    client.SetBufferSize(3)
    client.EnableSegmentData()

    print("Waiting for first Vicon frame...")

    for _ in range(100):
        client.GetFrame()
        time.sleep(0.02)

        try:
            client.GetSegmentGlobalTranslation(SUBJECT_NAME, SEGMENT_NAME)
            print("Vicon connected and subject visible.")
            return client
        except Exception:
            pass

    raise RuntimeError(
        f"Could not read Vicon subject '{SUBJECT_NAME}' / segment '{SEGMENT_NAME}'."
    )


def get_vicon_pose(client: ViconDataStream.Client) -> Pose2D:
    client.GetFrame()

    global_position = client.GetSegmentGlobalTranslation(SUBJECT_NAME, SEGMENT_NAME)
    position = global_position[0]

    raw_x = float(position[0])
    raw_y = float(position[1])
    raw_z = float(position[2])

    occluded = False

    if len(global_position) > 1:
        occluded = bool(global_position[1])

    if FLOOR_PLANE.upper() == "XZ":
        floor_x = raw_x
        floor_y = raw_z
    else:
        floor_x = raw_x
        floor_y = raw_y

    return Pose2D(
        x_mm=floor_x,
        y_mm=floor_y,
        raw_x_mm=raw_x,
        raw_y_mm=raw_y,
        raw_z_mm=raw_z,
        occluded=occluded,
    )


# ------------------------------------------------------------
# Sphero
# ------------------------------------------------------------

def safe_call(label: str, func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as exc:
        print(f"{label} failed: {type(exc).__name__}: {exc}")
        return None


def scan_for_sphero():
    print(f"Scanning for Sphero {SPHERO_NAME}...")

    toys = scanner.find_toys(toy_names=[SPHERO_NAME], timeout=SCAN_TIMEOUT_S)

    if toys:
        return toys[0]

    print(f"Could not find {SPHERO_NAME}. Visible toys:")

    visible = scanner.find_toys(timeout=SCAN_TIMEOUT_S)

    for toy in visible:
        print(f" - {toy.name}")

    return None


def connect_sphero():
    last_error = None

    for attempt in range(1, CONNECT_RETRIES + 1):
        print(f"Connecting to {SPHERO_NAME}, attempt {attempt}/{CONNECT_RETRIES}...")

        toy = scan_for_sphero()

        if toy is None:
            time.sleep(CONNECT_RETRY_DELAY_S)
            continue

        try:
            api = SpheroEduAPI(toy)
            api.__enter__()
            print(f"Connected to {toy.name}.")
            return toy, api

        except Exception as exc:
            last_error = exc
            print(f"Connection failed: {type(exc).__name__}: {exc}")
            time.sleep(CONNECT_RETRY_DELAY_S)

    raise RuntimeError(f"Could not connect to {SPHERO_NAME}. Last error: {last_error}")


def stop_sphero(api, motion: Optional[MotionState] = None) -> None:
    safe_call("set_speed(0)", api.set_speed, 0)
    safe_call("stop_roll", api.stop_roll)

    if motion is not None:
        motion.cmd_speed = 0.0


def set_sphero_motion_direct(api, heading_deg: float, speed: float) -> None:
    safe_call("set_heading", api.set_heading, int(round(heading_deg)) % 360)
    safe_call("set_speed", api.set_speed, int(round(speed)))


# ------------------------------------------------------------
# Vicon displacement calibration
# ------------------------------------------------------------

def measure_displacement_for_heading(
    api,
    client: ViconDataStream.Client,
    sphero_heading_deg: float,
    label: str,
) -> Tuple[float, float]:
    """
    Commands the Sphero to move in one heading and measures actual Vicon displacement.
    This is the correct way to learn how Sphero headings map to Vicon-world movement.
    """

    print(f"Calibration move: heading {sphero_heading_deg:.0f} deg ({label})")

    stop_sphero(api)
    time.sleep(0.5)

    start_pose = get_vicon_pose(client)

    set_sphero_motion_direct(api, sphero_heading_deg, CALIBRATION_SPEED)

    start_time = time.time()
    last_pose = start_pose

    while time.time() - start_time < CALIBRATION_MAX_TIME_S:
        time.sleep(0.08)
        last_pose = get_vicon_pose(client)

        dx = last_pose.x_mm - start_pose.x_mm
        dy = last_pose.y_mm - start_pose.y_mm

        if math.hypot(dx, dy) >= CALIBRATION_MIN_DISPLACEMENT_MM:
            break

    stop_sphero(api)
    time.sleep(0.5)

    end_pose = get_vicon_pose(client)

    dx = end_pose.x_mm - start_pose.x_mm
    dy = end_pose.y_mm - start_pose.y_mm

    displacement = math.hypot(dx, dy)

    print(
        f"  displacement = ({dx:.1f}, {dy:.1f}) mm, "
        f"magnitude = {displacement:.1f} mm"
    )

    if displacement < CALIBRATION_MIN_DISPLACEMENT_MM:
        raise RuntimeError(
            f"Calibration displacement too small for heading {sphero_heading_deg}. "
            f"Got {displacement:.1f} mm. Increase CALIBRATION_SPEED or check the chariot."
        )

    ux, uy = unit_vector(dx, dy)
    return ux, uy


def calibrate_heading_mapping(api, client: ViconDataStream.Client) -> HeadingCalibration:
    """
    Learns the world movement vectors for Sphero heading 0 and heading 90.

    This replaces the unreliable old method that used Vicon yaw.
    """

    print("Starting Vicon displacement heading calibration.")
    print("The chariot will move twice: heading 0, then heading 90.")

    safe_call("calibration LED", api.set_main_led, Color(255, 255, 0))
    safe_call("calibration matrix", api.set_matrix_character, "K", Color(255, 255, 0))

    v0x, v0y = measure_displacement_for_heading(api, client, 0.0, "Sphero forward")
    v90x, v90y = measure_displacement_for_heading(api, client, 90.0, "Sphero right")

    dot = v0x * v90x + v0y * v90y

    print(
        "Calibration result:\n"
        f"  heading 0  world vector = ({v0x:.3f}, {v0y:.3f})\n"
        f"  heading 90 world vector = ({v90x:.3f}, {v90y:.3f})\n"
        f"  dot product = {dot:.3f}"
    )

    if abs(dot) > 0.65:
        print(
            "Warning: calibration vectors are not close to perpendicular. "
            "This can happen if the chariot slips or cannot move cleanly."
        )

    return HeadingCalibration(v0x=v0x, v0y=v0y, v90x=v90x, v90y=v90y)


def world_vector_to_sphero_heading(
    vx: float,
    vy: float,
    calibration: HeadingCalibration,
) -> float:
    """
    Convert desired Vicon-world vector into Sphero command heading.

    World vector is represented as:
        desired_world ≈ cos(h) * v0 + sin(h) * v90

    Therefore:
        h = atan2(component_along_v90, component_along_v0)
    """

    # Matrix:
    # [vx] = [v0x v90x] [a]
    # [vy]   [v0y v90y] [b]
    #
    # where a ≈ cos(h), b ≈ sin(h)

    det = calibration.v0x * calibration.v90y - calibration.v90x * calibration.v0y

    if abs(det) < 1e-6:
        raise RuntimeError("Invalid heading calibration matrix. Determinant too small.")

    a = (vx * calibration.v90y - calibration.v90x * vy) / det
    b = (calibration.v0x * vy - vx * calibration.v0y) / det

    heading = math.degrees(math.atan2(b, a))
    return normalise_angle_360(heading)


def sphero_heading_to_world_vector(
    heading_deg: float,
    calibration: HeadingCalibration,
) -> Tuple[float, float]:
    local_x, local_y = sphero_heading_to_local_vector(heading_deg)

    # local_y corresponds to heading 0 vector.
    # local_x corresponds to heading 90 vector.
    wx = local_y * calibration.v0x + local_x * calibration.v90x
    wy = local_y * calibration.v0y + local_x * calibration.v90y

    return unit_vector(wx, wy)


# ------------------------------------------------------------
# Circle controller
# ------------------------------------------------------------

def compute_desired_world_vector(
    pose: Pose2D,
    centre_x_mm: float,
    centre_y_mm: float,
    phase: str,
) -> Tuple[float, float, float, float, float]:
    """
    Returns:
        vx, vy, desired_speed, radial_error_mm, radius_now_mm
    """

    dx = pose.x_mm - centre_x_mm
    dy = pose.y_mm - centre_y_mm

    radius_now = math.hypot(dx, dy)

    if radius_now < MIN_VECTOR_NORM:
        radial_out_x, radial_out_y = 1.0, 0.0
    else:
        radial_out_x = dx / radius_now
        radial_out_y = dy / radius_now

    radial_error = radius_now - CIRCLE_RADIUS_MM

    if phase == "APPROACH":
        # Nearest point on the desired circle.
        target_x = centre_x_mm + CIRCLE_RADIUS_MM * radial_out_x
        target_y = centre_y_mm + CIRCLE_RADIUS_MM * radial_out_y

        vx = target_x - pose.x_mm
        vy = target_y - pose.y_mm

        if math.hypot(vx, vy) < 4.0:
            # Already near enough; begin orbit direction.
            phase = "ORBIT"

        else:
            desired_speed = APPROACH_SPEED

            if abs(radial_error) < 70.0:
                desired_speed = RECOVERY_SPEED

            return vx, vy, desired_speed, radial_error, radius_now

    # Orbit controller.
    # Tangential vector moves around the circle.
    # Radial vector corrects inside/outside error.

    if ORBIT_CLOCKWISE:
        tangent_x = radial_out_y
        tangent_y = -radial_out_x
        lookahead_sign = -1.0
    else:
        tangent_x = -radial_out_y
        tangent_y = radial_out_x
        lookahead_sign = 1.0

    angle = math.atan2(dy, dx)
    lookahead_angle = angle + lookahead_sign * math.radians(LOOKAHEAD_ANGLE_DEG)

    lookahead_x = centre_x_mm + CIRCLE_RADIUS_MM * math.cos(lookahead_angle)
    lookahead_y = centre_y_mm + CIRCLE_RADIUS_MM * math.sin(lookahead_angle)

    lookahead_vx = lookahead_x - pose.x_mm
    lookahead_vy = lookahead_y - pose.y_mm

    # If outside the circle, radial_error positive -> pull inward.
    # If inside the circle, radial_error negative -> push outward.
    radial_correction_x = -RADIAL_GAIN * radial_error * radial_out_x
    radial_correction_y = -RADIAL_GAIN * radial_error * radial_out_y

    vx = (
        TANGENTIAL_GAIN * CIRCLE_RADIUS_MM * tangent_x
        + radial_correction_x
        + 0.25 * lookahead_vx
    )

    vy = (
        TANGENTIAL_GAIN * CIRCLE_RADIUS_MM * tangent_y
        + radial_correction_y
        + 0.25 * lookahead_vy
    )

    if abs(radial_error) > ORBIT_TOLERANCE_MM:
        desired_speed = RECOVERY_SPEED
    else:
        desired_speed = ORBIT_SPEED

    return vx, vy, desired_speed, radial_error, radius_now


def apply_chariot_safe_motion(
    api,
    motion: MotionState,
    desired_sphero_heading_deg: float,
    desired_speed: float,
    dt: float,
) -> None:
    now = time.time()

    if now < motion.collision_until:
        desired_sphero_heading_deg = motion.collision_heading_deg
        desired_speed = COLLISION_ESCAPE_SPEED

    desired_sphero_heading_deg = normalise_angle_360(desired_sphero_heading_deg)

    heading_error = abs(angle_error_deg(desired_sphero_heading_deg, motion.cmd_heading_deg))

    # Slow down before sharp heading changes.
    if heading_error > 120:
        desired_speed *= 0.15
    elif heading_error > 85:
        desired_speed *= 0.30
    elif heading_error > 55:
        desired_speed *= 0.50
    elif heading_error > 35:
        desired_speed *= 0.70

    if desired_speed > 0:
        desired_speed = clamp(desired_speed, MIN_MOVING_SPEED, MAX_SPEED)
    else:
        desired_speed = 0.0

    max_step = MAX_TURN_RATE_DEG_S * dt

    heading_step = clamp(
        angle_error_deg(desired_sphero_heading_deg, motion.cmd_heading_deg),
        -max_step,
        max_step,
    )

    new_heading = normalise_angle_360(motion.cmd_heading_deg + heading_step)

    if desired_speed > motion.cmd_speed:
        new_speed = min(desired_speed, motion.cmd_speed + MAX_ACCEL_PER_S * dt)
    else:
        new_speed = max(desired_speed, motion.cmd_speed - MAX_DECEL_PER_S * dt)

    motion.cmd_heading_deg = new_heading
    motion.cmd_speed = new_speed

    safe_call("set_heading", api.set_heading, int(round(new_heading)) % 360)
    safe_call("set_speed", api.set_speed, int(round(new_speed)))


# ------------------------------------------------------------
# Safety: wrong-way detection
# ------------------------------------------------------------

def check_wrong_way(
    previous_pose: Optional[Pose2D],
    current_pose: Pose2D,
    desired_world_vx: float,
    desired_world_vy: float,
) -> Optional[float]:
    """
    Returns dot product between actual movement direction and desired direction.

    Positive dot = moving generally the right way.
    Negative dot = moving opposite the desired direction.
    """

    if previous_pose is None:
        return None

    actual_dx = current_pose.x_mm - previous_pose.x_mm
    actual_dy = current_pose.y_mm - previous_pose.y_mm

    actual_mag = math.hypot(actual_dx, actual_dy)
    desired_mag = math.hypot(desired_world_vx, desired_world_vy)

    if actual_mag < 4.0 or desired_mag < MIN_VECTOR_NORM:
        return None

    ax = actual_dx / actual_mag
    ay = actual_dy / actual_mag

    dx = desired_world_vx / desired_mag
    dy = desired_world_vy / desired_mag

    return ax * dx + ay * dy


# ------------------------------------------------------------
# Collision handler
# ------------------------------------------------------------

def make_collision_handler(motion: MotionState):
    def on_collision(api):
        print("Collision detected. Escaping briefly.")

        motion.collision_until = time.time() + COLLISION_ESCAPE_TIME_S
        motion.collision_heading_deg = normalise_angle_360(
            motion.cmd_heading_deg + 135.0
        )

        safe_call("collision LED", api.set_main_led, Color(255, 0, 0))
        safe_call("collision matrix", api.set_matrix_character, "X", Color(255, 0, 0))

    return on_collision


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main() -> None:
    client = None
    api = None

    try:
        client = connect_vicon()
        toy, api = connect_sphero()

        motion = MotionState()

        safe_call(
            "register collision",
            api.register_event,
            EventType.on_collision,
            make_collision_handler(motion),
        )

        safe_call("main LED", api.set_main_led, Color(0, 80, 255))
        safe_call("matrix", api.set_matrix_character, "C", Color(0, 80, 255))

        print("Place the chariot safely. Starting in 3 seconds...")
        time.sleep(3.0)

        start_pose = get_vicon_pose(client)

        if TARGET_MODE == "relative_start":
            centre_x_mm = start_pose.x_mm + RELATIVE_CENTER_OFFSET_X_MM
            centre_y_mm = start_pose.y_mm + RELATIVE_CENTER_OFFSET_Y_MM
        else:
            centre_x_mm = CIRCLE_CENTER_X_MM
            centre_y_mm = CIRCLE_CENTER_Y_MM

        print(
            f"Circle centre: ({centre_x_mm:.1f}, {centre_y_mm:.1f}) mm, "
            f"diameter: {CIRCLE_DIAMETER_MM:.1f} mm, "
            f"radius: {CIRCLE_RADIUS_MM:.1f} mm"
        )

        calibration = calibrate_heading_mapping(api, client)

        motion.cmd_heading_deg = 0.0
        motion.cmd_speed = 0.0

        phase = "APPROACH"
        mission_start = time.time()
        last_loop = mission_start
        last_print = 0.0

        previous_pose = None
        wrong_way_start = None

        safe_call("mission LED", api.set_main_led, Color(0, 255, 80))
        safe_call("mission matrix", api.set_matrix_character, "G", Color(0, 255, 80))

        print("Mission started. Press Ctrl+C to stop.")

        while time.time() - mission_start < MISSION_TIME_S:
            loop_start = time.time()
            dt = clamp(loop_start - last_loop, 0.04, 0.25)
            last_loop = loop_start

            pose = get_vicon_pose(client)

            if pose.occluded:
                print("Vicon subject occluded. Stopping until visible again.")
                stop_sphero(api, motion)
                time.sleep(0.2)
                previous_pose = None
                continue

            desired_vx, desired_vy, desired_speed, radial_error, radius_now = (
                compute_desired_world_vector(
                    pose,
                    centre_x_mm,
                    centre_y_mm,
                    phase,
                )
            )

            desired_mag = math.hypot(desired_vx, desired_vy)

            if desired_mag < MIN_VECTOR_NORM:
                desired_vx, desired_vy = 0.0, 1.0

            desired_sphero_heading = world_vector_to_sphero_heading(
                desired_vx,
                desired_vy,
                calibration,
            )

            if phase == "APPROACH" and abs(radial_error) <= ARRIVAL_TOLERANCE_MM:
                phase = "ORBIT"
                safe_call("orbit LED", api.set_main_led, Color(0, 255, 80))
                safe_call("orbit matrix", api.set_matrix_character, "O", Color(0, 255, 80))
                print("Reached circular track. Switching to ORBIT mode.")

            direction_dot = check_wrong_way(
                previous_pose,
                pose,
                desired_vx,
                desired_vy,
            )

            if direction_dot is not None and direction_dot < WRONG_WAY_DOT_LIMIT:
                if wrong_way_start is None:
                    wrong_way_start = time.time()

                if time.time() - wrong_way_start > WRONG_WAY_GRACE_TIME_S:
                    stop_sphero(api, motion)
                    safe_call("wrong-way LED", api.set_main_led, Color(255, 0, 0))
                    safe_call("wrong-way matrix", api.set_matrix_character, "!", Color(255, 0, 0))

                    raise RuntimeError(
                        "Wrong-way detected. Vicon shows the chariot moving opposite "
                        "the desired direction. Re-run calibration, check FLOOR_PLANE, "
                        "or check that the Vicon subject is attached to the chariot "
                        "you are controlling."
                    )
            else:
                wrong_way_start = None

            apply_chariot_safe_motion(
                api,
                motion,
                desired_sphero_heading,
                desired_speed,
                dt,
            )

            if loop_start - last_print >= PRINT_STATUS_EVERY_S:
                last_print = loop_start

                if direction_dot is None:
                    dot_text = "n/a"
                else:
                    dot_text = f"{direction_dot:+.2f}"

                print(
                    f"{phase} | "
                    f"pos=({pose.x_mm:.1f}, {pose.y_mm:.1f}) mm | "
                    f"radius={radius_now:.1f} mm | "
                    f"target_radius={CIRCLE_RADIUS_MM:.1f} mm | "
                    f"radial_error={radial_error:+.1f} mm | "
                    f"sphero_heading={desired_sphero_heading:.1f} deg | "
                    f"speed={motion.cmd_speed:.1f} | "
                    f"dir_dot={dot_text}"
                )

            previous_pose = pose

            sleep_time = CONTROL_DT_S - (time.time() - loop_start)

            if sleep_time > 0:
                time.sleep(sleep_time)

        print("Mission time complete.")

    except KeyboardInterrupt:
        print("Interrupted by user.")

    except ViconDataStream.DataStreamException as exc:
        print("Vicon Datastream Error:", exc)

    except Exception as exc:
        print(f"Error: {type(exc).__name__}: {exc}")

    finally:
        if api is not None:
            print("Stopping Sphero.")

            try:
                api.set_speed(0)
                api.stop_roll()
            except Exception:
                pass

            try:
                api.set_main_led(Color(255, 255, 255))
                api.set_matrix_character("S", Color(255, 255, 255))
            except Exception:
                pass

            try:
                api.__exit__(None, None, None)
            except Exception:
                pass

        if client is not None:
            try:
                client.Disconnect()
            except Exception:
                pass

        print("Program ended safely.")


if __name__ == "__main__":
    main()