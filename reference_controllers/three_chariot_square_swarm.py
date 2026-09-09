"""
Three-chariot Vicon-referenced square swarm reference controller.

This file preserves the feature-rich controller architecture as a standalone hardware script.
All site-specific network addresses and robot identifiers have been replaced with local
configuration placeholders. Start with --dry-run before enabling real hardware.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import os
import math
import signal
import time
import queue
import threading
import multiprocessing as mp
from collections import deque
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


# =============================================================================
# Configuration
# =============================================================================

CONTROLLER_VERSION = "PUBLIC-THREE-CHARIOT-SQUARE-SWARM v1.0"

VICON_SERVER = os.getenv("VICON_SERVER", "127.0.0.1:801")
FLOOR_PLANE = "XY"
YAW_EULER_INDEX = 2
YAW_SIGN = 1.0
YAW_OFFSET_DEG = 0.0

ROBOT_CONFIGS = [
    (os.getenv("SPHERO_1_NAME", "YOUR_DEVICE_1"), os.getenv("VICON_1_SUBJECT", "Robot 1"), os.getenv("VICON_1_SEGMENT", "Robot 1")),
    (os.getenv("SPHERO_2_NAME", "YOUR_DEVICE_2"), os.getenv("VICON_2_SUBJECT", "Robot 2"), os.getenv("VICON_2_SEGMENT", "Robot 2")),
    (os.getenv("SPHERO_3_NAME", "YOUR_DEVICE_3"), os.getenv("VICON_3_SUBJECT", "Robot 3"), os.getenv("VICON_3_SEGMENT", "Robot 3")),
]

# Site-specific workspace limits belong in local environment/configuration.
# The defaults below define a generic 4 m x 4 m documentation workspace only.
VICON_AO_X_MIN_MM = float(os.getenv("AO_X_MIN_MM", "-2000"))
VICON_AO_X_MAX_MM = float(os.getenv("AO_X_MAX_MM", "2000"))
VICON_AO_Y_MIN_MM = float(os.getenv("AO_Y_MIN_MM", "-2000"))
VICON_AO_Y_MAX_MM = float(os.getenv("AO_Y_MAX_MM", "2000"))
BOUNDARY_EXTENSION_MM = float(os.getenv("BOUNDARY_EXTENSION_MM", "0"))
AO_X_MIN_MM = VICON_AO_X_MIN_MM - BOUNDARY_EXTENSION_MM
AO_X_MAX_MM = VICON_AO_X_MAX_MM + BOUNDARY_EXTENSION_MM
AO_Y_MIN_MM = VICON_AO_Y_MIN_MM - BOUNDARY_EXTENSION_MM
AO_Y_MAX_MM = VICON_AO_Y_MAX_MM + BOUNDARY_EXTENSION_MM
AO_CX = 0.5 * (AO_X_MIN_MM + AO_X_MAX_MM)
AO_CY = 0.5 * (AO_Y_MIN_MM + AO_Y_MAX_MM)

# Square is deliberately small and central.  Individual robots normally stay
# hundreds of mm away from the recovery band.
DEFAULT_SIDE_MM = 1600.0
MIN_SIDE_MM = 1200.0
MAX_SIDE_MM = 1800.0

# -------------------------------------------------------------------------
# PHYSICAL CHARIOT FOOTPRINT
# -------------------------------------------------------------------------
# Reference geometry: each chariot is approximately a 200 x 140 mm rectangle,
# centred on the Vicon centroid.  The long axis is assumed to follow Vicon yaw.
# Collision logic uses an additional safety halo around the real body.
BODY_LENGTH_MM = 200.0
BODY_WIDTH_MM = 140.0
BODY_HALF_LENGTH_MM = 0.5 * BODY_LENGTH_MM
BODY_HALF_WIDTH_MM = 0.5 * BODY_WIDTH_MM
BODY_SAFETY_MARGIN_MM = 10.0
BODY_WALL_MARGIN_MM = 30.0

# Vicon segment axes are not guaranteed to use the same body-longitudinal axis
# on every subject.  Reference observation shows Chariot 3's segment yaw axis is
# rotated 90 deg relative to its physical 20 x 14 cm rectangle.  This offset is
# ONLY for footprint geometry/digital twin; steering still uses the calibrated
# Sphero->Vicon travelling-course map.
BODY_YAW_OFFSET_DEG = {name: 90.0 for name, _subject, _segment in ROBOT_CONFIGS}

# Swarm-like waypoint capture: the group does not have to settle exactly at a
# mathematical point.  Entering the capture disc is enough to hand off to the
# next goal while the formation controller keeps the bodies together.
WAYPOINT_CAPTURE_RADIUS_MM = 210.0
WAYPOINT_MIN_FORM_RMS_MM = 430.0

# Formation must be feasible for the PHYSICAL boxes at arbitrary yaw.  A
# an earlier revision targets a compact physical triangle: 205-mm formation radius gives
# sqrt(3)*205 ~= 355 mm centre-to-centre.  This is close enough to look like
# one swarm, while the footprint/SAT controller still reserves space for the
# 200x140 mm bodies to rotate without contact.
FORMATION_RADIUS_MM = 200.0
FORMATION_KP = 2.20
FORMATION_KD = 1.25
FORMATION_CAPTURE_RMS_MM = 125.0
FORMATION_RUN_BAD_RMS_MM = 185.0
FORMATION_REFORM_RMS_MM = 360.0
FORMATION_STABLE_S = 0.18

# Footprint-to-footprint safety clearances (after the 25 mm safety halo is
# already included in each rectangle).  Positive = separated, zero = touching,
# negative = padded rectangles overlap.
BODY_CLEAR_SOFT_MM = 30.0
BODY_CLEAR_STRONG_MM = 10.0
BODY_CLEAR_CRITICAL_MM = -6.0
BODY_CLEAR_EXTREME_MM = -18.0
BODY_SEP_GAIN = 1.15
PREDICT_HORIZON_S = 0.22
PREDICT_BODY_CLEAR_SOFT_MM = 0.0
PREDICT_GAIN = 0.75

# Boundary handling now uses BODY edge clearance, not centroid edge clearance.
# The box footprint + wall margin is therefore already accounted for.
BOUNDARY_SOFT_MM = 260.0
RECENTER_TRIGGER_MM = 170.0
BOUNDARY_STRONG_MM = 110.0
BOUNDARY_CRITICAL_MM = 55.0
BOUNDARY_EXTREME_MM = 15.0
RECENTER_RELEASE_CLEARANCE_MM = 520.0
RECENTER_CENTROID_TOL_MM = 120.0
RECENTER_FORM_RMS_MM = 90.0
RECENTER_STABLE_S = 0.55

# Centroid square controller.
CENTROID_STRAIGHT_SPEED_MM_S = 220.0
CENTROID_CORNER_SPEED_MM_S = 85.0
CENTROID_CROSS_KP = 1.65
CENTROID_CROSS_KD = 0.80
CENTROID_BACKTRACK_KP = 0.55
CORNER_BLEND_MM = 180.0
CORNER_CAPTURE_MM = 70.0
CORNER_OVERSHOOT_MM = 60.0
PATH_ERROR_SLOW_MM = 120.0
PATH_ERROR_HARD_MM = 260.0

# Centre/formation acquisition.
FORM_CENTROID_KP = 1.25
FORM_CENTROID_MAX_MM_S = 210.0
GO_START_KP = 1.20
GO_START_MAX_MM_S = 280.0
RECENTER_CENTROID_KP = 1.35
RECENTER_MAX_MM_S = 260.0

# Rigid-group square controller.  One common Vicon centroid controller moves
# the whole swarm, while separate RELATIVE slot corrections preserve the
# triangle.  This prevents three independent point-target controllers from
# fighting each other.
GUIDE_CRUISE_MM_S = 185.0
GUIDE_CORNER_APPROACH_MM = 320.0
GUIDE_CORNER_MIN_MM_S = 48.0
GUIDE_MAX_LEAD_MM = 320.0
GUIDE_PAUSE_CENTROID_ERR_MM = 430.0
GUIDE_PAUSE_FORM_RMS_MM = 320.0
GUIDE_CORNER_CAPTURE_MM = 220.0
GUIDE_CORNER_STABLE_S = 0.10

GROUP_CENTROID_KP = 1.55
GROUP_CENTROID_KD = 0.82
GROUP_CENTROID_MAX_CORRECTION_MM_S = 300.0

# an earlier revision formation-riding controller.  All robots share one dominant translational
# command.  Individual slot repair is deliberately bounded around that shared
# motion instead of being allowed to become a second independent navigator.
REL_SLOT_KP = 2.05
REL_SLOT_KD = 1.35
REL_SLOT_MAX_CORRECTION_MM_S = 300.0
VELOCITY_CONSENSUS_K = 0.78
VELOCITY_CONSENSUS_MAX_MM_S = 125.0
NORMAL_SLOT_CORRECTION_MAX_MM_S = 155.0
STRETCHED_SLOT_CORRECTION_MAX_MM_S = 260.0
NORMAL_PERP_CORRECTION_MAX_MM_S = 115.0
NORMAL_ALONG_CORRECTION_MAX_MM_S = 105.0
MAX_ROBOT_HEADING_DEVIATION_FROM_SWARM_DEG = 34.0

# "Inertia" / command-shaping layer.  The requested world velocity is passed
# through a first-order lag plus acceleration limit before it is converted to a
# Sphero heading/speed.  Safety recovery uses the faster constants.
COMMAND_VECTOR_TAU_S = 0.26
RECOVERY_VECTOR_TAU_S = 0.12
COMMAND_VECTOR_ACCEL_MM_S2 = 700.0
RECOVERY_VECTOR_ACCEL_MM_S2 = 1350.0

HOME_CAPTURE_RMS_MM = 170.0
HOME_CENTROID_TOL_MM = 240.0
HOME_STABLE_S = 0.10

# Smooth transfer from HOME at (0,0) to the square perimeter.  v9 jumped the
# guide instantly from (0,0) to (0,-800), creating an ~800 mm error and causing
# immediate RECENTER.  ENTRY moves the virtual guide continuously instead.
ENTRY_TARGET_X_MM = 0.0
ENTRY_CRUISE_MM_S = 150.0
ENTRY_APPROACH_MM = 260.0
ENTRY_MIN_MM_S = 42.0
ENTRY_MAX_LEAD_MM = 340.0
ENTRY_PAUSE_FORM_RMS_MM = 320.0
ENTRY_CAPTURE_MM = 210.0
ENTRY_CAPTURE_FORM_RMS_MM = 430.0
ENTRY_STABLE_S = 0.06

TRANSIENT_OCCLUSION_PRINT_S = 1.0

# Command scaling and smoothness.
MM_S_PER_SPEED_CMD = 2.55
DEFAULT_MAX_SPEED_CMD = 170
MIN_MOVING_CMD = 78
MAX_HEADING_SLEW_DEG_S = 165.0
RECOVERY_HEADING_SLEW_DEG_S = 260.0
MAX_SPEED_RISE_PER_S = 520.0
MAX_SPEED_FALL_PER_S = 560.0
CONTROL_HZ = 60.0
COMMAND_HZ = 18.0
PRINT_HZ = 2.0

# BLE write suppression.  Sphero retains its last command, so sending every
# 1-degree / 1-speed-count change only adds latency and jitter.
BLE_HEADING_DEADBAND_DEG = 2.5
BLE_SPEED_DEADBAND_CMD = 4

# Loaded chariots sometimes need a short torque pulse to break static friction.
# This is used only when Vicon says a robot is nearly stationary while it has a
# meaningful position error; after breakaway, ordinary closed-loop speed resumes.
BREAKAWAY_CMD = 248
BREAKAWAY_DURATION_S = 0.13
BREAKAWAY_SPEED_THRESHOLD_MM_S = 30.0
BREAKAWAY_VECTOR_THRESHOLD_MM_S = 55.0

# v22 stiction + auto-advance controller.  A loaded chariot may sit motionless at ordinary
# speed commands.  Detect that from Vicon displacement, issue ONE short torque
# pulse along the already-constrained square heading, then maintain a modest
# rolling floor so static friction is not encountered again immediately.
STICTION_DETECT_S = 0.24
STICTION_MOVE_EPS_MM = 6.0
STICTION_COOLDOWN_S = 0.36
STICTION_ROLL_ASSIST_S = 0.55
STICTION_KICK_MIN_CMD = 235.0
STICTION_KICK_MAX_CMD = 255.0
STICTION_KICK_STEP_CMD = 2.0
STICTION_ROLLING_FLOOR_DEFAULT = 54.0
STICTION_ROLLING_FLOOR_MIN = 42.0
STICTION_ROLLING_FLOOR_MAX = 72.0
STICTION_TERMINAL_KICK_CMD = 160.0
STICTION_TERMINAL_KICK_S = 0.085
STICTION_TERMINAL_KICK_MIN_REMAIN_MM = 100.0
STICTION_TERMINAL_KICK_MAX_REMAIN_MM = 220.0

# Vicon-yaw safety caps.  Position control determines desired direction; yaw is
# used to prevent full-power motion while the physical chariot points elsewhere.
YAW_CAP_35 = 185
YAW_CAP_60 = 135
YAW_CAP_90 = 95
YAW_CAP_120 = 72
WHIP_YAW_RATE_DEG_S = 270.0
WHIP_SPEED_CAP = 110

# Velocity estimator + mission pose sanity filter.
VEL_WINDOW_S = 0.16
HISTORY_KEEP_S = 0.55
UNIQUE_POS_EPS_MM = 0.10
STATIONARY_AFTER_S = 0.18
YAW_RATE_TC_S = 0.10

# A loaded Chariot cannot teleport by ~1 m between Vicon frames.  Reject
# impossible pose jumps before they reach path/formation logic.  The threshold
# grows modestly with frame interval but is capped so a persistent false segment
# cannot become valid merely because time elapsed.
VICON_JUMP_BASE_MM = 75.0
VICON_MAX_PLAUSIBLE_SPEED_MM_S = 1250.0
# reference: the control/BLE loop can occasionally take close to a second.  The
# plausibility envelope therefore scales with the *real elapsed time* instead of
# saturating after 0.20 s.  Short-frame teleport glitches are still rejected.
VICON_JUMP_DT_CAP_S = 1.50
# A single occluded Vicon frame is common and should not tear down a good run.
VICON_OCCLUSION_GRACE_S = 0.28
# Rejected visible poses are allowed a little longer because a delayed control
# cycle can legitimately create a large displacement from the last accepted pose.
VICON_STALE_STOP_S = 0.90
# Reacquisition is based on several mutually-consistent NEW frames, not distance
# back to a stale pose.  This removes the old >520 mm permanent-recovery deadlock.
VICON_REACQUIRE_CONSISTENCY_BASE_MM = 45.0
VICON_REACQUIRE_MAX_SPEED_MM_S = 1500.0
VICON_REACQUIRE_DT_CAP_S = 0.30
VICON_REACQUIRE_AO_MARGIN_MM = 350.0
VICON_REACQUIRE_GOOD_SAMPLES = 4

# Per-robot displacement calibration.
# Chariots need a decisive breakaway command.  We therefore use full Sphero
# power for a fixed observation window and let Vicon measure the resulting
# world displacement.  Two strong orthogonal samples are normally enough.
CAL_PRIMARY_HEADINGS = (0.0, 90.0)
CAL_FALLBACK_HEADINGS = (180.0, 270.0, 45.0, 135.0, 225.0, 315.0)
CAL_SPEED_CMD = 255
CAL_DRIVE_TIME_S = 2.0
# The 2 s window is the desired test.  Vicon may terminate a leg early only to
# protect the AO if the robot has already travelled a large distance.
CAL_MAX_MOVE_MM = 520.0
CAL_BOUNDARY_STOP_CLEARANCE_MM = 300.0
CAL_REQUIRED_CLEARANCE_MM = 620.0
CAL_HARD_MIN_CLEARANCE_MM = 240.0
# Full-power legs should normally be large.  Retain moderate translations, but
# weight long translations more heavily in the heading fit.
CAL_MIN_SAMPLE_MOVE_MM = 35.0
CAL_GOOD_SAMPLE_MOVE_MM = 120.0
CAL_MIN_DET = 0.58
CAL_MAX_FIT_RMS_DEG = 28.0
CAL_MIN_NONCOLLINEAR_SIN = 0.42
CAL_SETTLE_SPEED_MM_S = 45.0
CAL_SETTLE_HOLD_S = 0.18
CAL_SETTLE_MAX_S = 1.4
CAL_FILE = "three_chariot_vicon_heading_calibration_reference.json"

# After displacement calibration, verify the *actual travelling course* using
# Vicon.  Chariot mechanics can rotate the realised travel direction by tens of
# degrees even when the static Sphero heading map is mathematically correct.
COURSE_VERIFY_SPEED_CMD = 220
COURSE_VERIFY_DRIVE_S = 1.55
COURSE_VERIFY_MAX_MOVE_MM = 430.0
COURSE_VERIFY_EDGE_GUARD_MM = 430.0
COURSE_VERIFY_MIN_MOVE_MM = 110.0
COURSE_VERIFY_GOOD_ERR_DEG = 12.0
COURSE_VERIFY_MAX_TRIES = 4
COURSE_TRIM_STEP_MAX_DEG = 85.0
COURSE_TRIM_RUNTIME_RATE_DEG_S = 32.0
COURSE_WINDOW_MIN_S = 0.22
COURSE_WINDOW_MAX_S = 0.48
COURSE_MIN_DISPLACEMENT_MM = 24.0
COURSE_VERIFY_BURN_IN_S = 0.32
COURSE_VERIFY_MEASURE_S = 0.95
COURSE_VERIFY_REQUIRED_PASSES = 2
COURSE_VERIFY_SECONDARY_TOL_DEG = 18.0
COURSE_RUNTIME_TRIM_BAND_DEG = 28.0
COURSE_RUNTIME_BAD_ERR_DEG = 38.0
COURSE_RUNTIME_SPEED_CAP = 92
COURSE_RUNTIME_STABLE_CMD_S = 0.32

# Vicon line-corridor square follower.  The target is tied to measured progress
# along the current side, so it cannot orbit ahead of the physical swarm.
LINE_LOOKAHEAD_MM = 230.0
LINE_CRUISE_MM_S = 165.0
LINE_CORNER_SPEED_MM_S = 72.0
LINE_CORNER_APPROACH_MM = 420.0
LINE_CROSS_SLOW_MM = 140.0
LINE_CROSS_HARD_MM = 330.0
LINE_CAPTURE_RADIUS_MM = 185.0
# Keep the physical swarm together while it follows each line.  Forward
# translation is automatically reduced as formation RMS grows; this lets
# stragglers catch up instead of allowing a leader to run the square alone.
FORMATION_FLOW_FULL_RMS_MM = 85.0
FORMATION_FLOW_SLOW_RMS_MM = 150.0
FORMATION_FLOW_HOLD_RMS_MM = 260.0
FORMATION_FLOW_MIN_SCALE = 0.04
BOUNDARY_HOLD_RELEASE_MARGIN_MM = 170.0
LINE_PASS_MARGIN_MM = 55.0
LINE_FORM_RMS_MAX_MM = 430.0

# v16 CENTROID-LOCKED FRENET FORMATION CONTROL.
# Each robot follows the same 1600-mm square translated by its fixed world-frame
# formation slot.  Centroid is diagnostic only and never generates steering.
RAIL_CRUISE_MM_S = 175.0
RAIL_CORNER_SPEED_MM_S = 68.0
RAIL_CORNER_APPROACH_MM = 360.0
RAIL_LOOKAHEAD_MM = 190.0
RAIL_CROSS_KP = 1.75
RAIL_CROSS_KD = 0.72
RAIL_CROSS_MAX_MM_S = 230.0
RAIL_SYNC_KP = 0.82
RAIL_SYNC_MAX_MM_S = 120.0
RAIL_PROGRESS_FULL_SPREAD_MM = 95.0
RAIL_PROGRESS_SLOW_SPREAD_MM = 210.0
RAIL_PROGRESS_HOLD_SPREAD_MM = 420.0
RAIL_FLOW_MIN = 0.16
RAIL_CORNER_CAPTURE_REMAINING_MM = 220.0
RAIL_CORNER_MAX_CROSS_MM = 280.0
RAIL_ENTRY_CAPTURE_REMAINING_MM = 210.0
RAIL_ENTRY_MAX_CROSS_MM = 260.0
RAIL_MAX_HEADING_DEVIATION_DEG = 55.0
RAIL_MAX_HEADING_DEVIATION_LARGE_CROSS_DEG = 72.0
RAIL_AHEAD_HOLD_MM = 270.0
RAIL_BEHIND_BOOST_MM = 220.0
RAIL_HOME_KP = 1.30
RAIL_HOME_KD = 0.78
RAIL_HOME_MAX_MM_S = 235.0
RAIL_HOME_CAPTURE_MM = 210.0
RAIL_HOME_ALL_MAX_MM = 265.0
RAIL_LEARNING_CROSS_MAX_MM = 120.0
RAIL_LEARNING_SPREAD_MAX_MM = 150.0
RAIL_SPEED_SCALE_RATE = 0.000020
RAIL_TRIM_RATE = 0.18
RAIL_TRIM_MAX_DEG = 2.0
RAIL_ERROR_EMA_TC_S = 2.8

# v16 hybrid square/formation controller.  The active side tangent is always the
# primary path direction.  Centroid feedback is used ONLY in the normal direction
# of that straight side, so it can pull the swarm onto the optimal centre line
# without creating circular/orbiting motion.  Along-track feedback synchronises
# all three robots around one actual group-progress coordinate.
FRENET_CRUISE_MM_S = 180.0
FRENET_CORNER_SPEED_MM_S = 58.0
FRENET_CORNER_APPROACH_MM = 260.0
FRENET_LOOKAHEAD_MM = 150.0
FRENET_CENTROID_CROSS_KP = 0.0
FRENET_CENTROID_CROSS_KD = 0.0
FRENET_REL_CROSS_KP = 1.05
FRENET_REL_CROSS_KD = 0.20
FRENET_CROSS_MAX_MM_S = 72.0
FRENET_SYNC_KP = 0.62
FRENET_SYNC_KD = 0.12
FRENET_SYNC_KI = 0.0
FRENET_SYNC_INTEGRAL_MAX_MM_S = 0.0
FRENET_SYNC_MAX_MM_S = 132.0
FRENET_REVERSE_MAX_MM_S = 0.0
FRENET_PROGRESS_FULL_SPREAD_MM = 65.0
FRENET_PROGRESS_SLOW_SPREAD_MM = 150.0
FRENET_PROGRESS_BAD_SPREAD_MM = 280.0
FRENET_MIN_BASE_MM_S = 70.0
FRENET_CENTROID_CROSS_SLOW_MM = 120.0
FRENET_CENTROID_CROSS_HARD_MM = 360.0
FRENET_CORNER_GROUP_REMAINING_MM = 155.0
FRENET_CORNER_MAX_SPREAD_MM = 175.0
FRENET_CORNER_MAX_CROSS_MM = 175.0
FRENET_ENTRY_GROUP_REMAINING_MM = 155.0
FRENET_ENTRY_MAX_SPREAD_MM = 180.0
FRENET_ENTRY_MAX_CROSS_MM = 185.0
FRENET_HEADING_DEVIATION_DEG = 24.0
FRENET_HEADING_DEVIATION_RECOVER_DEG = 34.0


# -------------------------------------------------------------------------
# v24 CONTINUOUS VIRTUAL-LEADER SWARM
# -------------------------------------------------------------------------
# There are NO waypoint holds in ENTRY/RUN.  The reference itself moves around
# the square continuously; robots track moving formation slots around it.
MOVING_ENTRY_SPEED_MM_S = 185.0
MOVING_CRUISE_MM_S = 215.0
MOVING_CORNER_SPEED_MM_S = 170.0
MOVING_CORNER_ZONE_MM = 240.0
MOVING_MIN_REFERENCE_SPEED_MM_S = 130.0
MOVING_MAX_REFERENCE_SPEED_MM_S = 240.0

# Moving-centroid path lock.  Along-track error changes pace, while normal error
# pulls the whole formation back to the active straight square segment.
MOVING_CENTROID_ALONG_KP = 0.42
MOVING_CENTROID_ALONG_KD = 0.16
MOVING_CENTROID_CROSS_KP = 1.00
MOVING_CENTROID_CROSS_KD = 0.24
MOVING_COMMON_FORWARD_MIN_MM_S = 0.0
MOVING_COMMON_FORWARD_MAX_MM_S = 280.0
MOVING_COMMON_CROSS_MAX_MM_S = 125.0

# Relative formation lock.  Fixed world-frame triangular slots mean that if
# these relative errors are small, the centroid automatically traces the central
# square and all three robots travel in formation.
MOVING_REL_ALONG_KP = 0.80
MOVING_REL_ALONG_KD = 0.18
MOVING_REL_CROSS_KP = 0.95
MOVING_REL_CROSS_KD = 0.20
MOVING_REL_ALONG_MAX_MM_S = 100.0
MOVING_REL_CROSS_MAX_MM_S = 105.0
MOVING_ROBOT_FORWARD_MIN_MM_S = 0.0
MOVING_ROBOT_FORWARD_MAX_MM_S = 300.0
MOVING_HEADING_CONE_DEG = 28.0
MOVING_RECOVERY_CONE_DEG = 38.0
MOVING_MIN_COMMAND_FLOOR = 42.0

# The virtual leader slows when the real centroid lags or the triangle stretches,
# but it NEVER waits for an exact goal/corner.  This is what eliminates
# CORNER_HOLD/ENTRY_HOLD and circling around static goal points.
MOVING_LAG_SOFT_MM = 180.0
MOVING_LAG_HARD_MM = 520.0
MOVING_FORM_SOFT_RMS_MM = 125.0
MOVING_FORM_HARD_RMS_MM = 300.0
MOVING_REF_MIN_SCALE = 0.64

# v24: the moving target is TETHERED to actual centroid progress instead of
# integrating freely in time.  This prevents the goal running away from, or
# falling far behind, the real swarm.
TETHER_LOOKAHEAD_MM = 235.0
TETHER_MAX_LEAD_MM = 310.0
TETHER_TURN_EARLY_MM = 125.0
TETHER_MAX_CENTROID_CROSS_MM = 420.0
TETHER_BAD_FORM_RMS_MM = 420.0

# v24 adaptive physical-speed loop.  A short high-torque pulse overcomes static
# friction; once rolling, Vicon speed closes the loop and per-robot gain is learned.
DRIVE_GAIN_DEFAULT_MM_S_PER_CMD = 3.0
DRIVE_GAIN_MIN = 1.1
DRIVE_GAIN_MAX = 7.0
DRIVE_GAIN_TC_S = 5.0
DRIVE_SPEED_KP_CMD_PER_MM_S = 0.055
DRIVE_SPEED_KI_CMD_PER_MM = 0.004
DRIVE_SPEED_I_MAX_CMD = 18.0
DRIVE_ROLLING_CMD_MIN = 40.0
DRIVE_ROLLING_CMD_MAX = 82.0
DRIVE_GAIN_LEARN_MIN_SPEED = 55.0
DRIVE_GAIN_LEARN_MAX_SPEED = 650.0

# Short-range collision bumper.  Formation tracking remains dominant.
MOVING_BUMPER_START_MM = 28.0
MOVING_BUMPER_OVERLAP_MM = -5.0
MOVING_BUMPER_CAP_MM_S = 90.0

# Online iterative learning control (ILC).  The square is repeated, so learning
# systematic per-side cross-track error is safer and more useful than a black-box
# model.  Feed-forward trims are tightly bounded and persist between runs.
PATH_ILC_FILE = "three_chariot_square_ilc_reference.json"
ILC_SIDE_COUNT = 5  # midpoint route has five directed segments
ILC_HEADING_TRIM_MAX_DEG = 7.0
ILC_CROSS_EMA_TC_S = 4.0
ILC_TRIM_ADAPT_TC_S = 14.0
ILC_TRIM_PER_MM_DEG = 0.025
ILC_CRUISE_SCALE_MIN = 0.92
ILC_CRUISE_SCALE_MAX = 1.12
ILC_CRUISE_ADAPT_UP_PER_S = 0.0025
ILC_CRUISE_ADAPT_DOWN_PER_S = 0.0040

# Per-robot learned formation feed-forward.
MOVING_LEARN_EMA_TC_S = 3.0
MOVING_SPEED_TRIM_PER_MM = 0.00035
MOVING_FORM_HEADING_PER_MM = 0.012
MOVING_FORM_HEADING_MAX_DEG = 3.5
MOVING_LEARN_BLEND_TC_S = 10.0

# v22 terminal plane / auto-advance gate.  Every robot must brake and HOLD at its
# own translated endpoint.  This prevents ENTRY or a square side from running
# through the corner while waiting for the other robots.
TERMINAL_SLOWDOWN_MM = 220.0
TERMINAL_HOLD_REMAINING_MM = 75.0
TERMINAL_HOLD_CROSS_MM = 190.0
TERMINAL_FORCE_STOP_PAST_MM = 8.0
TERMINAL_LOW_MIN_CMD = 34.0
TERMINAL_CREEP_MIN_CMD = 48.0
TERMINAL_FORWARD_GAIN = 0.80
TERMINAL_MAX_FORWARD_MM_S = 125.0
TERMINAL_HIGH_SPEED_MM_S = 240.0
TERMINAL_HIGH_SPEED_REMAINING_MM = 130.0

# v22 pragmatic stage acceptance.  The robots are loaded chariots with real
# static friction; once all three are physically close to their translated
# endpoint, continuing to fight for a few centimetres is counterproductive.
STAGE_ACCEPT_RADIUS_MM = 175.0
STAGE_HELD_ESCAPE_RADIUS_MM = 215.0
STAGE_ACCEPT_MAX_SPREAD_MM = 190.0
STAGE_ACCEPT_CENTER_CROSS_MM = 190.0
STAGE_ACCEPT_DWELL_S = 0.10
STAGE_HELD_DWELL_S = 0.18

# Persistent adaptation during clean square tracking only.
LEARNING_FILE = "three_chariot_swarm_learning_reference.json"
LEGACY_LEARNING_FILE = "three_chariot_swarm_learning_v25.json"
HEADING_BIAS_MAX_DEG = 175.0
HEADING_BIAS_RATE = 0.12         # fraction of course error learned per second-ish
SPEED_SCALE_MIN = 0.90
SPEED_SCALE_MAX = 1.12
SPEED_SCALE_RATE = 0.000090       # an earlier revision: learns persistent along-track formation lag
FORMATION_TRIM_MAX_DEG = 6.0
FORMATION_TRIM_RATE = 0.24
FORMATION_ERROR_EMA_TC_S = 2.2
LEARNING_SAVE_PERIOD_S = 6.0
LEARNING_MIN_SPEED_MM_S = 70.0
LEARNING_MAX_COURSE_ERR_DEG = 95.0

# Mission/logging.
DEFAULT_LAPS = 0                  # 0 = continuous
DEFAULT_TIMEOUT_S = 0.0           # 0 = no timeout
LOG_FILE = "three_chariot_square_swarm_reference_log.csv"
SCAN_TIMEOUT_S = 14

# Live controller digital twin. Uses only Python/Tkinter (no extra package).
DIGITAL_TWIN_HZ = 10.0
DIGITAL_TWIN_WIDTH = 1820
DIGITAL_TWIN_HEIGHT = 1000
DIGITAL_TWIN_SIDEBAR_PX = 520
DIGITAL_TWIN_MARGIN_PX = 34
DIGITAL_TWIN_TRAIL_POINTS = 140
LOG_FLUSH_PERIOD_S = 1.5
DIGITAL_TWIN_ACTUAL_VEL_HORIZON_S = 0.65
DIGITAL_TWIN_CMD_VECTOR_MM = 260.0


# =============================================================================
# Utility
# =============================================================================

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def wrap360(a: float) -> float:
    return a % 360.0


def wrap180(a: float) -> float:
    return (a + 180.0) % 360.0 - 180.0


def unit(x: float, y: float) -> Tuple[float, float]:
    d = math.hypot(x, y)
    if d < 1e-9:
        return 0.0, 0.0
    return x / d, y / d


def heading_of(x: float, y: float) -> float:
    return wrap360(math.degrees(math.atan2(y, x)))


def angle_step(cur: float, target: float, max_step: float) -> float:
    return wrap360(cur + clamp(wrap180(target - cur), -max_step, max_step))


def edge_clearance(x: float, y: float) -> float:
    return min(x - AO_X_MIN_MM, AO_X_MAX_MM - x, y - AO_Y_MIN_MM, AO_Y_MAX_MM - y)


def measured_course_from_history(est: "Estimate") -> Optional[float]:
    """Measure recent *travel course* directly from Vicon positions.

    This intentionally does not trust the instantaneous velocity fit for course
    calibration.  The hardware log showed stale/noisy velocity values while the
    raw Vicon positions clearly moved.  A 0.22-0.48 s displacement baseline is
    much more reliable for deciding where the chariot actually travelled.
    """
    if len(est.hist) < 2:
        return None
    t1, x1, y1 = est.hist[-1]
    candidate = None
    for t0, x0, y0 in est.hist:
        age = t1 - t0
        if COURSE_WINDOW_MIN_S <= age <= COURSE_WINDOW_MAX_S:
            candidate = (t0, x0, y0)
            break
    if candidate is None:
        return None
    _, x0, y0 = candidate
    dx, dy = x1 - x0, y1 - y0
    if math.hypot(dx, dy) < COURSE_MIN_DISPLACEMENT_MM:
        return None
    return heading_of(dx, dy)


def safe_target(x: float, y: float, inset: float = RECENTER_RELEASE_CLEARANCE_MM) -> Tuple[float, float]:
    return (
        clamp(x, AO_X_MIN_MM + inset, AO_X_MAX_MM - inset),
        clamp(y, AO_Y_MIN_MM + inset, AO_Y_MAX_MM - inset),
    )


def extract_number(value, preferred_keys: Optional[Sequence[str]] = None) -> float:
    preferred_keys = preferred_keys or []
    if isinstance(value, bool):
        raise ValueError("boolean is not numeric")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value)
    if isinstance(value, dict):
        low = {str(k).lower(): k for k in value}
        for key in preferred_keys:
            if key.lower() in low:
                return extract_number(value[low[key.lower()]], preferred_keys)
        for key in ("value", "val", "data", "result"):
            if key in low:
                return extract_number(value[low[key]], preferred_keys)
        for item in value.values():
            try:
                return extract_number(item, preferred_keys)
            except Exception:
                pass
    if isinstance(value, (list, tuple)):
        for item in value:
            try:
                return extract_number(item, preferred_keys)
            except Exception:
                pass
    raise ValueError(f"cannot extract numeric value from {value!r}")


# =============================================================================
# Vicon
# =============================================================================

@dataclass
class Pose:
    x: float
    y: float
    yaw_deg: float
    occluded: bool = False


@dataclass
class Estimate:
    x: float = 0.0
    y: float = 0.0
    yaw_deg: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    speed: float = 0.0
    yaw_rate_deg_s: float = 0.0
    ready: bool = False
    hist: deque = field(default_factory=deque)
    last_unique_x: float = 0.0
    last_unique_y: float = 0.0
    last_unique_t: float = 0.0
    last_t: float = 0.0
    last_yaw: float = 0.0
    last_good_pose_t: float = 0.0
    rejected_pose_count: int = 0

    def update(self, p: Pose, now: float) -> bool:
        if not self.ready:
            self.x = self.last_unique_x = p.x
            self.y = self.last_unique_y = p.y
            self.yaw_deg = self.last_yaw = p.yaw_deg
            self.last_unique_t = self.last_t = self.last_good_pose_t = now
            self.hist.append((now, p.x, p.y))
            self.ready = True
            self.rejected_pose_count = 0
            return True

        # Reject impossible Vicon translations.  v19 hardware logs contained
        # ~0.9-1.7 m frame-to-frame jumps and multi-m/s implied speeds, which
        # are not physically achievable by these loaded Sphero chariots.
        dt_good = max(1e-4, now - self.last_t)
        jump = math.hypot(p.x - self.x, p.y - self.y)
        max_jump = VICON_JUMP_BASE_MM + VICON_MAX_PLAUSIBLE_SPEED_MM_S * min(dt_good, VICON_JUMP_DT_CAP_S)
        if jump > max_jump:
            self.rejected_pose_count += 1
            return False

        self.rejected_pose_count = 0
        self.last_good_pose_t = now
        dt = dt_good
        raw_yr = wrap180(p.yaw_deg - self.last_yaw) / dt
        a = clamp(dt / (YAW_RATE_TC_S + dt), 0.0, 1.0)
        self.yaw_rate_deg_s += a * (raw_yr - self.yaw_rate_deg_s)
        self.last_t = now
        self.last_yaw = p.yaw_deg
        self.x, self.y, self.yaw_deg = p.x, p.y, p.yaw_deg

        if math.hypot(p.x - self.last_unique_x, p.y - self.last_unique_y) >= UNIQUE_POS_EPS_MM:
            self.hist.append((now, p.x, p.y))
            self.last_unique_x, self.last_unique_y = p.x, p.y
            self.last_unique_t = now

        while self.hist and now - self.hist[0][0] > HISTORY_KEEP_S:
            self.hist.popleft()

        recent = [r for r in self.hist if now - r[0] <= VEL_WINDOW_S]
        if len(recent) >= 3:
            mt = sum(r[0] for r in recent) / len(recent)
            mx = sum(r[1] for r in recent) / len(recent)
            my = sum(r[2] for r in recent) / len(recent)
            den = sum((r[0] - mt) ** 2 for r in recent)
            if den > 1e-9:
                self.vx = sum((r[0] - mt) * (r[1] - mx) for r in recent) / den
                self.vy = sum((r[0] - mt) * (r[2] - my) for r in recent) / den

        if now - self.last_unique_t >= STATIONARY_AFTER_S:
            self.vx = self.vy = 0.0
        self.speed = math.hypot(self.vx, self.vy)
        return True


class ViconSystem:
    def __init__(self, configs: Sequence[Tuple[str, str, str]]) -> None:
        from vicon_dssdk import ViconDataStream
        self.configs = list(configs)
        self.client = ViconDataStream.Client()
        self.client.Connect(VICON_SERVER)
        self.client.SetBufferSize(1)
        self.client.EnableSegmentData()

        deadline = time.monotonic() + 6.0
        while time.monotonic() < deadline:
            try:
                poses = self.read_all()
                if all(not p.occluded for p in poses.values()):
                    return
            except Exception:
                time.sleep(0.04)
        raise RuntimeError("Vicon subjects/segments are not all visible")

    @staticmethod
    def _vals(result):
        vals = tuple(float(v) for v in result[0])
        occ = bool(result[1]) if len(result) > 1 else False
        return vals, occ

    def read_all(self) -> Dict[str, Pose]:
        self.client.GetFrame()
        out = {}
        for name, subject, segment in self.configs:
            tr, tr_occ = self._vals(self.client.GetSegmentGlobalTranslation(subject, segment))
            rot, rot_occ = self._vals(self.client.GetSegmentGlobalRotationEulerXYZ(subject, segment))
            if FLOOR_PLANE.upper() == "XY":
                x, y = tr[0], tr[1]
            else:
                x, y = tr[0], tr[2]
            yaw = wrap360(YAW_SIGN * math.degrees(rot[YAW_EULER_INDEX]) + YAW_OFFSET_DEG)
            out[name] = Pose(x, y, yaw, tr_occ or rot_occ)
        return out

    def close(self) -> None:
        try:
            self.client.Disconnect()
        except Exception:
            pass


# =============================================================================
# Per-robot heading basis + driver
# =============================================================================

@dataclass
class HeadingBasis:
    v0x: float
    v0y: float
    v90x: float
    v90y: float

    @property
    def det(self) -> float:
        return self.v0x * self.v90y - self.v90x * self.v0y

    def world_to_internal(self, world_deg: float) -> float:
        wx = math.cos(math.radians(world_deg))
        wy = math.sin(math.radians(world_deg))
        det = self.det
        if abs(det) < 1e-6:
            raise RuntimeError("invalid heading basis")
        # Solve [v0 v90] [a b]^T = world-vector.
        a = (wx * self.v90y - wy * self.v90x) / det
        b = (-wx * self.v0y + wy * self.v0x) / det
        return wrap360(math.degrees(math.atan2(b, a)))

    def internal_to_world(self, h_deg: float) -> float:
        c = math.cos(math.radians(h_deg))
        s = math.sin(math.radians(h_deg))
        return heading_of(self.v0x * c + self.v90x * s, self.v0y * c + self.v90y * s)


class HardwareDriver:
    def __init__(self, api, name: str) -> None:
        self.api = api
        self.name = name
        self.basis: Optional[HeadingBasis] = None
        self.last_h = 0
        self.last_speed = 0
        self.last_stop_t = -1e9
        try:
            self.api.set_stabilization(True)
        except Exception:
            pass

    def set_basis(self, basis: HeadingBasis) -> None:
        self.basis = basis

    def command_internal(self, heading: float, speed: int) -> None:
        h = int(round(heading)) % 360
        s = int(clamp(speed, 0, 255))
        if abs(wrap180(h - self.last_h)) >= BLE_HEADING_DEADBAND_DEG:
            self.api.set_heading(h)
            self.last_h = h
        if abs(s - self.last_speed) >= BLE_SPEED_DEADBAND_CMD or (s == 0) != (self.last_speed == 0):
            self.api.set_speed(s)
            self.last_speed = s

    def command_world(self, world_deg: float, speed: int, heading_bias_deg: float = 0.0) -> None:
        if self.basis is None:
            raise RuntimeError(f"{self.name} has no heading calibration")
        adjusted = wrap360(world_deg + heading_bias_deg)
        self.command_internal(self.basis.world_to_internal(adjusted), speed)

    def stop_hold(self, force: bool = False) -> None:
        now = time.monotonic()
        if not force and self.last_speed == 0 and now - self.last_stop_t < 0.08:
            return
        stop_roll = getattr(self.api, "stop_roll", None)
        if callable(stop_roll):
            try:
                stop_roll(self.last_h)
            except TypeError:
                stop_roll()
        else:
            self.api.set_speed(0)
        self.last_speed = 0
        self.last_stop_t = now


@dataclass
class Robot:
    name: str
    subject: str
    segment: str
    driver: HardwareDriver
    est: Estimate = field(default_factory=Estimate)
    slot_x: float = 0.0
    slot_y: float = 0.0
    cmd_heading_world: Optional[float] = None
    cmd_speed: float = 0.0
    last_cmd_t: float = -1e9
    mode: str = "INIT"
    # Additional Vicon-learned travelling-course correction.  This is allowed
    # to be large because the hardware log showed 60-80 deg systematic course
    # errors after the static heading-basis calibration.
    heading_bias_deg: float = 0.0
    speed_scale: float = 1.0
    slot_error_mm: float = 0.0
    breakaway_until: float = -1e9
    # v21 Vicon-confirmed stiction state.
    stall_ref_t: float = -1e9
    stall_ref_x: float = 0.0
    stall_ref_y: float = 0.0
    stiction_cooldown_until: float = -1e9
    roll_assist_until: float = -1e9
    last_kick_t: float = -1e9
    learned_breakaway_cmd: float = STICTION_KICK_MIN_CMD
    learned_rolling_floor_cmd: float = STICTION_ROLLING_FLOOR_DEFAULT
    stiction_kicks: int = 0
    # v24 learned physical speed response.  This replaces the old assumption
    # that every chassis moves at 2.55 mm/s per Sphero speed count.
    drive_gain_mm_s_per_cmd: float = DRIVE_GAIN_DEFAULT_MM_S_PER_CMD
    drive_speed_i_cmd: float = 0.0
    # Digital-twin/debug vectors in Vicon world coordinates.  These do not
    # affect control; they expose the controller components in real time.
    dbg_target_x: float = 0.0
    dbg_target_y: float = 0.0
    dbg_common_vx: float = 0.0
    dbg_common_vy: float = 0.0
    dbg_slot_vx: float = 0.0
    dbg_slot_vy: float = 0.0
    dbg_sep_vx: float = 0.0
    dbg_sep_vy: float = 0.0
    dbg_boundary_vx: float = 0.0
    dbg_boundary_vy: float = 0.0
    # Verified travelling-course reference and live watchdog telemetry.
    verified_trim_deg: float = 0.0
    measured_course_deg: Optional[float] = None
    course_error_deg: float = 0.0
    course_ref_heading_deg: Optional[float] = None
    course_ref_since: float = -1e9
    dbg_final_vx: float = 0.0
    dbg_final_vy: float = 0.0
    # an earlier revision command inertia and persistent formation-learning states.
    smooth_vx: float = 0.0
    smooth_vy: float = 0.0
    formation_trim_deg: float = 0.0
    learn_along_ema: float = 0.0
    learn_cross_ema: float = 0.0
    learning_samples: int = 0
    # v16 Frenet rail diagnostics/learning state.
    rail_along_mm: float = 0.0
    rail_cross_mm: float = 0.0
    rail_remaining_mm: float = 0.0
    rail_target_x: float = 0.0
    rail_target_y: float = 0.0
    rail_forward_cmd: float = 0.0
    rail_sync_cmd: float = 0.0
    rail_sync_integral: float = 0.0


# =============================================================================
# Hardware connection + robust displacement calibration
# =============================================================================

def connect_hardware(stack: ExitStack, poses: Dict[str, Pose]) -> List[Robot]:
    from spherov2 import scanner
    from spherov2.sphero_edu import SpheroEduAPI

    wanted = [r[0] for r in ROBOT_CONFIGS]
    found = {}
    for attempt in range(1, 5):
        missing = [n for n in wanted if n not in found]
        if not missing:
            break
        print(f"Sphero scan {attempt}/4: {', '.join(missing)}")
        for toy in scanner.find_toys(toy_names=missing, timeout=SCAN_TIMEOUT_S):
            found[toy.name] = toy
        time.sleep(0.4)
    missing = [n for n in wanted if n not in found]
    if missing:
        raise RuntimeError("Could not find: " + ", ".join(missing))

    robots = []
    for name, subject, segment in ROBOT_CONFIGS:
        api = stack.enter_context(SpheroEduAPI(found[name]))
        try:
            api.set_stabilization(True)
        except Exception:
            pass
        driver = HardwareDriver(api, name)
        robots.append(Robot(name, subject, segment, driver))
        p = poses[name]
        print(f"  {name}: Vicon=({p.x:+.1f},{p.y:+.1f}) yaw={p.yaw_deg:.1f} deg")
    return robots


def stop_all(robots: Sequence[Robot], force: bool = True) -> None:
    for r in robots:
        try:
            r.driver.stop_hold(force=force)
            r.cmd_speed = 0.0
        except Exception as exc:
            print(f"  stop failed {r.name}: {exc}")


def update_all(vicon: ViconSystem, robots: Sequence[Robot], now: Optional[float] = None) -> Dict[str, Pose]:
    """Update robot estimates without treating one delayed/occluded frame as data loss.

    reference deliberately separates three cases:
      * brief occlusion -> keep the last good estimate for a short grace window;
      * visible but implausible jump -> reject it and wait for the next frame;
      * sustained loss -> stop and enter the explicit reacquisition routine.
    """
    poses = vicon.read_all()
    now = time.monotonic() if now is None else now
    stale_occ = []
    stale_jump = []

    for r in robots:
        p = poses[r.name]
        if p.occluded:
            # Do not destroy a good mission for one transient Vicon occlusion.
            if (not r.est.ready) or (now - r.est.last_good_pose_t >= VICON_OCCLUSION_GRACE_S):
                stale_occ.append(r.name)
            continue

        accepted = r.est.update(p, now)
        if not accepted and r.est.ready and now - r.est.last_good_pose_t >= VICON_STALE_STOP_S:
            stale_jump.append(r.name)

    if stale_occ or stale_jump:
        stop_all(robots)
        detail = []
        if stale_occ:
            detail.append('occluded=' + ','.join(stale_occ))
        if stale_jump:
            jump_bits = []
            for name in stale_jump:
                rr = next(r for r in robots if r.name == name)
                age = now - rr.est.last_good_pose_t
                jump_bits.append(f"{name}(age={age:.2f}s,rejects={rr.est.rejected_pose_count})")
            detail.append('jump=' + ','.join(jump_bits))
        raise RuntimeError('Vicon pose loss: ' + ' '.join(detail))
    return poses


def wait_settled(vicon: ViconSystem, robot: Robot, robots: Sequence[Robot], max_s: float = CAL_SETTLE_MAX_S) -> Pose:
    local = Estimate()
    start = time.monotonic()
    stable_since = None
    last = vicon.read_all()[robot.name]
    while time.monotonic() - start < max_s:
        poses = vicon.read_all()
        if any(p.occluded for p in poses.values()):
            stop_all(robots)
            raise RuntimeError("Vicon occlusion while settling")
        p = poses[robot.name]
        now = time.monotonic()
        local.update(p, now)
        last = p
        robot.driver.stop_hold()
        if local.speed <= CAL_SETTLE_SPEED_MM_S:
            stable_since = stable_since or now
            if now - stable_since >= CAL_SETTLE_HOLD_S:
                return p
        else:
            stable_since = None
        time.sleep(0.012)
    return last


@dataclass
class CalibrationSample:
    internal_heading: float
    dx: float
    dy: float
    displacement: float
    world_heading: float

    @property
    def weight(self) -> float:
        # Weak-but-real motion still contributes; long clean legs dominate.
        q = clamp(self.displacement / CAL_GOOD_SAMPLE_MOVE_MM, 0.35, 1.8)
        return q * q


def calibration_leg(
    vicon: ViconSystem,
    robot: Robot,
    robots: Sequence[Robot],
    heading: float,
) -> Optional[CalibrationSample]:
    """Run one full-power Vicon displacement calibration leg.

    The chariot receives speed 255 at the requested internal heading for up to
    CAL_DRIVE_TIME_S seconds.  Vicon measures the net world displacement.
    The only reasons to end before the full window are AO protection or the
    large-travel guard.  A single weak leg is never fatal.
    """
    stop_all(robots)
    time.sleep(0.10)
    p0 = vicon.read_all()[robot.name]
    clearance0 = edge_clearance(p0.x, p0.y)
    if clearance0 < CAL_HARD_MIN_CLEARANCE_MM:
        print(
            f"    heading {heading:3.0f}: SKIPPED -- only {clearance0:.0f} mm AO clearance. "
            "Move/recenter before this calibration direction."
        )
        return None

    if clearance0 < CAL_REQUIRED_CLEARANCE_MM:
        print(
            f"    heading {heading:3.0f}: FULL POWER but boundary-guarded "
            f"(start clearance={clearance0:.0f} mm)"
        )
    else:
        print(
            f"    heading {heading:3.0f}: FULL POWER 255 for up to "
            f"{CAL_DRIVE_TIME_S:.1f} s...",
            flush=True,
        )

    start = time.monotonic()
    last_cmd = -1e9
    p = p0
    early_reason = "time"

    while True:
        poses = vicon.read_all()
        if any(q.occluded for q in poses.values()):
            stop_all(robots)
            raise RuntimeError("Vicon occlusion during calibration")

        p = poses[robot.name]
        moved = math.hypot(p.x - p0.x, p.y - p0.y)
        clearance = edge_clearance(p.x, p.y)
        elapsed = time.monotonic() - start

        if elapsed >= CAL_DRIVE_TIME_S:
            early_reason = "time"
            break
        if moved >= CAL_MAX_MOVE_MM:
            early_reason = f"travel guard {moved:.0f} mm"
            break
        if clearance <= CAL_BOUNDARY_STOP_CLEARANCE_MM:
            early_reason = f"AO guard clearance {clearance:.0f} mm"
            break

        now = time.monotonic()
        if now - last_cmd >= 1.0 / COMMAND_HZ:
            robot.driver.command_internal(heading, CAL_SPEED_CMD)
            last_cmd = now
        time.sleep(0.008)

    robot.driver.stop_hold(force=True)
    p1 = wait_settled(vicon, robot, robots)
    dx, dy = p1.x - p0.x, p1.y - p0.y
    disp = math.hypot(dx, dy)
    elapsed = time.monotonic() - start

    if disp < CAL_MIN_SAMPLE_MOVE_MM:
        print(
            f"      result: WEAK/SKIPPED displacement=({dx:+.1f},{dy:+.1f}) mm, "
            f"distance={disp:.1f} mm after {elapsed:.2f} s ({early_reason}); "
            f"need >= {CAL_MIN_SAMPLE_MOVE_MM:.0f} mm"
        )
        return None

    world = heading_of(dx, dy)
    quality = "GOOD" if disp >= CAL_GOOD_SAMPLE_MOVE_MM else "usable/weak"
    print(
        f"      result: displacement=({dx:+.1f},{dy:+.1f}) mm, distance={disp:.1f}, "
        f"world={world:.1f} deg [{quality}], elapsed={elapsed:.2f} s ({early_reason})"
    )
    return CalibrationSample(heading, dx, dy, disp, world)


def _weighted_circular_mean_deg(angles: Sequence[float], weights: Sequence[float]) -> float:
    sx = sum(w * math.cos(math.radians(a)) for a, w in zip(angles, weights))
    sy = sum(w * math.sin(math.radians(a)) for a, w in zip(angles, weights))
    if math.hypot(sx, sy) < 1e-9:
        return wrap360(angles[0])
    return wrap360(math.degrees(math.atan2(sy, sx)))


def _has_noncollinear_internal_geometry(samples: Sequence[CalibrationSample]) -> bool:
    for a, b in itertools.combinations(samples, 2):
        dh = math.radians(wrap180(a.internal_heading - b.internal_heading))
        if abs(math.sin(dh)) >= CAL_MIN_NONCOLLINEAR_SIN:
            return True
    return False


def fit_basis_from_samples(samples: Sequence[CalibrationSample]) -> Tuple[HeadingBasis, float, int, float]:
    """Fit world_angle ~= offset + sign * internal_heading.

    The Sphero heading map should be an orthogonal 2-D rotation/reflection, so
    fitting this model is substantially more robust than subtracting opposite
    calibration vectors.  It also means a 25 mm heading-90 leg can still be used
    together with an 80 mm heading-0 leg instead of aborting the mission.
    """
    if len(samples) < 2 or not _has_noncollinear_internal_geometry(samples):
        raise ValueError("need at least two usable non-collinear displacement samples")

    best = None
    for sign in (+1, -1):
        weights = [s.weight for s in samples]
        offsets = [wrap360(s.world_heading - sign * s.internal_heading) for s in samples]
        offset = _weighted_circular_mean_deg(offsets, weights)
        errs = [wrap180(s.world_heading - (offset + sign * s.internal_heading)) for s in samples]
        wrms = math.sqrt(sum(w * e * e for w, e in zip(weights, errs)) / max(1e-9, sum(weights)))
        maxerr = max(abs(e) for e in errs)
        score = wrms + 0.12 * maxerr
        if best is None or score < best[0]:
            best = (score, wrms, maxerr, sign, offset, errs)

    assert best is not None
    _, wrms, maxerr, sign, offset, errs = best
    if wrms > CAL_MAX_FIT_RMS_DEG:
        raise ValueError(f"direction-fit RMS {wrms:.1f} deg is too large")

    a0 = wrap360(offset)
    a90 = wrap360(offset + sign * 90.0)
    v0 = (math.cos(math.radians(a0)), math.sin(math.radians(a0)))
    v90 = (math.cos(math.radians(a90)), math.sin(math.radians(a90)))
    basis = HeadingBasis(v0[0], v0[1], v90[0], v90[1])
    return basis, wrms, sign, maxerr


def basis_from_vectors(vecs: Dict[float, Tuple[float, float]]) -> HeadingBasis:
    """Compatibility helper for old saved/tests; not used by robust calibration."""
    v0 = unit(vecs[0.0][0] - vecs[180.0][0], vecs[0.0][1] - vecs[180.0][1])
    v90 = unit(vecs[90.0][0] - vecs[270.0][0], vecs[90.0][1] - vecs[270.0][1])
    return HeadingBasis(v0[0], v0[1], v90[0], v90[1])


def calibration_path() -> Path:
    return Path(__file__).resolve().with_name(CAL_FILE)


def save_calibrations(robots: Sequence[Robot]) -> None:
    payload = {"controller": CONTROLLER_VERSION, "robots": {}}
    for r in robots:
        b = r.driver.basis
        if b is None:
            continue
        payload["robots"][r.name] = {"v0": [b.v0x, b.v0y], "v90": [b.v90x, b.v90y], "course_trim_deg": r.heading_bias_deg}
    calibration_path().write_text(json.dumps(payload, indent=2))


def load_calibrations(robots: Sequence[Robot]) -> bool:
    # reference may explicitly reuse the user's known-good v25 calibration so the Vicon
    # continuity patch can be tested without changing a successful heading map.
    candidates = [
        calibration_path(),
        Path(__file__).resolve().with_name("three_chariot_vicon_heading_calibration_v25.json"),
    ]
    for candidate in candidates:
        try:
            if not candidate.exists():
                continue
            data = json.loads(candidate.read_text())
            rows = data.get("robots", {})
            for r in robots:
                row = rows[r.name]
                b = HeadingBasis(float(row["v0"][0]), float(row["v0"][1]), float(row["v90"][0]), float(row["v90"][1]))
                if abs(b.det) < CAL_MIN_DET:
                    raise ValueError("invalid saved heading basis")
                r.driver.set_basis(b)
                r.heading_bias_deg = clamp(float(row.get("course_trim_deg", 0.0)), -HEADING_BIAS_MAX_DEG, HEADING_BIAS_MAX_DEG)
                r.verified_trim_deg = r.heading_bias_deg
            print(f"Loaded displacement + Vicon course calibration from {candidate.name}")
            return True
        except Exception:
            continue
    return False


def _course_verify_heading(p: Pose) -> float:
    """Choose a safe world direction for a short travelling-course check."""
    # If not near the central operating area, verification doubles as recentering.
    if math.hypot(p.x, p.y) > 260.0:
        return heading_of(-p.x, -p.y)

    # Near the centre, choose the cardinal direction with the most AO room.
    choices = [
        (AO_X_MAX_MM - p.x, 0.0),
        (AO_Y_MAX_MM - p.y, 90.0),
        (p.x - AO_X_MIN_MM, 180.0),
        (p.y - AO_Y_MIN_MM, 270.0),
    ]
    return max(choices, key=lambda z: z[0])[1]


def _room_along_heading(p: Pose, heading_deg: float) -> float:
    """Approximate ray distance from pose to AO boundary along heading."""
    ux = math.cos(math.radians(heading_deg))
    uy = math.sin(math.radians(heading_deg))
    vals = []
    if ux > 1e-6:
        vals.append((AO_X_MAX_MM - p.x) / ux)
    elif ux < -1e-6:
        vals.append((AO_X_MIN_MM - p.x) / ux)
    if uy > 1e-6:
        vals.append((AO_Y_MAX_MM - p.y) / uy)
    elif uy < -1e-6:
        vals.append((AO_Y_MIN_MM - p.y) / uy)
    vals = [v for v in vals if v >= 0.0]
    return min(vals) if vals else 0.0


def _safe_verification_pair(p: Pose) -> Tuple[float, float]:
    """Choose two non-collinear world headings with maximum AO room."""
    card = [0.0, 90.0, 180.0, 270.0]
    rooms = {h: _room_along_heading(p, h) for h in card}
    h1 = max(card, key=lambda h: rooms[h])
    perpendicular = [wrap360(h1 + 90.0), wrap360(h1 - 90.0)]
    h2 = max(perpendicular, key=lambda h: _room_along_heading(p, h))
    return h1, h2


def _course_verification_leg(
    vicon: ViconSystem, robot: Robot, robots: Sequence[Robot], desired: float
) -> Optional[Tuple[float, float]]:
    """Command one world direction and measure the STEADY Vicon travel course.

    The first COURSE_VERIFY_BURN_IN_S is deliberately excluded so the chariot
    may rotate/settle onto its casters.  Only the later displacement is used to
    judge whether the command is actually being followed.
    """
    stop_all(robots)
    time.sleep(0.20)
    poses0 = vicon.read_all()
    if any(p.occluded for p in poses0.values()):
        return None
    p0 = poses0[robot.name]
    start = time.monotonic()
    measure_pose = None
    last_cmd = -1e9
    p = p0
    reason = "time"
    while True:
        poses = vicon.read_all()
        if any(q.occluded for q in poses.values()):
            reason = "occlusion"
            break
        p = poses[robot.name]
        elapsed = time.monotonic() - start
        moved_total = math.hypot(p.x - p0.x, p.y - p0.y)
        clearance = edge_clearance(p.x, p.y)
        if elapsed >= COURSE_VERIFY_BURN_IN_S and measure_pose is None:
            measure_pose = Pose(p.x, p.y, p.yaw_deg, p.occluded)
        if elapsed >= COURSE_VERIFY_BURN_IN_S + COURSE_VERIFY_MEASURE_S:
            reason = "steady window"
            break
        if moved_total >= COURSE_VERIFY_MAX_MOVE_MM:
            reason = "travel guard"
            break
        if clearance <= COURSE_VERIFY_EDGE_GUARD_MM:
            reason = "AO guard"
            break
        now = time.monotonic()
        if now - last_cmd >= 1.0 / COMMAND_HZ:
            robot.driver.command_world(desired, COURSE_VERIFY_SPEED_CMD, robot.heading_bias_deg)
            last_cmd = now
        time.sleep(0.008)

    robot.driver.stop_hold(force=True)
    try:
        p1 = wait_settled(vicon, robot, robots)
    except Exception:
        p1 = p
    if measure_pose is None:
        measure_pose = p0
    dx, dy = p1.x - measure_pose.x, p1.y - measure_pose.y
    disp = math.hypot(dx, dy)
    if disp < COURSE_VERIFY_MIN_MOVE_MM:
        print(
            f"      weak steady-course sample: displacement=({dx:+.1f},{dy:+.1f}) mm "
            f"distance={disp:.1f} mm ({reason})"
        )
        return None
    actual = heading_of(dx, dy)
    err = wrap180(desired - actual)
    print(
        f"      steady Vicon course={actual:.1f} deg, displacement={disp:.1f} mm, "
        f"desired={desired:.1f}, residual={err:+.1f} deg ({reason})"
    )
    return actual, err


def verify_robot_course(vicon: ViconSystem, robot: Robot, robots: Sequence[Robot]) -> None:
    """Closed-loop proof that commanded WORLD directions are physically followed.

    A fresh static 0/90 displacement basis is not enough by itself for the
    loaded chariot.  We therefore command two real world directions, measure the
    late/steady Vicon displacement, iteratively correct the course trim, and do
    not release this robot to the mission until both directions are credible.
    """
    robot.heading_bias_deg = 0.0
    passes = 0
    residuals: List[float] = []

    # Re-evaluate safe headings from the current position before each axis.
    poses = vicon.read_all()
    p = poses[robot.name]
    headings = list(_safe_verification_pair(p))

    for axis_idx in range(COURSE_VERIFY_REQUIRED_PASSES):
        desired = headings[min(axis_idx, len(headings)-1)]
        axis_ok = False
        for attempt in range(1, COURSE_VERIFY_MAX_TRIES + 1):
            # If this heading no longer has enough room, pick the safest
            # cardinal that is not collinear with the previous verified axis.
            pnow = vicon.read_all()[robot.name]
            if _room_along_heading(pnow, desired) < COURSE_VERIFY_EDGE_GUARD_MM + 260.0:
                h1, h2 = _safe_verification_pair(pnow)
                desired = h1 if axis_idx == 0 else h2

            print(
                f"    {robot.name}: CLOSED-LOOP VERIFY axis {axis_idx+1}/2, "
                f"attempt {attempt}/{COURSE_VERIFY_MAX_TRIES}: desired={desired:.1f} deg, "
                f"trim={robot.heading_bias_deg:+.1f} deg"
            )
            sample = _course_verification_leg(vicon, robot, robots, desired)
            if sample is None:
                continue
            actual, err = sample
            residuals.append(err)
            tol = COURSE_VERIFY_GOOD_ERR_DEG if axis_idx == 0 else COURSE_VERIFY_SECONDARY_TOL_DEG
            if abs(err) <= tol:
                print(
                    f"      AXIS PASS {robot.name}: desired={desired:.1f}, actual={actual:.1f}, "
                    f"residual={err:+.1f} deg"
                )
                axis_ok = True
                passes += 1
                break

            # Directly apply most of the measured correction.  This is a
            # controlled calibration step, not slow runtime learning.
            robot.heading_bias_deg = clamp(
                robot.heading_bias_deg + clamp(err, -95.0, 95.0),
                -HEADING_BIAS_MAX_DEG, HEADING_BIAS_MAX_DEG,
            )
            print(f"      applying course-trim correction -> {robot.heading_bias_deg:+.1f} deg")

        if not axis_ok:
            raise RuntimeError(
                f"{robot.name}: command verification failed on axis {axis_idx+1}. "
                "Vicon could not confirm that the robot followed the requested world direction; "
                "mission will not start with an unverified steering map."
            )

    robot.verified_trim_deg = robot.heading_bias_deg
    print(
        f"    VERIFIED {robot.name}: world commands physically followed on two axes; "
        f"final trim={robot.heading_bias_deg:+.1f} deg, residuals=" +
        ", ".join(f"{e:+.1f}" for e in residuals[-2:])
    )

def verify_all_courses(vicon: ViconSystem, robots: Sequence[Robot]) -> None:
    print("Per-robot Vicon TRAVELLING-COURSE verification...")
    print(
        "  Static heading calibration is followed by real displacement feedback. "
        "If a chariot travels sideways, the controller learns the angular correction before swarming."
    )
    for r in robots:
        verify_robot_course(vicon, r, robots)
    stop_all(robots)
    save_calibrations(robots)


def calibrate_all(vicon: ViconSystem, robots: Sequence[Robot]) -> None:
    print("Per-robot FULL-POWER Sphero-heading -> Vicon-displacement calibration...")
    print(
        f"  Each primary leg commands speed {CAL_SPEED_CMD} for up to {CAL_DRIVE_TIME_S:.1f} s. "
        "Vicon measures the resulting world displacement; normally headings 0 and 90 are enough."
    )

    for r in robots:
        print(f"  {r.name}:")
        samples: List[CalibrationSample] = []

        # Start with two full-power orthogonal directions.  This is usually all
        # that is required and avoids unnecessary calibration wandering.
        for h in CAL_PRIMARY_HEADINGS:
            sample = calibration_leg(vicon, r, robots, h)
            if sample is not None:
                samples.append(sample)

        def try_fit() -> Optional[Tuple[HeadingBasis, float, int, float]]:
            try:
                return fit_basis_from_samples(samples)
            except ValueError:
                return None

        fit = try_fit()

        # Only if the two decisive full-power primary legs are insufficient do
        # we add further headings, one at a time, until Vicon can identify the map.
        if fit is None:
            print("    Primary 0/90 fit insufficient; adding full-power fallback headings...")
            for h in CAL_FALLBACK_HEADINGS:
                sample = calibration_leg(vicon, r, robots, h)
                if sample is not None:
                    samples.append(sample)
                fit = try_fit()
                if fit is not None:
                    break

        # Last-resort: if exactly two non-collinear usable samples exist but the
        # weighted residual threshold was marginal, fit those two directly.  This
        # is preferable to killing the whole swarm because one chariot resisted
        # a particular calibration direction.
        if fit is None and len(samples) >= 2 and _has_noncollinear_internal_geometry(samples):
            best_pair = None
            for a, b in itertools.combinations(samples, 2):
                dh = abs(math.sin(math.radians(wrap180(a.internal_heading - b.internal_heading))))
                if dh < CAL_MIN_NONCOLLINEAR_SIN:
                    continue
                score = (a.displacement + b.displacement) * dh
                if best_pair is None or score > best_pair[0]:
                    best_pair = (score, a, b)
            if best_pair is not None:
                pair = [best_pair[1], best_pair[2]]
                # With two samples, choose sign/offset by minimum pair disagreement
                # and accept a looser residual because both samples came from Vicon.
                candidates = []
                for sign in (+1, -1):
                    weights = [x.weight for x in pair]
                    offs = [wrap360(x.world_heading - sign * x.internal_heading) for x in pair]
                    off = _weighted_circular_mean_deg(offs, weights)
                    errs = [wrap180(x.world_heading - (off + sign*x.internal_heading)) for x in pair]
                    rms = math.sqrt(sum(w*e*e for w,e in zip(weights,errs))/sum(weights))
                    candidates.append((rms, sign, off))
                rms, sign, off = min(candidates, key=lambda z: z[0])
                a0 = wrap360(off)
                a90 = wrap360(off + sign*90.0)
                b = HeadingBasis(
                    math.cos(math.radians(a0)), math.sin(math.radians(a0)),
                    math.cos(math.radians(a90)), math.sin(math.radians(a90)),
                )
                fit = (b, rms, sign, rms)
                print(
                    f"    ROBUST TWO-SAMPLE FALLBACK: headings {pair[0].internal_heading:.0f}/"
                    f"{pair[1].internal_heading:.0f}, fit_rms={rms:.1f} deg"
                )

        if fit is None:
            stop_all(robots)
            raise RuntimeError(
                f"{r.name}: could not obtain two usable non-collinear Vicon displacement samples. "
                "The robot may be mechanically jammed or not responding to heading commands."
            )

        b, fit_rms, sign, maxerr = fit
        r.driver.set_basis(b)
        print(
            f"    ACCEPTED {r.name}: samples={len(samples)}, sign={sign:+d}, "
            f"v0=({b.v0x:+.3f},{b.v0y:+.3f}) v90=({b.v90x:+.3f},{b.v90y:+.3f}) "
            f"det={b.det:+.3f}, fit_rms={fit_rms:.1f} deg, maxerr={maxerr:.1f} deg"
        )

    stop_all(robots)
    # Crucial dynamic check: the hardware log showed that a good static 0/90
    # fit could still yield 60-80 deg travelling-course error under the chariot.
    verify_all_courses(vicon, robots)


# =============================================================================
# Formation, square, boundary, collision
# =============================================================================

def centroid(robots: Sequence[Robot]) -> Tuple[float, float, float, float]:
    n = len(robots)
    return (
        sum(r.est.x for r in robots) / n,
        sum(r.est.y for r in robots) / n,
        sum(r.est.vx for r in robots) / n,
        sum(r.est.vy for r in robots) / n,
    )


def pair_min(robots: Sequence[Robot]) -> float:
    """Minimum centroid-to-centroid distance (diagnostic only)."""
    return min(math.hypot(a.est.x - b.est.x, a.est.y - b.est.y) for a, b in itertools.combinations(robots, 2))


def body_yaw_deg(r: Robot) -> float:
    """Physical long-axis yaw of the 20 x 14 cm body in Vicon world coordinates."""
    return wrap360(r.est.yaw_deg + BODY_YAW_OFFSET_DEG.get(r.name, 0.0))


def _body_axes(yaw_deg: float) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """Longitudinal and lateral unit axes of the rectangular chariot."""
    th = math.radians(yaw_deg)
    longitudinal = (math.cos(th), math.sin(th))
    lateral = (-math.sin(th), math.cos(th))
    return longitudinal, lateral


def _projection_radius(axis: Tuple[float, float], yaw_deg: float, margin_mm: float) -> float:
    """Projection radius of an oriented rectangle onto an arbitrary unit axis."""
    u, v = _body_axes(yaw_deg)
    hl = BODY_HALF_LENGTH_MM + margin_mm
    hw = BODY_HALF_WIDTH_MM + margin_mm
    return (
        hl * abs(u[0] * axis[0] + u[1] * axis[1])
        + hw * abs(v[0] * axis[0] + v[1] * axis[1])
    )


def body_edge_clearance(r: Robot, margin_mm: float = BODY_WALL_MARGIN_MM) -> float:
    """Clearance from the padded rectangular body to the closest AO wall.

    Unlike the old point-robot test, this accounts for 200 x 140 mm body size
    and the current Vicon yaw.
    """
    th = math.radians(body_yaw_deg(r))
    hl = BODY_HALF_LENGTH_MM + margin_mm
    hw = BODY_HALF_WIDTH_MM + margin_mm
    hx = hl * abs(math.cos(th)) + hw * abs(math.sin(th))
    hy = hl * abs(math.sin(th)) + hw * abs(math.cos(th))
    return min(
        (r.est.x - hx) - AO_X_MIN_MM,
        AO_X_MAX_MM - (r.est.x + hx),
        (r.est.y - hy) - AO_Y_MIN_MM,
        AO_Y_MAX_MM - (r.est.y + hy),
    )


def footprint_pair_clearance(
    a: Robot,
    b: Robot,
    margin_mm: float = BODY_SAFETY_MARGIN_MM,
    predict_s: float = 0.0,
) -> Tuple[float, float, float]:
    """Signed SAT clearance between two oriented padded chariot rectangles.

    Returns (clearance_mm, push_x, push_y).  Positive clearance means the padded
    rectangles are separated.  Zero means touching.  Negative means overlap.
    push_x/push_y points from b away toward a along the SAT axis that requires
    the strongest separation.
    """
    ax = a.est.x + a.est.vx * predict_s
    ay = a.est.y + a.est.vy * predict_s
    bx = b.est.x + b.est.vx * predict_s
    by = b.est.y + b.est.vy * predict_s
    dx, dy = ax - bx, ay - by

    ayaw = body_yaw_deg(a)
    byaw = body_yaw_deg(b)
    au, av = _body_axes(ayaw)
    bu, bv = _body_axes(byaw)
    axes = (au, av, bu, bv)

    best_gap = -1e12
    best_axis = (1.0, 0.0)
    for axis in axes:
        # axis is already unit length.
        center_sep_signed = dx * axis[0] + dy * axis[1]
        center_sep = abs(center_sep_signed)
        ra = _projection_radius(axis, ayaw, margin_mm)
        rb = _projection_radius(axis, byaw, margin_mm)
        gap = center_sep - (ra + rb)
        if gap > best_gap:
            best_gap = gap
            sign = 1.0 if center_sep_signed >= 0.0 else -1.0
            best_axis = (sign * axis[0], sign * axis[1])

    return best_gap, best_axis[0], best_axis[1]


def min_body_clearance(robots: Sequence[Robot]) -> float:
    return min(
        footprint_pair_clearance(a, b)[0]
        for a, b in itertools.combinations(robots, 2)
    )


def formation_rms(robots: Sequence[Robot], cx: float, cy: float) -> float:
    vals = []
    for r in robots:
        ex = (cx + r.slot_x) - r.est.x
        ey = (cy + r.slot_y) - r.est.y
        vals.append(ex * ex + ey * ey)
    return math.sqrt(sum(vals) / len(vals))


def choose_slots(robots: Sequence[Robot]) -> None:
    # Choose orientation/permutation minimizing current movement relative to the
    # CURRENT centroid.  This avoids unnecessary crossing during formation lock.
    cx, cy, _, _ = centroid(robots)
    best = None
    for angle in range(0, 360, 15):
        slots = []
        for k in range(3):
            a = math.radians(angle + 120.0 * k)
            slots.append((FORMATION_RADIUS_MM * math.cos(a), FORMATION_RADIUS_MM * math.sin(a)))
        for perm in itertools.permutations(range(3)):
            cost = 0.0
            for ri, si in enumerate(perm):
                tx, ty = cx + slots[si][0], cy + slots[si][1]
                cost += math.hypot(robots[ri].est.x - tx, robots[ri].est.y - ty)
            if best is None or cost < best[0]:
                best = (cost, slots, perm, angle)
    _, slots, perm, angle = best
    for ri, si in enumerate(perm):
        robots[ri].slot_x, robots[ri].slot_y = slots[si]
    print(f"Formation slots: radius={FORMATION_RADIUS_MM:.0f} mm (~{math.sqrt(3)*FORMATION_RADIUS_MM:.0f} mm pair), orientation={angle} deg")
    for r in robots:
        print(f"  {r.name}: relative slot=({r.slot_x:+.1f},{r.slot_y:+.1f}) mm")


def square_corners(side_mm: float) -> List[Tuple[float, float]]:
    h = 0.5 * side_mm
    # Exact user-requested square centred at Vicon (0,0), clockwise from SW.
    return [
        (-h, -h),
        (+h, -h),
        (+h, +h),
        (-h, +h),
    ]


def boundary_vector(r: Robot) -> Tuple[float, float, float]:
    """Footprint-aware inward vector plus padded-body wall clearance."""
    th = math.radians(body_yaw_deg(r))
    hl = BODY_HALF_LENGTH_MM + BODY_WALL_MARGIN_MM
    hw = BODY_HALF_WIDTH_MM + BODY_WALL_MARGIN_MM
    hx = hl * abs(math.cos(th)) + hw * abs(math.sin(th))
    hy = hl * abs(math.sin(th)) + hw * abs(math.cos(th))

    walls = [
        ((r.est.x - hx) - AO_X_MIN_MM, +1.0, 0.0),
        (AO_X_MAX_MM - (r.est.x + hx), -1.0, 0.0),
        ((r.est.y - hy) - AO_Y_MIN_MM, 0.0, +1.0),
        (AO_Y_MAX_MM - (r.est.y + hy), 0.0, -1.0),
    ]
    c = min(w[0] for w in walls)
    vx = vy = 0.0
    for d, nx, ny in walls:
        if d < BOUNDARY_SOFT_MM:
            q = clamp(
                (BOUNDARY_SOFT_MM - d)
                / max(1.0, BOUNDARY_SOFT_MM - BOUNDARY_CRITICAL_MM),
                0.0,
                1.9,
            )
            mag = 300.0 * q * q
            vx += mag * nx
            vy += mag * ny
    return vx, vy, c


def collision_vectors(robots: Sequence[Robot]) -> Dict[str, Tuple[float, float, float]]:
    """Very short-range, bounded collision bumper using REAL body clearance.

    This is deliberately not a flocking/repulsion field.  It is zero until the
    200x140-mm rectangles are within 30 mm, then rises smoothly and is capped.
    Trajectory and formation tracking therefore remain dominant.
    """
    out = {r.name: [0.0, 0.0, 1e9] for r in robots}
    for a, b in itertools.combinations(robots, 2):
        clear, ux, uy = footprint_pair_clearance(a, b, 0.0, 0.0)
        out[a.name][2] = min(out[a.name][2], clear)
        out[b.name][2] = min(out[b.name][2], clear)
        if clear < BODY_CLEAR_SOFT_MM:
            q = clamp((BODY_CLEAR_SOFT_MM - clear) / max(1.0, BODY_CLEAR_SOFT_MM), 0.0, 2.0)
            mag = min(58.0, 28.0 * q * q)
            out[a.name][0] += mag * ux
            out[a.name][1] += mag * uy
            out[b.name][0] -= mag * ux
            out[b.name][1] -= mag * uy
    return {k: (v[0], v[1], v[2]) for k, v in out.items()}

def centroid_side_velocity(
    cx: float, cy: float, cvx: float, cvy: float,
    corners: Sequence[Tuple[float, float]], side_idx: int,
) -> Tuple[float, float, float, float, float]:
    """Return centroid desired vx/vy, cross-track, remaining-along and corner distance."""
    a = corners[side_idx]
    b = corners[(side_idx + 1) % 4]
    nxt = corners[(side_idx + 2) % 4]
    tx, ty = unit(b[0] - a[0], b[1] - a[1])
    nx, ny = -ty, tx
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    rx, ry = cx - a[0], cy - a[1]
    along = rx * tx + ry * ty
    cross = rx * nx + ry * ny
    remaining = L - along
    cross_v = cvx * nx + cvy * ny

    # Blend tangent smoothly toward next side near a corner, but side state is
    # still explicit and only advances from actual Vicon corner capture.
    ntx, nty = unit(nxt[0] - b[0], nxt[1] - b[1])
    alpha = clamp((CORNER_BLEND_MM - max(0.0, remaining)) / CORNER_BLEND_MM, 0.0, 1.0)
    bx, by = unit((1.0 - alpha) * tx + alpha * ntx, (1.0 - alpha) * ty + alpha * nty)

    forward = (1.0 - alpha) * CENTROID_STRAIGHT_SPEED_MM_S + alpha * CENTROID_CORNER_SPEED_MM_S
    abs_cross = abs(cross)
    if abs_cross > PATH_ERROR_SLOW_MM:
        q = clamp((PATH_ERROR_HARD_MM - abs_cross) / max(1.0, PATH_ERROR_HARD_MM - PATH_ERROR_SLOW_MM), 0.10, 1.0)
        forward *= q
    if abs_cross >= PATH_ERROR_HARD_MM:
        forward = min(forward, 90.0)

    # If centroid is behind start of this side, add forward correction. If it
    # has overshot, reduce forward component drastically.
    if along < 0.0:
        forward += min(150.0, -CENTROID_BACKTRACK_KP * along)
    if remaining < -CORNER_OVERSHOOT_MM:
        forward = 70.0

    corr = -CENTROID_CROSS_KP * cross - CENTROID_CROSS_KD * cross_v
    vx = forward * bx + corr * nx
    vy = forward * by + corr * ny
    corner_dist = math.hypot(cx - b[0], cy - b[1])
    return vx, vy, cross, remaining, corner_dist


# =============================================================================
# Learning + command generation
# =============================================================================

def learning_path() -> Path:
    return Path(__file__).resolve().with_name(LEARNING_FILE)


def load_learning(robots: Sequence[Robot]) -> None:
    rows = {}
    source_name = None
    for candidate in (learning_path(), Path(__file__).resolve().with_name(LEGACY_LEARNING_FILE)):
        try:
            if candidate.exists():
                rows = json.loads(candidate.read_text()).get("robots", {})
                source_name = candidate.name
                break
        except Exception:
            continue
    if source_name:
        print(f"  adaptive drive: importing {source_name}")
    for r in robots:
        row = rows.get(r.name, {})
        # Course trim comes from the Vicon course-verification calibration file.
        # Do not overwrite it with an older learning snapshot.  an earlier revision separately
        # learns small formation feed-forward terms that cannot invalidate the
        # verified heading map.
        r.speed_scale = clamp(float(row.get("speed_scale", 1.0)), SPEED_SCALE_MIN, SPEED_SCALE_MAX)
        r.formation_trim_deg = clamp(float(row.get("formation_trim_deg", 0.0)), -FORMATION_TRIM_MAX_DEG, FORMATION_TRIM_MAX_DEG)
        r.learning_samples = int(row.get("learning_samples", 0))
        r.learned_breakaway_cmd = clamp(
            float(row.get("breakaway_cmd", STICTION_KICK_MIN_CMD)),
            STICTION_KICK_MIN_CMD, STICTION_KICK_MAX_CMD
        )
        r.learned_rolling_floor_cmd = clamp(
            float(row.get("rolling_floor_cmd", STICTION_ROLLING_FLOOR_DEFAULT)),
            STICTION_ROLLING_FLOOR_MIN, STICTION_ROLLING_FLOOR_MAX
        )
        # Do not inherit v23's very high rolling floors blindly.  v24 learns
        # physical speed response directly from Vicon.
        r.learned_rolling_floor_cmd = min(r.learned_rolling_floor_cmd, 66.0)
        r.drive_gain_mm_s_per_cmd = clamp(
            float(row.get("drive_gain_mm_s_per_cmd", DRIVE_GAIN_DEFAULT_MM_S_PER_CMD)),
            DRIVE_GAIN_MIN, DRIVE_GAIN_MAX
        )
        r.stiction_kicks = int(row.get("stiction_kicks", 0))
        print(
            f"  learning {r.name}: course_trim={r.heading_bias_deg:+.2f} deg "
            f"speed_scale={r.speed_scale:.3f} form_trim={r.formation_trim_deg:+.2f} deg "
            f"breakaway={r.learned_breakaway_cmd:.0f} roll_floor={r.learned_rolling_floor_cmd:.0f} driveGain={r.drive_gain_mm_s_per_cmd:.2f} "
            f"samples={r.learning_samples}"
        )


def save_learning(robots: Sequence[Robot]) -> None:
    payload = {
        "controller": CONTROLLER_VERSION,
        "robots": {
            r.name: {
                "heading_bias_deg": r.heading_bias_deg,
                "speed_scale": r.speed_scale,
                "formation_trim_deg": r.formation_trim_deg,
                "learning_samples": r.learning_samples,
                "breakaway_cmd": r.learned_breakaway_cmd,
                "rolling_floor_cmd": r.learned_rolling_floor_cmd,
                "drive_gain_mm_s_per_cmd": r.drive_gain_mm_s_per_cmd,
                "stiction_kicks": r.stiction_kicks,
                "drive_gain_mm_s_per_cmd": r.drive_gain_mm_s_per_cmd,
            }
            for r in robots
        },
    }
    try:
        learning_path().write_text(json.dumps(payload, indent=2))
        # Runtime course-lock improves the same angular correction established
        # during startup verification, so persist it with the heading basis too.
        if all(r.driver.basis is not None for r in robots):
            save_calibrations(robots)
    except Exception as exc:
        print(f"WARNING: could not save learning model: {exc}")


def command_robot(r: Robot, vx: float, vy: float, max_cmd: int, dt: float, recovery: bool, min_cmd: float = MIN_MOVING_CMD) -> None:
    """Shape one robot command and actively overcome loaded-chariot stiction.

    Normal motion remains smooth, but a robot that Vicon confirms has remained
    physically stationary despite a meaningful forward command receives one
    short torque pulse ALONG THE ALREADY-CONSTRAINED path heading.  The pulse
    bypasses the normal speed slew limiter; this is essential, because a
    0.1-second breakaway request passed through a ~300 cmd/s slew never reaches
    useful torque before it expires.
    """
    now = time.monotonic()

    # First-order vector lag.
    tau = RECOVERY_VECTOR_TAU_S if recovery else COMMAND_VECTOR_TAU_S
    alpha = 1.0 - math.exp(-max(1e-4, dt) / max(1e-3, tau))
    tvx = r.smooth_vx + alpha * (vx - r.smooth_vx)
    tvy = r.smooth_vy + alpha * (vy - r.smooth_vy)

    # Vector acceleration limit.
    dvx, dvy = tvx - r.smooth_vx, tvy - r.smooth_vy
    dmag = math.hypot(dvx, dvy)
    amax = RECOVERY_VECTOR_ACCEL_MM_S2 if recovery else COMMAND_VECTOR_ACCEL_MM_S2
    max_dv = amax * max(1e-3, dt)
    if dmag > max_dv:
        ux, uy = unit(dvx, dvy)
        tvx = r.smooth_vx + ux * max_dv
        tvy = r.smooth_vy + uy * max_dv
    r.smooth_vx, r.smooth_vy = tvx, tvy

    mag = math.hypot(tvx, tvy)

    # Genuine wait/hold.  Reset the stiction timer: zero requested motion is not
    # a stall and must never trigger a torque kick.
    if mag < 10.0:
        if math.hypot(vx, vy) < 8.0:
            r.smooth_vx *= 0.72
            r.smooth_vy *= 0.72
        if math.hypot(r.smooth_vx, r.smooth_vy) < 5.0:
            r.driver.stop_hold()
            r.cmd_speed = 0.0
        r.stall_ref_t = now
        r.stall_ref_x = r.est.x
        r.stall_ref_y = r.est.y
        return

    desired_world = heading_of(tvx, tvy)
    if r.cmd_heading_world is None:
        r.cmd_heading_world = desired_world
    slew = RECOVERY_HEADING_SLEW_DEG_S if recovery else MAX_HEADING_SLEW_DEG_S
    r.cmd_heading_world = angle_step(r.cmd_heading_world, desired_world, slew * dt)

    # v24 adaptive Vicon-speed controller.  The old fixed 2.55 mm/s per
    # command assumption badly over-drove real hardware once friction broke.
    gain = clamp(r.drive_gain_mm_s_per_cmd, DRIVE_GAIN_MIN, DRIVE_GAIN_MAX)
    desired_phys_speed = mag
    speed_err = desired_phys_speed - r.est.speed
    r.drive_speed_i_cmd = clamp(
        r.drive_speed_i_cmd + DRIVE_SPEED_KI_CMD_PER_MM * speed_err * max(1e-3, dt),
        -DRIVE_SPEED_I_MAX_CMD, DRIVE_SPEED_I_MAX_CMD
    )
    cmd_ff = desired_phys_speed / max(0.5, gain)
    cmd = cmd_ff + DRIVE_SPEED_KP_CMD_PER_MM_S * speed_err + r.drive_speed_i_cmd
    cmd = clamp(cmd, min_cmd, max_cmd)
    cmd *= r.speed_scale

    # Learn actual rolling gain only from plausible, already-moving samples.
    if (
        not recovery
        and now >= r.breakaway_until
        and r.cmd_speed >= 30.0
        and DRIVE_GAIN_LEARN_MIN_SPEED <= r.est.speed <= DRIVE_GAIN_LEARN_MAX_SPEED
    ):
        sample_gain = r.est.speed / max(20.0, r.cmd_speed)
        sample_gain = clamp(sample_gain, DRIVE_GAIN_MIN, DRIVE_GAIN_MAX)
        ga = 1.0 - math.exp(-max(1e-4, dt) / DRIVE_GAIN_TC_S)
        r.drive_gain_mm_s_per_cmd += ga * (sample_gain - r.drive_gain_mm_s_per_cmd)
        r.drive_gain_mm_s_per_cmd = clamp(
            r.drive_gain_mm_s_per_cmd, DRIVE_GAIN_MIN, DRIVE_GAIN_MAX
        )

    # ------------------------------------------------------------------
    # Vicon-confirmed stiction detector.
    # ------------------------------------------------------------------
    if r.stall_ref_t < -1e8:
        r.stall_ref_t = now
        r.stall_ref_x = r.est.x
        r.stall_ref_y = r.est.y

    moved = math.hypot(r.est.x - r.stall_ref_x, r.est.y - r.stall_ref_y)
    definitely_moving = moved >= STICTION_MOVE_EPS_MM or r.est.speed >= BREAKAWAY_SPEED_THRESHOLD_MM_S

    if definitely_moving:
        # A recent kick succeeded.  Keep the learned values conservative rather
        # than ratcheting torque upward forever.
        if now - r.last_kick_t < 1.2 and r.est.speed >= 45.0:
            r.learned_breakaway_cmd = max(
                STICTION_KICK_MIN_CMD, r.learned_breakaway_cmd - 0.6
            )
        r.stall_ref_t = now
        r.stall_ref_x = r.est.x
        r.stall_ref_y = r.est.y

    # v24 moving-goal RUN/ENTRY never enters a terminal zone.  Only the
    # legacy TERMINAL_APPROACH mode is treated specially.  This ensures a stuck
    # robot on a moving square receives the full learned breakaway pulse instead
    # of a weak terminal micro-kick.
    terminal_zone = (r.mode == "TERMINAL_APPROACH")
    kick_allowed_mode = r.mode in (
        "HOME", "ENTRY", "RUN", "MOVING_ENTRY", "MOVING_RUN",
        "COLLISION_BUMPER", "TERMINAL_APPROACH", "RECENTER"
    )
    required_stall_mag = 22.0 if terminal_zone else BREAKAWAY_VECTOR_THRESHOLD_MM_S
    high_stiction_history = r.stiction_kicks >= 300
    detect_s = 0.18 if high_stiction_history else STICTION_DETECT_S
    stalled_long_enough = (
        now - r.stall_ref_t >= detect_s
        and moved < STICTION_MOVE_EPS_MM
        and r.est.speed < BREAKAWAY_SPEED_THRESHOLD_MM_S
        and mag >= required_stall_mag
    )

    if (
        kick_allowed_mode
        and not recovery
        and stalled_long_enough
        and now >= r.stiction_cooldown_until
    ):
        # Inside the final capture band we deliberately do NOT kick.  The group
        # corner/entry gate already accepts a robot this close, and a torque
        # pulse here would only create overshoot.
        terminal_kick_ok = (
            terminal_zone
            and STICTION_TERMINAL_KICK_MIN_REMAIN_MM
                < r.rail_remaining_mm
                <= STICTION_TERMINAL_KICK_MAX_REMAIN_MM
        )
        normal_kick_ok = not terminal_zone

        if terminal_kick_ok or normal_kick_ok:
            duration = STICTION_TERMINAL_KICK_S if terminal_kick_ok else (0.15 if high_stiction_history else BREAKAWAY_DURATION_S)
            r.breakaway_until = now + duration
            r.stiction_cooldown_until = now + STICTION_COOLDOWN_S
            r.roll_assist_until = now + (0.82 if high_stiction_history else STICTION_ROLL_ASSIST_S)
            r.last_kick_t = now
            r.stiction_kicks += 1

            # If a second/third kick is required, learn that this chassis needs a
            # little more static-friction torque.  Keep tight bounds.
            if not terminal_kick_ok:
                r.learned_breakaway_cmd = min(
                    STICTION_KICK_MAX_CMD,
                    r.learned_breakaway_cmd + STICTION_KICK_STEP_CMD,
                )
                r.learned_rolling_floor_cmd = min(
                    STICTION_ROLLING_FLOOR_MAX,
                    r.learned_rolling_floor_cmd + 0.8,
                )

            # Start a fresh displacement observation after the pulse.
            r.stall_ref_t = now
            r.stall_ref_x = r.est.x
            r.stall_ref_y = r.est.y

    # A real breakaway pulse MUST bypass the normal speed slew.  Keep the world
    # heading exactly the same constrained trajectory heading.
    if now < r.breakaway_until:
        pulse = (
            STICTION_TERMINAL_KICK_CMD
            if terminal_zone
            else r.learned_breakaway_cmd
        )
        pulse = int(round(clamp(pulse, 0.0, 255.0)))
        world_cmd = wrap360(r.cmd_heading_world + r.formation_trim_deg)
        r.cmd_speed = float(pulse)
        r.driver.command_world(world_cmd, pulse, r.heading_bias_deg)
        r.last_cmd_t = now
        return

    # For a short period after a successful launch, stay above the learned
    # dynamic-friction floor.  This prevents kick -> slow command -> immediate
    # re-stick cycles.  Terminal approach retains its lower, safer floor.
    if now < r.roll_assist_until and not terminal_zone:
        cmd = max(cmd, min(r.learned_rolling_floor_cmd, DRIVE_ROLLING_CMD_MAX))

    # Physical yaw is a secondary safety cue; verified Vicon travelling course
    # remains the steering truth.
    yaw_err = abs(wrap180(r.cmd_heading_world - body_yaw_deg(r)))
    if recovery:
        if yaw_err > 145.0:
            cmd = min(cmd, 105)
        elif yaw_err > 115.0:
            cmd = min(cmd, 125)
    else:
        if yaw_err > 155.0:
            cmd = min(cmd, 115)
        elif yaw_err > 125.0:
            cmd = min(cmd, 140)

    if abs(r.est.yaw_rate_deg_s) > WHIP_YAW_RATE_DEG_S:
        cmd = min(cmd, WHIP_SPEED_CAP)

    if cmd > r.cmd_speed:
        r.cmd_speed = min(cmd, r.cmd_speed + MAX_SPEED_RISE_PER_S * dt)
    else:
        r.cmd_speed = max(cmd, r.cmd_speed - MAX_SPEED_FALL_PER_S * dt)

    if now - r.last_cmd_t >= 1.0 / COMMAND_HZ:
        world_cmd = wrap360(r.cmd_heading_world + r.formation_trim_deg)
        r.driver.command_world(world_cmd, int(round(r.cmd_speed)), r.heading_bias_deg)
        r.last_cmd_t = now

def absolute_slot_commands(
    robots: Sequence[Robot], desired_cx: float, desired_cy: float,
    desired_vx: float, desired_vy: float, max_cmd: int, dt: float,
    phase: str,
) -> Tuple[float, float, float]:
    """Formation-riding controller.

    One dominant shared velocity moves the swarm.  Per-robot correction repairs
    only relative slot error and velocity disagreement.  During ordinary motion,
    those corrections are bounded so a robot cannot suddenly navigate in a
    completely different direction from the other two.  If formation is badly
    stretched, common translation is slowed and correction authority increases.
    """
    sep = collision_vectors(robots)
    cx, cy, cvx, cvy = centroid(robots)
    crms = formation_rms(robots, cx, cy)
    flow = formation_flow_scale(crms)

    # Common translation shared by all robots.  Formation stretch attenuates the
    # centroid chase too; otherwise the centroid target can continue towing the
    # leader away while a straggler is trying to catch up.
    cex = desired_cx - cx
    cey = desired_cy - cy
    common_cx = GROUP_CENTROID_KP * cex + GROUP_CENTROID_KD * (desired_vx - cvx)
    common_cy = GROUP_CENTROID_KP * cey + GROUP_CENTROID_KD * (desired_vy - cvy)
    cmag = math.hypot(common_cx, common_cy)
    if cmag > GROUP_CENTROID_MAX_CORRECTION_MM_S:
        ux, uy = unit(common_cx, common_cy)
        common_cx = ux * GROUP_CENTROID_MAX_CORRECTION_MM_S
        common_cy = uy * GROUP_CENTROID_MAX_CORRECTION_MM_S
    centroid_correction_scale = max(0.28, flow)
    common_vx = desired_vx + common_cx * centroid_correction_scale
    common_vy = desired_vy + common_cy * centroid_correction_scale
    common_mag = math.hypot(common_vx, common_vy)

    min_clear = min(body_edge_clearance(r) for r in robots)
    min_body = min_body_clearance(robots)

    # Shared motion axes used to constrain normal formation corrections.
    if common_mag > 35.0:
        ux, uy = unit(common_vx, common_vy)
    elif math.hypot(desired_vx, desired_vy) > 20.0:
        ux, uy = unit(desired_vx, desired_vy)
    else:
        ux, uy = 1.0, 0.0
    px, py = -uy, ux

    for r in robots:
        rel_x = r.est.x - cx
        rel_y = r.est.y - cy
        rex = r.slot_x - rel_x
        rey = r.slot_y - rel_y
        r.slot_error_mm = math.hypot(rex, rey)

        rel_vx = r.est.vx - cvx
        rel_vy = r.est.vy - cvy

        # Slot spring + explicit velocity consensus.  The latter is what makes
        # the three physical bodies "ride" rather than merely share a centroid.
        fvx = REL_SLOT_KP * rex - REL_SLOT_KD * rel_vx
        fvy = REL_SLOT_KP * rey - REL_SLOT_KD * rel_vy
        avx = clamp(VELOCITY_CONSENSUS_K * (cvx - r.est.vx),
                    -VELOCITY_CONSENSUS_MAX_MM_S, VELOCITY_CONSENSUS_MAX_MM_S)
        avy = clamp(VELOCITY_CONSENSUS_K * (cvy - r.est.vy),
                    -VELOCITY_CONSENSUS_MAX_MM_S, VELOCITY_CONSENSUS_MAX_MM_S)
        fvx += avx
        fvy += avy

        stretched = crms > FORMATION_FLOW_SLOW_RMS_MM or r.slot_error_mm > 180.0
        corr_cap = STRETCHED_SLOT_CORRECTION_MAX_MM_S if stretched else NORMAL_SLOT_CORRECTION_MAX_MM_S
        fmag = math.hypot(fvx, fvy)
        if fmag > corr_cap:
            qx, qy = unit(fvx, fvy)
            fvx, fvy = qx * corr_cap, qy * corr_cap

        # During normal RUN/ENTRY, constrain correction around the group motion.
        # When badly stretched, forward flow has already slowed and we permit
        # stronger direct slot repair.
        if phase in ("RUN", "ENTRY") and not stretched and common_mag > 70.0:
            along = clamp(fvx * ux + fvy * uy,
                          -NORMAL_ALONG_CORRECTION_MAX_MM_S,
                          NORMAL_ALONG_CORRECTION_MAX_MM_S)
            perp = clamp(fvx * px + fvy * py,
                         -NORMAL_PERP_CORRECTION_MAX_MM_S,
                         NORMAL_PERP_CORRECTION_MAX_MM_S)
            fvx = along * ux + perp * px
            fvy = along * uy + perp * py

        svx, svy, body_clear = sep[r.name]
        bvx, bvy, clearance = boundary_vector(r)

        r.dbg_target_x = desired_cx + r.slot_x
        r.dbg_target_y = desired_cy + r.slot_y
        r.dbg_common_vx, r.dbg_common_vy = common_vx, common_vy
        r.dbg_slot_vx, r.dbg_slot_vy = fvx, fvy
        r.dbg_sep_vx, r.dbg_sep_vy = svx, svy
        r.dbg_boundary_vx, r.dbg_boundary_vy = bvx, bvy

        vx = common_vx + fvx + svx + bvx
        vy = common_vy + fvy + svy + bvy

        recovery = (
            phase in ("RECENTER", "HOME")
            or clearance < RECENTER_TRIGGER_MM
            or body_clear < BODY_CLEAR_STRONG_MM
        )
        local_max = max_cmd

        if r.slot_error_mm > 180.0:
            local_max = min(local_max, 138)
        if r.slot_error_mm > 320.0:
            local_max = min(local_max, 112)
        if body_clear < BODY_CLEAR_SOFT_MM:
            local_max = min(local_max, 122)
        if body_clear < BODY_CLEAR_STRONG_MM:
            local_max = min(local_max, 88)
        if body_clear < BODY_CLEAR_CRITICAL_MM:
            local_max = min(local_max, 68)
        if body_clear < BODY_CLEAR_EXTREME_MM:
            local_max = min(local_max, 56)

        if clearance < BOUNDARY_STRONG_MM:
            local_max = min(local_max, 96)
        if clearance < BOUNDARY_CRITICAL_MM:
            local_max = min(local_max, 74)
        if clearance < BOUNDARY_EXTREME_MM:
            local_max = min(local_max, 56)

        if clearance < RECENTER_TRIGGER_MM:
            target_inset = RECENTER_TRIGGER_MM + 180.0
            tx_safe = clamp(r.dbg_target_x, AO_X_MIN_MM + target_inset, AO_X_MAX_MM - target_inset)
            ty_safe = clamp(r.dbg_target_y, AO_Y_MIN_MM + target_inset, AO_Y_MAX_MM - target_inset)
            dx_in, dy_in = tx_safe - r.est.x, ty_safe - r.est.y
            dist_in = math.hypot(dx_in, dy_in)
            ivx, ivy = unit(dx_in, dy_in)
            inward_speed = clamp(1.15 * dist_in, 105.0, 330.0)
            vx = inward_speed * ivx + 0.90 * svx + 0.55 * bvx
            vy = inward_speed * ivy + 0.90 * svy + 0.55 * bvy
            local_max = min(local_max, 108)
            r.mode = "BOUNDARY_RECOVER"
            recovery = True
        elif body_clear < BODY_CLEAR_CRITICAL_MM:
            # Local separation is the only normal condition allowed to break
            # velocity consensus abruptly.
            vx = 0.22 * common_vx + 1.25 * svx
            vy = 0.22 * common_vy + 1.25 * svy
            r.mode = "BODY_SEPARATE"
            recovery = True
        else:
            r.mode = phase

        # Final heading-consensus guard: when healthy and moving, do not let an
        # individual command diverge wildly from the shared swarm direction.
        if (
            phase in ("RUN", "ENTRY")
            and not recovery
            and common_mag > 90.0
            and math.hypot(vx, vy) > 25.0
        ):
            h_common = heading_of(common_vx, common_vy)
            h_local = heading_of(vx, vy)
            dh = clamp(wrap180(h_local - h_common),
                       -MAX_ROBOT_HEADING_DEVIATION_FROM_SWARM_DEG,
                       MAX_ROBOT_HEADING_DEVIATION_FROM_SWARM_DEG)
            h_limited = math.radians(wrap360(h_common + dh))
            vmag = math.hypot(vx, vy)
            vx, vy = vmag * math.cos(h_limited), vmag * math.sin(h_limited)

        r.dbg_final_vx, r.dbg_final_vy = vx, vy
        command_robot(r, vx, vy, local_max, dt, recovery)

    return min_clear, pair_min(robots), min_body


def formation_flow_scale(crms: float) -> float:
    """Formation-first translation gate.

    v13 still allowed a visually broken formation to travel around the square.
    an earlier revision nearly stops shared progression when the triangle is badly stretched,
    while relative-position and velocity-consensus terms keep working.
    """
    if crms <= FORMATION_FLOW_FULL_RMS_MM:
        return 1.0
    if crms >= FORMATION_FLOW_HOLD_RMS_MM:
        return FORMATION_FLOW_MIN_SCALE
    if crms <= FORMATION_FLOW_SLOW_RMS_MM:
        q = (crms - FORMATION_FLOW_FULL_RMS_MM) / max(
            1.0, FORMATION_FLOW_SLOW_RMS_MM - FORMATION_FLOW_FULL_RMS_MM
        )
        return 1.0 - 0.62 * clamp(q, 0.0, 1.0)
    q = (crms - FORMATION_FLOW_SLOW_RMS_MM) / max(
        1.0, FORMATION_FLOW_HOLD_RMS_MM - FORMATION_FLOW_SLOW_RMS_MM
    )
    return 0.38 - (0.38 - FORMATION_FLOW_MIN_SCALE) * clamp(q, 0.0, 1.0)


def body_flow_scale(body_clear_mm: float) -> float:
    """Pause shared translation before physical padded bodies can collide."""
    if body_clear_mm >= BODY_CLEAR_SOFT_MM:
        return 1.0
    if body_clear_mm <= BODY_CLEAR_CRITICAL_MM:
        return 0.08
    q = clamp((body_clear_mm - BODY_CLEAR_CRITICAL_MM) / max(1.0, BODY_CLEAR_SOFT_MM - BODY_CLEAR_CRITICAL_MM), 0.0, 1.0)
    return 0.08 + 0.92 * q


def guide_state_for_side(
    corners: Sequence[Tuple[float, float]], side_idx: int, guide_s: float,
) -> Tuple[float, float, float, float, float]:
    """Return virtual-centroid x,y,tangent-x,tangent-y,remaining on side."""
    a = corners[side_idx]
    b = corners[(side_idx + 1) % 4]
    tx, ty = unit(b[0] - a[0], b[1] - a[1])
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ss = clamp(guide_s, 0.0, L)
    return a[0] + tx * ss, a[1] + ty * ss, tx, ty, L - ss


def square_cross_track(cx: float, cy: float, corners: Sequence[Tuple[float, float]], side_idx: int) -> float:
    a = corners[side_idx]
    b = corners[(side_idx + 1) % 4]
    tx, ty = unit(b[0] - a[0], b[1] - a[1])
    nx, ny = -ty, tx
    return (cx - a[0]) * nx + (cy - a[1]) * ny

def square_midpoint_route(side_mm: float) -> List[Tuple[float, float]]:
    """Closed square route starting/ending at the bottom-side midpoint.

    Starting at the midpoint avoids the v9 guide teleport while still tracing
    exactly one 1600 x 1600 mm square per route cycle.  Five straight segments
    are required because the bottom side is split around the chosen start point.
    """
    h = 0.5 * side_mm
    return [
        (0.0, -h),
        (+h, -h),
        (+h, +h),
        (-h, +h),
        (-h, -h),
        (0.0, -h),
    ]


def guide_state_for_segment(
    route: Sequence[Tuple[float, float]], segment_idx: int, guide_s: float,
) -> Tuple[float, float, float, float, float]:
    a = route[segment_idx]
    b = route[segment_idx + 1]
    tx, ty = unit(b[0] - a[0], b[1] - a[1])
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ss = clamp(guide_s, 0.0, L)
    return a[0] + tx * ss, a[1] + ty * ss, tx, ty, L - ss


def segment_cross_track(
    cx: float, cy: float, route: Sequence[Tuple[float, float]], segment_idx: int,
) -> float:
    a = route[segment_idx]
    b = route[segment_idx + 1]
    tx, ty = unit(b[0] - a[0], b[1] - a[1])
    nx, ny = -ty, tx
    return (cx - a[0]) * nx + (cy - a[1]) * ny


def line_follow_reference(
    cx: float, cy: float, cvx: float, cvy: float,
    a: Tuple[float, float], b: Tuple[float, float],
    lookahead_mm: float = LINE_LOOKAHEAD_MM,
) -> Tuple[float, float, float, float, float, float, bool]:
    """Reference tied to ACTUAL Vicon progress on one straight segment.

    Returns guide_x, guide_y, guide_vx, guide_vy, cross_track, endpoint_distance,
    passed_endpoint.  Because along-track progress comes from the measured
    centroid, the reference cannot run around the square ahead of the robots.
    """
    tx, ty = unit(b[0]-a[0], b[1]-a[1])
    nx, ny = -ty, tx
    L = math.hypot(b[0]-a[0], b[1]-a[1])
    rx, ry = cx-a[0], cy-a[1]
    along = rx*tx + ry*ty
    cross = rx*nx + ry*ny
    proj = clamp(along, 0.0, L)
    guide_along = min(L, proj + lookahead_mm)
    gx, gy = a[0] + tx*guide_along, a[1] + ty*guide_along
    remaining = max(0.0, L-proj)

    # Keep straight-line appearance: large cross-track error removes forward
    # authority until the centroid returns to the corridor.
    if abs(cross) <= LINE_CROSS_SLOW_MM:
        cross_factor = 1.0
    elif abs(cross) >= LINE_CROSS_HARD_MM:
        cross_factor = 0.12
    else:
        cross_factor = 1.0 - 0.88 * (abs(cross)-LINE_CROSS_SLOW_MM) / (LINE_CROSS_HARD_MM-LINE_CROSS_SLOW_MM)

    if remaining < LINE_CORNER_APPROACH_MM:
        q = clamp(remaining/LINE_CORNER_APPROACH_MM, 0.0, 1.0)
        base_speed = LINE_CORNER_SPEED_MM_S + (LINE_CRUISE_MM_S-LINE_CORNER_SPEED_MM_S)*q
    else:
        base_speed = LINE_CRUISE_MM_S
    speed = base_speed * cross_factor
    gvx, gvy = speed*tx, speed*ty
    endpoint_dist = math.hypot(cx-b[0], cy-b[1])
    passed = along >= L + LINE_PASS_MARGIN_MM
    return gx, gy, gvx, gvy, cross, endpoint_dist, passed


def update_runtime_course_lock(robots: Sequence[Robot], dt: float, aggressive: bool) -> None:
    """Diagnostics-only travelling-course watchdog.

    v17 rewrote heading_bias_deg during RUN and one hardware robot spent ~75% of
    RUN in COURSE_CORRECT.  Once startup two-axis verification passes, v18 treats
    that mapping as immutable for the mission.  We still measure realised course
    for the ATC twin/log, but never change the verified trim here.
    """
    now = time.monotonic()
    for r in robots:
        if r.cmd_heading_world is None:
            continue
        if r.course_ref_heading_deg is None or abs(wrap180(r.cmd_heading_world-r.course_ref_heading_deg)) > 10.0:
            r.course_ref_heading_deg = r.cmd_heading_world
            r.course_ref_since = now
            continue
        if now-r.course_ref_since < max(0.45, COURSE_RUNTIME_STABLE_CMD_S):
            continue
        if r.cmd_speed < 70.0:
            continue
        course = measured_course_from_history(r.est)
        if course is None:
            continue
        r.measured_course_deg = course
        r.course_error_deg = wrap180(r.cmd_heading_world-course)
        # Intentionally NO heading_bias update here.

def update_learning(robots: Sequence[Robot], centroid_v_cmd: Tuple[float, float], dt: float, clean: bool) -> None:
    """Learn persistent *formation* feed-forward only from clean straight motion.

    Startup verification owns the large course calibration.  Runtime learning
    here is intentionally slow: speed scale removes systematic fore/aft lag and
    a bounded +/-8 deg formation trim removes systematic lateral slot bias.
    """
    if not clean or math.hypot(*centroid_v_cmd) < LEARNING_MIN_SPEED_MM_S:
        return

    ux, uy = unit(*centroid_v_cmd)
    px, py = -uy, ux
    cx, cy, _, _ = centroid(robots)
    alpha = 1.0 - math.exp(-max(1e-4, dt) / FORMATION_ERROR_EMA_TC_S)

    for r in robots:
        ex = (cx + r.slot_x) - r.est.x
        ey = (cy + r.slot_y) - r.est.y
        along_err = ex * ux + ey * uy
        cross_err = ex * px + ey * py
        r.learn_along_ema += alpha * (along_err - r.learn_along_ema)
        r.learn_cross_ema += alpha * (cross_err - r.learn_cross_ema)

        # Behind slot -> slightly more speed; ahead -> slightly less.
        r.speed_scale = clamp(
            r.speed_scale + SPEED_SCALE_RATE * r.learn_along_ema * dt,
            SPEED_SCALE_MIN, SPEED_SCALE_MAX,
        )

        # Small lateral feed-forward.  Convert persistent cross error into a
        # desired heading offset relative to shared motion.
        target_trim = clamp(
            math.degrees(math.atan2(0.26 * r.learn_cross_ema, max(120.0, math.hypot(*centroid_v_cmd)))),
            -FORMATION_TRIM_MAX_DEG, FORMATION_TRIM_MAX_DEG,
        )
        max_step = FORMATION_TRIM_RATE * dt
        r.formation_trim_deg += clamp(target_trim - r.formation_trim_deg, -max_step, max_step)
        r.formation_trim_deg = clamp(r.formation_trim_deg, -FORMATION_TRIM_MAX_DEG, FORMATION_TRIM_MAX_DEG)
        r.learning_samples += 1





# =============================================================================
# v16 centroid-locked translated-square Frenet controller
# =============================================================================

def _median(vals: Sequence[float]) -> float:
    ss = sorted(float(v) for v in vals)
    n = len(ss)
    if n == 0:
        return 0.0
    return ss[n//2] if n % 2 else 0.5 * (ss[n//2-1] + ss[n//2])


def translated_segment(
    r: Robot, a: Tuple[float, float], b: Tuple[float, float]
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """The robot's own square rail is the global square translated by its fixed slot."""
    return (a[0] + r.slot_x, a[1] + r.slot_y), (b[0] + r.slot_x, b[1] + r.slot_y)


def robot_rail_state(
    r: Robot, a: Tuple[float, float], b: Tuple[float, float]
) -> Dict[str, float]:
    """Project one robot onto its OWN translated straight corridor."""
    ar, br = translated_segment(r, a, b)
    tx, ty = unit(br[0] - ar[0], br[1] - ar[1])
    nx, ny = -ty, tx
    L = math.hypot(br[0] - ar[0], br[1] - ar[1])
    rx, ry = r.est.x - ar[0], r.est.y - ar[1]
    along = rx * tx + ry * ty
    cross = rx * nx + ry * ny
    along_v = r.est.vx * tx + r.est.vy * ty
    cross_v = r.est.vx * nx + r.est.vy * ny
    proj = clamp(along, 0.0, L)
    remaining = max(0.0, L - proj)
    endpoint_dist = math.hypot(r.est.x - br[0], r.est.y - br[1])
    return {
        "ax": ar[0], "ay": ar[1], "bx": br[0], "by": br[1],
        "tx": tx, "ty": ty, "nx": nx, "ny": ny, "L": L,
        "along": along, "proj": proj, "cross": cross,
        "along_v": along_v, "cross_v": cross_v,
        "remaining": remaining, "endpoint_dist": endpoint_dist,
    }


def rail_progress_flow(spread_mm: float, crms: float, body_clear_mm: float) -> float:
    """Shared speed gate only; it never generates a steering direction.

    The square rails are always the steering authority.  This factor simply
    slows all three robots when their along-track progress separates.
    """
    if spread_mm <= RAIL_PROGRESS_FULL_SPREAD_MM:
        s = 1.0
    elif spread_mm >= RAIL_PROGRESS_HOLD_SPREAD_MM:
        s = RAIL_FLOW_MIN
    elif spread_mm <= RAIL_PROGRESS_SLOW_SPREAD_MM:
        q = (spread_mm - RAIL_PROGRESS_FULL_SPREAD_MM) / max(
            1.0, RAIL_PROGRESS_SLOW_SPREAD_MM - RAIL_PROGRESS_FULL_SPREAD_MM
        )
        s = 1.0 - 0.52 * clamp(q, 0.0, 1.0)
    else:
        q = (spread_mm - RAIL_PROGRESS_SLOW_SPREAD_MM) / max(
            1.0, RAIL_PROGRESS_HOLD_SPREAD_MM - RAIL_PROGRESS_SLOW_SPREAD_MM
        )
        s = 0.48 - (0.48 - RAIL_FLOW_MIN) * clamp(q, 0.0, 1.0)

    # Formation RMS is diagnostic, but a very distorted group should not be
    # allowed to sprint away.  This affects magnitude only, never direction.
    if crms > 220.0:
        s = min(s, 0.42)
    if crms > 360.0:
        s = min(s, 0.22)
    if body_clear_mm < BODY_CLEAR_SOFT_MM:
        s = min(s, body_flow_scale(body_clear_mm))
    return clamp(s, RAIL_FLOW_MIN, 1.0)


def point_slot_commands(
    robots: Sequence[Robot], center_x: float, center_y: float,
    max_cmd: int, dt: float,
) -> Tuple[float, float, float, float]:
    """Direct HOME point control.  Centroid is not used to generate commands."""
    sep = collision_vectors(robots)
    max_err = 0.0
    for r in robots:
        tx = center_x + r.slot_x
        ty = center_y + r.slot_y
        ex, ey = tx - r.est.x, ty - r.est.y
        err = math.hypot(ex, ey)
        max_err = max(max_err, err)
        vx = RAIL_HOME_KP * ex - RAIL_HOME_KD * r.est.vx
        vy = RAIL_HOME_KP * ey - RAIL_HOME_KD * r.est.vy
        mag = math.hypot(vx, vy)
        if mag > RAIL_HOME_MAX_MM_S:
            ux, uy = unit(vx, vy)
            vx, vy = ux * RAIL_HOME_MAX_MM_S, uy * RAIL_HOME_MAX_MM_S

        svx, svy, body_clear = sep[r.name]
        bvx, bvy, clearance = boundary_vector(r)
        r.dbg_target_x, r.dbg_target_y = tx, ty
        r.dbg_common_vx = r.dbg_common_vy = 0.0
        r.dbg_slot_vx, r.dbg_slot_vy = vx, vy
        r.dbg_sep_vx, r.dbg_sep_vy = svx, svy
        r.dbg_boundary_vx, r.dbg_boundary_vy = bvx, bvy
        r.slot_error_mm = err

        recovery = clearance < RECENTER_TRIGGER_MM or body_clear < BODY_CLEAR_STRONG_MM
        local_max = max_cmd
        if body_clear < BODY_CLEAR_STRONG_MM:
            vx, vy = 0.22 * vx + 1.25 * svx, 0.22 * vy + 1.25 * svy
            local_max = min(local_max, 82)
            r.mode = "BODY_SEPARATE"
            recovery = True
        elif clearance < RECENTER_TRIGGER_MM:
            vx, vy = 0.25 * vx + 1.20 * bvx, 0.25 * vy + 1.20 * bvy
            local_max = min(local_max, 92)
            r.mode = "BOUNDARY_RECOVER"
            recovery = True
        else:
            vx += 0.55 * svx + 0.45 * bvx
            vy += 0.55 * svy + 0.45 * bvy
            r.mode = "HOME"

        r.dbg_final_vx, r.dbg_final_vy = vx, vy
        command_robot(r, vx, vy, local_max, dt, recovery)
    return max_err, pair_min(robots), min_body_clearance(robots), min(body_edge_clearance(r) for r in robots)


def direct_rail_commands(
    robots: Sequence[Robot],
    a: Tuple[float, float], b: Tuple[float, float],
    max_cmd: int, dt: float, phase: str,
    boundary_hold: bool = False,
) -> Dict[str, float]:
    """Hard square-corridor formation controller.

    v20 gives endpoint-gated trajectory geometry higher priority than every
    formation/safety correction except the extended-AO guard.

    Key rules:
      * all three robots travel only FORWARD along the active square side;
      * the SLOWEST robot defines shared progress;
      * robots ahead WAIT instead of reversing/turning around;
      * cross-track steering is confined to a narrow cone about the side tangent;
      * collision avoidance is a small short-range bumper, never a flocking force.
    """
    states = {r.name: robot_rail_state(r, a, b) for r in robots}
    st0 = states[robots[0].name]
    tx, ty, nx, ny, L = st0["tx"], st0["ty"], st0["nx"], st0["ny"], st0["L"]

    raw_progresses = [states[r.name]["along"] for r in robots]
    slow_progress = min(raw_progresses)
    fast_progress = max(raw_progresses)
    spread = fast_progress - slow_progress
    group_progress = clamp(slow_progress, 0.0, L)

    # "All robots have arrived" is represented by the slowest robot's remaining
    # distance. A leader beyond the corner cannot trick the side state forward.
    group_remaining_raw = L - slow_progress
    group_remaining = max(0.0, group_remaining_raw)

    # Shared forward schedule. Slow down the complete formation before corners.
    if group_remaining < FRENET_CORNER_APPROACH_MM:
        q = clamp(group_remaining / max(1.0, FRENET_CORNER_APPROACH_MM), 0.0, 1.0)
        base = FRENET_CORNER_SPEED_MM_S + (FRENET_CRUISE_MM_S - FRENET_CORNER_SPEED_MM_S) * q
    else:
        base = FRENET_CRUISE_MM_S

    # If the group stretches, do NOT reverse leaders. Slow the common pace while
    # the ahead robots are individually held and the slowest continues forward.
    if spread <= FRENET_PROGRESS_FULL_SPREAD_MM:
        spread_scale = 1.0
    elif spread <= FRENET_PROGRESS_SLOW_SPREAD_MM:
        q = (spread - FRENET_PROGRESS_FULL_SPREAD_MM) / max(
            1.0, FRENET_PROGRESS_SLOW_SPREAD_MM - FRENET_PROGRESS_FULL_SPREAD_MM
        )
        spread_scale = 1.0 - 0.25 * clamp(q, 0.0, 1.0)
    elif spread <= FRENET_PROGRESS_BAD_SPREAD_MM:
        q = (spread - FRENET_PROGRESS_SLOW_SPREAD_MM) / max(
            1.0, FRENET_PROGRESS_BAD_SPREAD_MM - FRENET_PROGRESS_SLOW_SPREAD_MM
        )
        spread_scale = 0.75 - 0.35 * clamp(q, 0.0, 1.0)
    else:
        spread_scale = 0.32

    base = max(FRENET_MIN_BASE_MM_S, base * spread_scale)
    if boundary_hold:
        base = 0.0

    cx, cy, cvx, cvy = centroid(robots)
    center_cross = (cx - a[0]) * nx + (cy - a[1]) * ny

    along_vels = [states[r.name]["along_v"] for r in robots]
    # Use velocity of the current slowest robot as the sync velocity reference.
    slow_name = min(robots, key=lambda rr: states[rr.name]["along"]).name
    slow_v = states[slow_name]["along_v"]
    sep = collision_vectors(robots)

    max_abs_cross = 0.0
    max_remaining = 0.0
    max_endpoint = 0.0

    for r in robots:
        st = states[r.name]
        along = st["along"]
        cross = st["cross"]
        remaining = L - along
        max_abs_cross = max(max_abs_cross, abs(cross))
        max_remaining = max(max_remaining, remaining)
        max_endpoint = max(max_endpoint, st["endpoint_dist"])

        # Ahead-gap synchronisation. The slowest gets the shared pace; leaders
        # progressively yield speed and eventually stop. NO reverse is allowed.
        ahead = max(0.0, along - slow_progress)
        rel_v = st["along_v"] - slow_v
        sync_reduce = FRENET_SYNC_KP * ahead + FRENET_SYNC_KD * max(0.0, rel_v)
        sync_reduce = clamp(sync_reduce, 0.0, FRENET_SYNC_MAX_MM_S)
        forward = max(0.0, base - sync_reduce)

        # Strong leader hold once clearly ahead.  This is what keeps the three
        # Chariots abreast without ever commanding a 180-degree turnaround.
        if ahead > 180.0:
            q = clamp((ahead - 180.0) / 160.0, 0.0, 1.0)
            forward *= (1.0 - q)
        if ahead >= 340.0:
            forward = 0.0
        if boundary_hold:
            forward = 0.0

        # v20 ENDPOINT GATE.  v19 could set forward=0 yet continue rolling
        # through ENTRY/corners because a lateral correction still produced the
        # global MIN_MOVING_CMD.  Slow each robot against ITS OWN remaining
        # distance, then hard-stop it inside the terminal capture zone.
        remaining_raw = L - along
        terminal_approach = remaining_raw <= TERMINAL_SLOWDOWN_MM
        if terminal_approach and remaining_raw > TERMINAL_HOLD_REMAINING_MM:
            terminal_forward_cap = clamp(
                TERMINAL_FORWARD_GAIN * (remaining_raw - TERMINAL_HOLD_REMAINING_MM),
                0.0, TERMINAL_MAX_FORWARD_MM_S
            )
            forward = min(forward, terminal_forward_cap)

        terminal_capture = (
            remaining_raw <= TERMINAL_HOLD_REMAINING_MM
            and abs(cross) <= TERMINAL_HOLD_CROSS_MM
        )
        terminal_past = remaining_raw <= -TERMINAL_FORCE_STOP_PAST_MM
        terminal_brake = (
            terminal_approach
            and remaining_raw <= TERMINAL_HIGH_SPEED_REMAINING_MM
            and st["along_v"] >= TERMINAL_HIGH_SPEED_MM_S
            and abs(cross) <= TERMINAL_HOLD_CROSS_MM + 45.0
        )

        if (terminal_capture or terminal_past or terminal_brake) and not boundary_hold:
            # Bypass the normal vector inertia/minimum-speed floor. speed=0 is
            # the chariot's active hold/brake; it must not keep creeping while
            # the other robots catch up.  A high-speed brake can release again
            # after Vicon confirms the robot has slowed, unless it is already in
            # the capture zone.
            r.smooth_vx = r.smooth_vy = 0.0
            r.driver.stop_hold()
            r.cmd_speed = 0.0
            r.cmd_heading_world = heading_of(tx, ty)
            r.mode = "ENTRY_HOLD" if phase == "ENTRY" else "CORNER_HOLD"
            r.rail_along_mm = along
            r.rail_cross_mm = cross
            r.rail_remaining_mm = remaining_raw
            r.rail_forward_cmd = 0.0
            r.rail_sync_cmd = -sync_reduce
            r.rail_target_x, r.rail_target_y = st["bx"], st["by"]
            r.dbg_target_x, r.dbg_target_y = st["bx"], st["by"]
            r.dbg_common_vx = r.dbg_common_vy = 0.0
            r.dbg_slot_vx = r.dbg_slot_vy = 0.0
            svx, svy, _bc = sep[r.name]
            bvx, bvy, _ec = boundary_vector(r)
            r.dbg_sep_vx, r.dbg_sep_vy = svx, svy
            r.dbg_boundary_vx, r.dbg_boundary_vy = bvx, bvy
            r.dbg_final_vx = r.dbg_final_vy = 0.0
            r.slot_error_mm = math.hypot(st["bx"] - r.est.x, st["by"] - r.est.y)
            continue

        # Rail correction with a deadband to prevent left-right chatter.
        dead = 14.0
        if abs(cross) <= dead:
            cross_eff = 0.0
        else:
            cross_eff = math.copysign(abs(cross) - dead, cross)
        cross_cmd = -FRENET_REL_CROSS_KP * cross_eff - FRENET_REL_CROSS_KD * st["cross_v"]
        cross_cmd = clamp(cross_cmd, -FRENET_CROSS_MAX_MM_S, +FRENET_CROSS_MAX_MM_S)

        # Hard corridor behaviour: when far off the rail, stop advancing quickly
        # and devote the available steering cone to rejoining it.
        if abs(cross) > 120.0:
            forward = min(forward, 72.0)
        if abs(cross) > 220.0:
            forward = min(forward, 48.0)
        if abs(cross) > 360.0:
            forward = min(forward, 32.0)

        # A waiting leader with cross-track error may creep forward slowly while
        # correcting laterally; otherwise it simply holds and lets peers catch.
        if forward < 8.0 and abs(cross) > 55.0 and not boundary_hold:
            forward = 26.0

        # Enforce a narrow heading cone around the ACTIVE SQUARE SIDE before
        # adding the tiny collision bumper.
        cone = FRENET_HEADING_DEVIATION_RECOVER_DEG if abs(cross) > 170.0 else FRENET_HEADING_DEVIATION_DEG
        lateral_cap = math.tan(math.radians(cone)) * max(26.0, forward)
        cross_cmd = clamp(cross_cmd, -lateral_cap, +lateral_cap)

        vx = forward * tx + cross_cmd * nx
        vy = forward * ty + cross_cmd * ny

        svx, svy, body_clear = sep[r.name]
        bvx, bvy, clearance = boundary_vector(r)
        local_max = max_cmd
        recovery = False

        # Collision is now only a bumper.  It cannot reverse the side tangent.
        if body_clear < -12.0:
            vx = 0.90 * vx + 0.22 * svx
            vy = 0.90 * vy + 0.22 * svy
            local_max = min(local_max, 78)
            r.mode = "BODY_SEPARATE"
        elif clearance < RECENTER_TRIGGER_MM:
            # Boundary safety is the one authority allowed to leave the square
            # corridor substantially.
            vx = 0.42 * vx + 0.95 * bvx
            vy = 0.42 * vy + 0.95 * bvy
            local_max = min(local_max, 88)
            r.mode = "BOUNDARY_RECOVER"
            recovery = True
        else:
            vx += 0.025 * svx + 0.035 * bvx
            vy += 0.025 * svy + 0.035 * bvy
            r.mode = phase

        # Re-apply square-side heading cone after the collision bumper unless
        # the extended-AO boundary is actively recovering the robot.
        if not recovery and math.hypot(vx, vy) > 8.0:
            h_side = heading_of(tx, ty)
            h_cmd = heading_of(vx, vy)
            safe_cone = 42.0 if r.mode == "BODY_SEPARATE" else cone
            dh = clamp(wrap180(h_cmd - h_side), -safe_cone, +safe_cone)
            vm = math.hypot(vx, vy)
            hm = math.radians(wrap360(h_side + dh))
            vx, vy = vm * math.cos(hm), vm * math.sin(hm)

        # Shared target uses the slowest robot, not the median/leader.
        target_along = clamp(slow_progress + FRENET_LOOKAHEAD_MM, 0.0, L)
        r.rail_target_x = st["ax"] + tx * target_along
        r.rail_target_y = st["ay"] + ty * target_along
        r.dbg_target_x, r.dbg_target_y = r.rail_target_x, r.rail_target_y
        r.dbg_common_vx, r.dbg_common_vy = base * tx, base * ty
        r.dbg_slot_vx, r.dbg_slot_vy = -sync_reduce * tx + cross_cmd * nx, -sync_reduce * ty + cross_cmd * ny
        r.dbg_sep_vx, r.dbg_sep_vy = svx, svy
        r.dbg_boundary_vx, r.dbg_boundary_vy = bvx, bvy
        r.dbg_final_vx, r.dbg_final_vy = vx, vy
        r.rail_along_mm = along
        r.rail_cross_mm = cross
        r.rail_remaining_mm = remaining
        r.rail_forward_cmd = forward
        r.rail_sync_cmd = -sync_reduce

        # Formation target is the common SLOWEST progress.  Ahead robots have a
        # meaningful slot error until the group catches them.
        form_s = clamp(slow_progress, 0.0, L)
        fx = st["ax"] + tx * form_s
        fy = st["ay"] + ty * form_s
        r.slot_error_mm = math.hypot(fx - r.est.x, fy - r.est.y)

        if abs(cross) > 180.0:
            local_max = min(local_max, 108)
        if abs(cross) > 320.0:
            local_max = min(local_max, 88)

        # While translating on a side, keep a small learned rolling floor.
        # Leaders that should genuinely wait have forward~0 and are stopped by
        # the vector-magnitude/endpoint logic, so this floor does not make them
        # run through corners.
        min_cmd_this = max(MIN_MOVING_CMD, r.learned_rolling_floor_cmd)
        if terminal_approach and not recovery:
            # Once already rolling, allow a genuinely slow terminal creep.
            # Do not invoke the ENTRY breakaway pulse in this region.
            min_cmd_this = TERMINAL_CREEP_MIN_CMD if remaining_raw > 105.0 else TERMINAL_LOW_MIN_CMD
            if r.mode == phase:
                r.mode = "TERMINAL_APPROACH"

        command_robot(r, vx, vy, local_max, dt, recovery, min_cmd=min_cmd_this)

    flow = clamp(base / max(1.0, FRENET_CRUISE_MM_S), 0.0, 1.0)
    return {
        "group_progress": slow_progress,
        "group_progress_clamped": group_progress,
        "group_remaining": group_remaining,
        "spread": spread,
        "flow": flow,
        "center_cross": center_cross,
        "max_abs_cross": max_abs_cross,
        "max_remaining": max_remaining,
        "max_endpoint_dist": max_endpoint,
        "body_min": min_body_clearance(robots),
        "pair_min": pair_min(robots),
        "min_edge": min(body_edge_clearance(r) for r in robots),
        "L": L,
        "tx": tx, "ty": ty,
    }

def update_rail_learning(
    robots: Sequence[Robot], dt: float, clean: bool,
) -> None:
    """Learn only tiny per-robot SPEED feed-forward corrections.

    v20 intentionally does not learn steering during the mission.  The verified
    command->Vicon heading map is frozen, so path geometry cannot drift over time.
    """
    if not clean:
        return
    progresses = [r.rail_along_mm for r in robots]
    ref = min(progresses)
    alpha = 1.0 - math.exp(-max(1e-4, dt) / RAIL_ERROR_EMA_TC_S)

    for r in robots:
        # Positive lag means this robot is the slow member and may receive a very
        # small persistent speed increase on future clean straight sections.
        lag = max(0.0, _median(progresses) - r.rail_along_mm)
        r.learn_along_ema += alpha * (lag - r.learn_along_ema)
        r.learn_cross_ema += alpha * (0.0 - r.learn_cross_ema)

        r.speed_scale = clamp(
            r.speed_scale + 0.35 * RAIL_SPEED_SCALE_RATE * r.learn_along_ema * dt,
            0.985, 1.015,
        )
        r.formation_trim_deg = 0.0
        r.learning_samples += 1

_DT_PALETTE = ["#ff7b72", "#79c0ff", "#d2a8ff", "#ffa657", "#7ee787"]


def _digital_twin_process_main(snap_q, side_mm: float, slot_map: dict, robot_meta: list) -> None:
    """Tkinter lives in its own spawned process so Windows UI work can never block control."""
    try:
        _TwinDashboard(snap_q, side_mm, slot_map, robot_meta).run()
    except Exception as exc:
        print(f"Digital twin process unavailable ({type(exc).__name__}: {exc}); robot control continues.")


class _TwinDashboard:
    def __init__(self, snap_q, side_mm: float, slot_map: dict, robot_meta: list) -> None:
        import tkinter as tk
        self.tk = tk
        self.snap_q = snap_q
        self.side_mm = side_mm
        self.slot_map = slot_map
        self.robot_meta = robot_meta
        self.robot_order = [r[0] for r in robot_meta]
        self.friendly = {r[0]: r[1] for r in robot_meta}
        self.colors = {name: _DT_PALETTE[i % len(_DT_PALETTE)] for i, name in enumerate(self.robot_order)}
        self.trails = {name: deque(maxlen=DIGITAL_TWIN_TRAIL_POINTS) for name in self.robot_order}
        self.centroid_trail = deque(maxlen=DIGITAL_TWIN_TRAIL_POINTS)
        self._static_size = None
        self._last_snap_t = None
        self._ui_hz = 0.0
        self._last_kicks = {name: 0 for name in self.robot_order}
        self._events = deque(maxlen=5)
        self.fullscreen = False
        self.snap = None

    def run(self) -> None:
        tk = self.tk
        root = tk.Tk()
        self.root = root
        root.title("SWARM ATC // VICON LIVE // reference")
        root.geometry(f"{DIGITAL_TWIN_WIDTH}x{DIGITAL_TWIN_HEIGHT}")
        root.minsize(1280, 760)
        root.configure(bg="#05090d")
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # Professional top command strip.
        top = tk.Frame(root, bg="#08131c", height=66, padx=18, pady=8)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=0)
        self.title_var = tk.StringVar(value="SWARM TRAFFIC CONTROL  //  VICON LIVE")
        tk.Label(top, textvariable=self.title_var, bg="#08131c", fg="#8bffbd",
                 font=("Segoe UI", 17, "bold"), anchor="w").grid(row=0, column=0, sticky="w")
        self.subtitle_var = tk.StringVar(value="TETHERED LOOKAHEAD FORMATION DIRECTOR  •  WAITING FOR TELEMETRY")
        tk.Label(top, textvariable=self.subtitle_var, bg="#08131c", fg="#7d9cab",
                 font=("Consolas", 9, "bold"), anchor="w").grid(row=1, column=0, sticky="w", pady=(2,0))
        self.clock_var = tk.StringVar(value="--:--:--")
        tk.Label(top, textvariable=self.clock_var, bg="#08131c", fg="#c9d1d9",
                 font=("Consolas", 11, "bold"), anchor="e").grid(row=0, column=1, rowspan=2, sticky="e")

        body = tk.Frame(root, bg="#05090d", padx=10, pady=10)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=3, minsize=720)
        body.grid_columnconfigure(1, weight=2, minsize=500)

        # Radar/map area.
        radar_frame = tk.Frame(body, bg="#07120f", highlightbackground="#1d493b", highlightthickness=1)
        radar_frame.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        radar_frame.grid_rowconfigure(1, weight=1)
        radar_frame.grid_columnconfigure(0, weight=1)
        radar_hdr = tk.Frame(radar_frame, bg="#0a1914", padx=10, pady=5)
        radar_hdr.grid(row=0, column=0, sticky="ew")
        radar_hdr.grid_columnconfigure(0, weight=1)
        self.radar_title_var = tk.StringVar(value="TACTICAL PLAN VIEW")
        tk.Label(radar_hdr, textvariable=self.radar_title_var, bg="#0a1914", fg="#90e6bd",
                 font=("Consolas", 10, "bold"), anchor="w").grid(row=0, column=0, sticky="w")
        self.radar_age_var = tk.StringVar(value="NO DATA")
        tk.Label(radar_hdr, textvariable=self.radar_age_var, bg="#0a1914", fg="#7d9cab",
                 font=("Consolas", 9), anchor="e").grid(row=0, column=1, sticky="e")
        self.canvas = tk.Canvas(radar_frame, bg="#03110d", highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew")

        # Right information stack.
        side = tk.Frame(body, bg="#05090d")
        side.grid(row=0, column=1, sticky="nsew")
        side.grid_columnconfigure(0, weight=1)
        side.grid_rowconfigure(3, weight=1)

        self.mission_var = tk.StringVar(value="WAITING FOR LIVE VICON SNAPSHOT")
        mission = tk.Label(side, textvariable=self.mission_var, justify="left", anchor="w",
                           bg="#0d1720", fg="#e6edf3", padx=12, pady=9,
                           font=("Consolas", 10, "bold"))
        mission.grid(row=0, column=0, sticky="ew", pady=(0,7))

        # 2 x 4 KPI matrix.
        kpi = tk.Frame(side, bg="#05090d")
        kpi.grid(row=1, column=0, sticky="ew", pady=(0,7))
        for c in range(2): kpi.grid_columnconfigure(c, weight=1)
        self.kpi_vars = {}
        kpis = [
            ("REF SPEED", "ref_speed"), ("GOAL LEAD", "goal_lag"),
            ("CENT XTRACK", "cross"), ("FORMATION RMS", "crms"),
            ("PAIR MIN", "pair"), ("PROGRESS SPREAD", "spread"),
            ("BODY CLEAR", "body"), ("AO CLEAR", "edge"),
        ]
        for i,(label,key) in enumerate(kpis):
            box=tk.Frame(kpi,bg="#0d1720",padx=9,pady=6,highlightbackground="#182b37",highlightthickness=1)
            box.grid(row=i//2,column=i%2,sticky="ew",padx=(0 if i%2==0 else 4,0),pady=(0,4))
            tk.Label(box,text=label,bg="#0d1720",fg="#738694",font=("Consolas",8,"bold"),anchor="w").pack(fill="x")
            v=tk.StringVar(value="--")
            tk.Label(box,textvariable=v,bg="#0d1720",fg="#f0f6fc",font=("Consolas",13,"bold"),anchor="w").pack(fill="x")
            self.kpi_vars[key]=v

        self.learning_var = tk.StringVar(value="ILC  waiting")
        tk.Label(side,textvariable=self.learning_var,bg="#0a1219",fg="#a5b4c0",
                 font=("Consolas",9),anchor="w",padx=10,pady=6).grid(row=2,column=0,sticky="ew",pady=(0,7))

        robots_frame = tk.Frame(side,bg="#05090d")
        robots_frame.grid(row=3,column=0,sticky="nsew")
        robots_frame.grid_columnconfigure(0,weight=1)
        self.robot_vars={}
        self.robot_headers={}
        for i,name in enumerate(self.robot_order):
            card=tk.Frame(robots_frame,bg="#0d1117",padx=10,pady=7,
                          highlightbackground="#27313a",highlightthickness=1)
            card.grid(row=i,column=0,sticky="ew",pady=(0,6))
            card.grid_columnconfigure(0,weight=1)
            hdr=tk.StringVar(value=f"{self.friendly.get(name,name)}  //  {name}")
            self.robot_headers[name]=hdr
            tk.Label(card,textvariable=hdr,bg="#0d1117",fg=self.colors[name],
                     font=("Consolas",10,"bold"),anchor="w").grid(row=0,column=0,sticky="ew")
            var=tk.StringVar(value="waiting for Vicon...")
            tk.Label(card,textvariable=var,bg="#0d1117",fg="#c9d1d9",
                     font=("Consolas",8),justify="left",anchor="nw").grid(row=1,column=0,sticky="ew",pady=(3,0))
            self.robot_vars[name]=var

        self.alert_var=tk.StringVar(value="SYSTEM  dashboard online • F11 fullscreen • Esc windowed")
        alert=tk.Label(root,textvariable=self.alert_var,bg="#0a1219",fg="#8b949e",
                       font=("Consolas",9,"bold"),anchor="w",padx=14,pady=6)
        alert.grid(row=2,column=0,sticky="ew")

        root.protocol("WM_DELETE_WINDOW", root.destroy)
        root.bind("<F11>", self._toggle_fullscreen)
        root.bind("<Escape>", self._windowed)
        # Maximise by default, but keep F11 for borderless fullscreen.
        try: root.state("zoomed")
        except Exception: pass
        root.after(60, self._poll)
        root.mainloop()

    def _toggle_fullscreen(self, _evt=None):
        self.fullscreen = not self.fullscreen
        try: self.root.attributes("-fullscreen", self.fullscreen)
        except Exception: pass

    def _windowed(self, _evt=None):
        self.fullscreen=False
        try: self.root.attributes("-fullscreen", False)
        except Exception: pass

    def _poll(self):
        import datetime
        self.clock_var.set(datetime.datetime.now().strftime("%H:%M:%S"))
        newest=None
        try:
            while True:
                item=self.snap_q.get_nowait()
                if item.get("_close"):
                    self.root.destroy(); return
                newest=item
        except queue.Empty:
            pass
        if newest is not None:
            now=time.monotonic()
            if self._last_snap_t is not None:
                dt=now-self._last_snap_t
                if dt>1e-4:
                    inst=1.0/dt
                    self._ui_hz = inst if self._ui_hz<=0 else 0.85*self._ui_hz+0.15*inst
            self._last_snap_t=now
            self.snap=newest
            self._render(newest)
        elif self.snap is not None:
            age=(time.monotonic()-self.snap.get("stamp",time.monotonic()))*1000
            self.radar_age_var.set(f"DATA AGE {age:4.0f} ms  •  UI {self._ui_hz:4.1f} Hz")
            if age>1500:
                self.subtitle_var.set("TELEMETRY STALE  //  CONTROL PROCESS CONTINUES")
        try: self.root.after(max(45,int(1000.0/DIGITAL_TWIN_HZ)),self._poll)
        except Exception: pass

    def _canvas_size(self):
        return max(650.0,float(self.canvas.winfo_width())), max(620.0,float(self.canvas.winfo_height()))

    def _scale(self):
        w,h=self._canvas_size(); pad=28.0
        sx=AO_X_MAX_MM-AO_X_MIN_MM; sy=AO_Y_MAX_MM-AO_Y_MIN_MM
        sc=min((w-2*pad)/sx,(h-2*pad)/sy)
        left=0.5*(w-sx*sc); top=0.5*(h-sy*sc)
        return sc,left,top

    def _xy(self,x,y):
        sc,left,top=self._scale()
        return left+(x-AO_X_MIN_MM)*sc, top+(AO_Y_MAX_MM-y)*sc

    def _line(self,x1,y1,x2,y2,tag="dynamic",**kw):
        self.canvas.create_line(*self._xy(x1,y1),*self._xy(x2,y2),tags=tag,**kw)

    def _rect(self,x1,y1,x2,y2,tag="dynamic",**kw):
        self.canvas.create_rectangle(*self._xy(x1,y2),*self._xy(x2,y1),tags=tag,**kw)

    def _circle(self,x,y,r,tag="dynamic",**kw):
        sc,_,_=self._scale(); px,py=self._xy(x,y); rr=max(2.0,r*sc)
        self.canvas.create_oval(px-rr,py-rr,px+rr,py+rr,tags=tag,**kw)

    def _trail(self,pts,color,width=2):
        if len(pts)<2:return
        coords=[]
        for x,y in pts: coords.extend(self._xy(x,y))
        self.canvas.create_line(*coords,fill=color,width=width,tags="dynamic",smooth=False)

    def _body_poly(self,rd):
        u,v=_body_axes(rd["body_yaw"]); pts=[]
        for su,sv in ((1,1),(1,-1),(-1,-1),(-1,1)):
            x=rd["x"]+su*BODY_HALF_LENGTH_MM*u[0]+sv*BODY_HALF_WIDTH_MM*v[0]
            y=rd["y"]+su*BODY_HALF_LENGTH_MM*u[1]+sv*BODY_HALF_WIDTH_MM*v[1]
            pts.extend(self._xy(x,y))
        return pts

    def _vector(self,x,y,vx,vy,horizon,color,width=2):
        m=math.hypot(vx,vy)
        if m<2:return
        ux,uy=unit(vx,vy); L=clamp(m*horizon,25.0,250.0)
        self._line(x,y,x+ux*L,y+uy*L,fill=color,width=width,arrow=self.tk.LAST)

    @staticmethod
    def _status_color(value, good, warn, invert=False):
        if invert:
            return "#7ee787" if value>=good else ("#d29922" if value>=warn else "#ff7b72")
        return "#7ee787" if value<=good else ("#d29922" if value<=warn else "#ff7b72")

    def _render(self,s):
        c=self.canvas; cx,cy=s["cx"],s["cy"]
        self.centroid_trail.append((cx,cy))
        for rd in s["robots"]:
            if rd["name"] in self.trails:self.trails[rd["name"]].append((rd["x"],rd["y"]))

        w,h=self._canvas_size(); sig=(int(w//20)*20,int(h//20)*20)
        if self._static_size!=sig:
            self._static_size=sig; c.delete("static")
            gx=math.floor(AO_X_MIN_MM/500)*500
            while gx<=AO_X_MAX_MM:
                self._line(gx,AO_Y_MIN_MM,gx,AO_Y_MAX_MM,tag="static",fill="#0a3428",width=1); gx+=500
            gy=math.floor(AO_Y_MIN_MM/500)*500
            while gy<=AO_Y_MAX_MM:
                self._line(AO_X_MIN_MM,gy,AO_X_MAX_MM,gy,tag="static",fill="#0a3428",width=1); gy+=500
            for rr in (500,1000,1500,2000): self._circle(0,0,rr,tag="static",outline="#0b4b38",dash=(3,5))
            self._rect(AO_X_MIN_MM,AO_Y_MIN_MM,AO_X_MAX_MM,AO_Y_MAX_MM,tag="static",outline="#49f2a4",width=2)
            self._rect(VICON_AO_X_MIN_MM,VICON_AO_Y_MIN_MM,VICON_AO_X_MAX_MM,VICON_AO_Y_MAX_MM,tag="static",outline="#50655c",width=1,dash=(7,5))
            self._line(AO_X_MIN_MM,0,AO_X_MAX_MM,0,tag="static",fill="#1c5e49")
            self._line(0,AO_Y_MIN_MM,0,AO_Y_MAX_MM,tag="static",fill="#1c5e49")
            route=square_midpoint_route(self.side_mm)
            for i in range(len(route)-1):
                a,b=route[i],route[i+1]; self._line(a[0],a[1],b[0],b[1],tag="static",fill="#42c8ff",width=3)
            corners=square_corners(self.side_mm)
            for name,(sx,sy) in self.slot_map.items():
                rc=[(x+sx,y+sy) for x,y in corners]
                for i in range(4):
                    a,b=rc[i],rc[(i+1)%4]
                    self._line(a[0],a[1],b[0],b[1],tag="static",fill=self.colors.get(name,"#8b949e"),width=1,dash=(4,5))

        c.delete("dynamic")
        self._trail(self.centroid_trail,"#3fb950",3)
        for name in self.robot_order:self._trail(self.trails[name],self.colors[name],1)

        # Active square corridor and moving reference.
        route=square_midpoint_route(self.side_mm)
        si=min(max(0,int(s.get("side_idx",0))),len(route)-2)
        if s["phase"]=="RUN":
            a,b=route[si],route[si+1]
            self._line(a[0],a[1],b[0],b[1],fill="#e3b341",width=5)
        gx,gy=s["guide_x"],s["guide_y"]
        self._circle(gx,gy,20,outline="#ffdf5d",width=3)
        self._circle(cx,cy,24,outline="#3fb950",width=3)
        self._line(cx,cy,gx,gy,fill="#7d8590",dash=(4,4),width=1)

        targets=[]
        for rd in s["robots"]:
            targets.append((rd["target_x"],rd["target_y"]))
            self._circle(rd["target_x"],rd["target_y"],16,outline="#a371f7",width=2)
        if len(targets)>=2:
            for i in range(len(targets)):
                a,b=targets[i],targets[(i+1)%len(targets)]
                self._line(a[0],a[1],b[0],b[1],fill="#8957e5",dash=(5,4),width=1)

        alerts=[]
        for i,rd in enumerate(s["robots"]):
            name=rd["name"]; col=self.colors.get(name,"#ffffff")
            c.create_polygon(*self._body_poly(rd),outline=col,fill="",width=3,tags="dynamic")
            self._circle(rd["x"],rd["y"],9,fill=col,outline=col)
            self._vector(rd["x"],rd["y"],rd["vx"],rd["vy"],0.55,"#3fb950",3)
            self._vector(rd["x"],rd["y"],rd["common_vx"],rd["common_vy"],0.38,"#39c5cf",2)
            self._vector(rd["x"],rd["y"],rd["slot_vx"],rd["slot_vy"],0.38,"#f0883e",2)
            if math.hypot(rd["boundary_vx"],rd["boundary_vy"])>2:self._vector(rd["x"],rd["y"],rd["boundary_vx"],rd["boundary_vy"],0.45,"#f85149",3)
            if rd["cmd_heading"] is not None and rd["cmd_speed"]>1:
                th=math.radians(rd["cmd_heading"]); L=90+160*clamp(rd["cmd_speed"]/255,0,1)
                self._line(rd["x"],rd["y"],rd["x"]+L*math.cos(th),rd["y"]+L*math.sin(th),fill="#ffdf5d",width=3,arrow=self.tk.LAST)
            px,py=self._xy(rd["x"],rd["y"])
            c.create_text(px,py-14,text=f"C{i+1}",fill=col,font=("Consolas",9,"bold"),tags="dynamic")
            if rd.get("kick_active"):
                alerts.append(f"C{i+1} BREAKAWAY")
            if rd.get("mode") in ("BOUNDARY_RECOVER","COLLISION_BUMPER"):
                alerts.append(f"C{i+1} {rd['mode']}")
            old=self._last_kicks.get(name,0)
            if rd.get("stiction_kicks",0)>old:
                self._events.appendleft(f"{self.friendly.get(name,name)} stiction recovery +{rd['stiction_kicks']-old}")
            self._last_kicks[name]=rd.get("stiction_kicks",0)

        age_ms=max(0.0,(time.monotonic()-s.get("stamp",time.monotonic()))*1000)
        self.radar_age_var.set(f"DATA AGE {age_ms:4.0f} ms  •  UI {self._ui_hz:4.1f} Hz")
        live="LIVE" if age_ms<700 else ("DELAYED" if age_ms<1500 else "STALE")
        leg=(s.get("side_idx",0)+1 if s["phase"]=="RUN" else 0)
        self.subtitle_var.set(f"{live}  //  {s['phase']}  //  LAP {s['lap']:02d}  //  LEG {leg}/5  //  TETHERED LOOKAHEAD")
        self.radar_title_var.set(f"TACTICAL PLAN VIEW  •  CENTROID ({cx:+.0f}, {cy:+.0f}) mm  •  GOAL ({gx:+.0f}, {gy:+.0f}) mm")
        self.mission_var.set(
            f"MISSION  {s['phase']:<6}    LAP {s['lap']:02d}    LEG {leg}/5\n"
            f"TRACK    centroid ({cx:+7.0f},{cy:+7.0f})   moving goal ({gx:+7.0f},{gy:+7.0f})\n"
            f"HEALTH   {'FORMATION LOCKED' if s['crms']<100 else ('FORMATION WIDE' if s['crms']>220 else 'FORMATION CORRECTING')}   •   telemetry {live}"
        )
        self.kpi_vars["ref_speed"].set(f"{s.get('ref_speed',0):.0f} mm/s")
        self.kpi_vars["goal_lag"].set(f"{s.get('goal_lag',0):.0f} mm")
        self.kpi_vars["cross"].set(f"{s.get('centroid_cross',0):+.0f} mm")
        self.kpi_vars["crms"].set(f"{s['crms']:.0f} mm")
        self.kpi_vars["pair"].set(f"{s['pair_min']:.0f} mm")
        self.kpi_vars["spread"].set(f"{s.get('progress_spread',0):.0f} mm")
        self.kpi_vars["body"].set(f"{s['body_clear']:.0f} mm")
        self.kpi_vars["edge"].set(f"{s['body_edge']:.0f} mm")
        self.learning_var.set(
            f"ADAPTIVE  ILC side trim {s.get('ilc_trim',0):+5.2f}°   cruise ×{s.get('ilc_scale',1):.3f}   "
            f"flow {s.get('rail_flow',0):.2f}   goal lead {s.get('goal_lag',0):.0f} mm"
        )

        for i,rd in enumerate(s["robots"]):
            name=rd["name"]
            if name not in self.robot_vars: continue
            terr=math.hypot(rd["target_x"]-rd["x"],rd["target_y"]-rd["y"])
            course="--" if rd["measured_course"] is None else f"{rd['measured_course']:.0f}°"
            cmdh="--" if rd["cmd_heading"] is None else f"{rd['cmd_heading']:.0f}°"
            state="KICK" if rd.get("kick_active") else rd.get("mode","--")
            self.robot_headers[name].set(f"C{i+1}  {self.friendly.get(name,name)}   //   {name}   //   {state}")
            self.robot_vars[name].set(
                f"POS   x {rd['x']:+7.0f}  y {rd['y']:+7.0f} mm     VICON {rd['speed']:6.0f} mm/s\n"
                f"NAV   target err {terr:5.0f}  cross {rd['rail_cross']:+6.0f}  along {rd['rail_along']:+6.0f} mm\n"
                f"CMD   {cmdh:>5} @ {rd['cmd_speed']:5.0f}     actual course {course:>5}     yaw {rd['body_yaw']:5.0f}°\n"
                f"DRIVE gain {rd['drive_gain_mm_s_per_cmd']:4.2f} mm/s/cmd   scale {rd['speed_scale']:5.3f}   FF {rd['formation_trim']:+4.2f}°\n"
                f"GRIP  breakaway {rd['breakaway_cmd']:3.0f}   roll {rd['rolling_floor_cmd']:3.0f}   stiction events {rd['stiction_kicks']:4d}"
            )

        if alerts:
            msg="ALERT  " + "  •  ".join(alerts)
            self.alert_var.set(msg)
        elif self._events:
            self.alert_var.set("EVENT  " + "  |  ".join(list(self._events)[:3]))
        else:
            self.alert_var.set("SYSTEM  NOMINAL  •  F11 fullscreen  •  Esc windowed  •  closing dashboard does not stop control")


class DigitalTwin:
    """Non-blocking ATC dashboard hosted in a separate spawned process.

    This fixes two Windows-specific failure modes from v24: Tk running in a
    background thread, and hard-coded legacy robot IDs.  All display content is
    now generated directly from ROBOT_CONFIGS, so changing a BOLT never breaks
    telemetry cards.  Robot control only publishes tiny immutable dictionaries.
    """
    def __init__(self, side_mm: float, robots: Optional[Sequence[Robot]]=None, enabled: bool=True) -> None:
        self.enabled=bool(enabled); self.closed=not self.enabled; self.last_submit=-1e9
        self.proc=None; self.snap_q=None; self._reported_dead=False
        if not self.enabled:return
        slot_map={r.name:(r.slot_x,r.slot_y) for r in (robots or [])}
        meta=[(name,subject,segment) for name,subject,segment in ROBOT_CONFIGS]
        try:
            ctx=mp.get_context("spawn")
            self.snap_q=ctx.Queue(maxsize=3)
            self.proc=ctx.Process(target=_digital_twin_process_main,
                                  args=(self.snap_q,side_mm,slot_map,meta),
                                  name="SpheroATCDashboard",daemon=True)
            self.proc.start()
            print("Digital twin: professional ATC dashboard started in a separate process (10 Hz, latest-frame telemetry).")
        except Exception as exc:
            print(f"Digital twin unavailable ({type(exc).__name__}: {exc}); control continues.")
            self.enabled=False; self.closed=True

    def close(self) -> None:
        if self.closed:return
        self.closed=True; self.enabled=False
        try:self.snap_q.put_nowait({"_close":True})
        except Exception:pass
        try:
            if self.proc is not None:
                self.proc.join(timeout=0.8)
                if self.proc.is_alive(): self.proc.terminate()
        except Exception:pass

    def update(self, robots, phase, lap, side_idx, guide_x, guide_y, guide_vx, guide_vy,
               cx, cy, crms, pair_min_mm, body_clear_mm, body_edge_mm,
               rail_flow=0.0, progress_spread_mm=0.0, max_cross_mm=0.0,
               ref_speed=0.0, goal_lag=0.0, centroid_cross=0.0,
               ilc_trim=0.0, ilc_scale=1.0) -> None:
        if not self.enabled or self.closed:return
        if self.proc is not None and not self.proc.is_alive():
            if not self._reported_dead:
                print("Digital twin process closed; robot control continues normally.")
                self._reported_dead=True
            self.enabled=False; return
        now=time.monotonic()
        if now-self.last_submit < 1.0/12.0:return
        self.last_submit=now
        snap={"stamp":now,"phase":phase,"lap":lap,"side_idx":side_idx,
              "guide_x":guide_x,"guide_y":guide_y,"guide_vx":guide_vx,"guide_vy":guide_vy,
              "cx":cx,"cy":cy,"crms":crms,"pair_min":pair_min_mm,"body_clear":body_clear_mm,
              "body_edge":body_edge_mm,"rail_flow":rail_flow,"progress_spread":progress_spread_mm,
              "max_cross":max_cross_mm,"ref_speed":ref_speed,"goal_lag":goal_lag,
              "centroid_cross":centroid_cross,"ilc_trim":ilc_trim,"ilc_scale":ilc_scale,"robots":[]}
        for r in robots:
            snap["robots"].append({
                "name":r.name,"x":r.est.x,"y":r.est.y,"yaw":r.est.yaw_deg,"body_yaw":body_yaw_deg(r),
                "vx":r.est.vx,"vy":r.est.vy,"speed":r.est.speed,
                "target_x":r.dbg_target_x,"target_y":r.dbg_target_y,
                "common_vx":r.dbg_common_vx,"common_vy":r.dbg_common_vy,
                "slot_vx":r.dbg_slot_vx,"slot_vy":r.dbg_slot_vy,
                "sep_vx":r.dbg_sep_vx,"sep_vy":r.dbg_sep_vy,
                "boundary_vx":r.dbg_boundary_vx,"boundary_vy":r.dbg_boundary_vy,
                "cmd_heading":r.cmd_heading_world,"cmd_speed":r.cmd_speed,"mode":r.mode,
                "trim":r.heading_bias_deg,"verified_trim":r.verified_trim_deg,
                "measured_course":r.measured_course_deg,"course_error":r.course_error_deg,
                "speed_scale":r.speed_scale,"formation_trim":r.formation_trim_deg,"slot_error":r.slot_error_mm,
                "rail_along":r.rail_along_mm,"rail_cross":r.rail_cross_mm,"rail_remaining":r.rail_remaining_mm,
                "rail_forward":r.rail_forward_cmd,"rail_sync":r.rail_sync_cmd,
                "breakaway_cmd":r.learned_breakaway_cmd,"rolling_floor_cmd":r.learned_rolling_floor_cmd,
                "drive_gain_mm_s_per_cmd":r.drive_gain_mm_s_per_cmd,"stiction_kicks":r.stiction_kicks,
                "kick_active":time.monotonic()<r.breakaway_until,
            })
        try:
            self.snap_q.put_nowait(snap)
        except queue.Full:
            try:self.snap_q.get_nowait()
            except Exception:pass
            try:self.snap_q.put_nowait(snap)
            except Exception:pass
        except Exception:
            pass


# =============================================================================
# reference tethered lookahead + professional ATC dashboard + robust Vicon continuity
# =============================================================================

def _v23_default_ilc() -> dict:
    return {
        "controller": CONTROLLER_VERSION,
        "side_heading_trim_deg": [0.0] * ILC_SIDE_COUNT,
        "side_cross_ema_mm": [0.0] * ILC_SIDE_COUNT,
        "side_samples": [0] * ILC_SIDE_COUNT,
        "cruise_scale": 1.0,
        "laps_learned": 0,
    }


def load_path_ilc() -> dict:
    p = Path(__file__).resolve().with_name(PATH_ILC_FILE)
    legacy = Path(__file__).resolve().with_name("three_chariot_square_ilc_v25.json")
    model = _v23_default_ilc()
    try:
        source = p if p.exists() else legacy
        raw = json.loads(source.read_text())
        if source != p:
            print(f"  path ILC: importing {source.name}")
        trims = list(raw.get("side_heading_trim_deg", model["side_heading_trim_deg"]))
        emas = list(raw.get("side_cross_ema_mm", model["side_cross_ema_mm"]))
        samples = list(raw.get("side_samples", model["side_samples"]))
        if len(trims) == ILC_SIDE_COUNT:
            model["side_heading_trim_deg"] = [
                clamp(float(v), -ILC_HEADING_TRIM_MAX_DEG, ILC_HEADING_TRIM_MAX_DEG)
                for v in trims
            ]
        if len(emas) == ILC_SIDE_COUNT:
            model["side_cross_ema_mm"] = [float(v) for v in emas]
        if len(samples) == ILC_SIDE_COUNT:
            model["side_samples"] = [int(v) for v in samples]
        model["cruise_scale"] = clamp(
            float(raw.get("cruise_scale", 1.0)),
            ILC_CRUISE_SCALE_MIN, ILC_CRUISE_SCALE_MAX
        )
        model["laps_learned"] = int(raw.get("laps_learned", 0))
        print(
            "  path ILC: "
            f"cruise_scale={model['cruise_scale']:.3f} "
            f"side_trim={[round(v,2) for v in model['side_heading_trim_deg']]} "
            f"laps={model['laps_learned']}"
        )
    except Exception:
        print("  path ILC: starting fresh moving-square model")
    return model


def save_path_ilc(model: dict) -> None:
    p = Path(__file__).resolve().with_name(PATH_ILC_FILE)
    payload = dict(model)
    payload["controller"] = CONTROLLER_VERSION
    try:
        p.write_text(json.dumps(payload, indent=2))
    except Exception as exc:
        print(f"WARNING: could not save path ILC model: {exc}")


def moving_reference_speed(
    phase: str, ref_s: float, seg_len: float,
    centroid_lag_mm: float, crms: float, path_ilc: dict,
) -> float:
    """Continuous reference speed.  Never waits for a corner/goal."""
    if phase == "ENTRY":
        nominal = MOVING_ENTRY_SPEED_MM_S
    else:
        d_corner = min(max(0.0, ref_s), max(0.0, seg_len - ref_s))
        q = clamp(d_corner / max(1.0, MOVING_CORNER_ZONE_MM), 0.0, 1.0)
        # Smoothstep avoids a visible speed discontinuity around the corner zone.
        q = q * q * (3.0 - 2.0 * q)
        nominal = MOVING_CORNER_SPEED_MM_S + (MOVING_CRUISE_MM_S - MOVING_CORNER_SPEED_MM_S) * q
        nominal *= clamp(float(path_ilc.get("cruise_scale", 1.0)),
                         ILC_CRUISE_SCALE_MIN, ILC_CRUISE_SCALE_MAX)

    # Slow but never freeze the moving goal if the actual group is lagging.
    lag = max(0.0, centroid_lag_mm)
    if lag <= MOVING_LAG_SOFT_MM:
        lag_scale = 1.0
    elif lag >= MOVING_LAG_HARD_MM:
        lag_scale = MOVING_REF_MIN_SCALE
    else:
        q = (lag - MOVING_LAG_SOFT_MM) / max(1.0, MOVING_LAG_HARD_MM - MOVING_LAG_SOFT_MM)
        lag_scale = 1.0 - (1.0 - MOVING_REF_MIN_SCALE) * q

    if crms <= MOVING_FORM_SOFT_RMS_MM:
        form_scale = 1.0
    elif crms >= MOVING_FORM_HARD_RMS_MM:
        form_scale = MOVING_REF_MIN_SCALE
    else:
        q = (crms - MOVING_FORM_SOFT_RMS_MM) / max(
            1.0, MOVING_FORM_HARD_RMS_MM - MOVING_FORM_SOFT_RMS_MM
        )
        form_scale = 1.0 - (1.0 - MOVING_REF_MIN_SCALE) * q

    return clamp(
        nominal * min(lag_scale, form_scale),
        MOVING_MIN_REFERENCE_SPEED_MM_S,
        MOVING_MAX_REFERENCE_SPEED_MM_S,
    )


def _cap_vector(x: float, y: float, cap: float) -> Tuple[float, float]:
    m = math.hypot(x, y)
    if m <= cap or m < 1e-9:
        return x, y
    return x * cap / m, y * cap / m


def moving_virtual_leader_commands(
    robots: Sequence[Robot],
    a: Tuple[float, float], b: Tuple[float, float],
    goal_x: float, goal_y: float, goal_speed: float,
    max_cmd: int, dt: float, phase: str, side_idx: int,
    path_ilc: dict, boundary_hold: bool = False,
) -> dict:
    """Track one continuously moving translated slot per robot.

    v24 deliberately avoids a separate free-running flock/centroid navigator.
    Each Chariot tracks the same moving square point plus its fixed formation
    offset.  Along-track error changes speed only; cross-track error changes
    steering only.  Forward speed is never negative: an ahead robot waits for
    the moving slot rather than reversing toward an old goal.
    """
    tx, ty = unit(b[0] - a[0], b[1] - a[1])
    nx, ny = -ty, tx
    L = math.hypot(b[0] - a[0], b[1] - a[1])

    cx, cy, cvx, cvy = centroid(robots)
    crms = formation_rms(robots, cx, cy)
    sep = collision_vectors(robots)
    trims = path_ilc.get("side_heading_trim_deg", [0.0] * ILC_SIDE_COUNT)
    trim_deg = 0.0
    if phase == "RUN" and 0 <= side_idx < len(trims):
        trim_deg = clamp(float(trims[side_idx]),
                         -ILC_HEADING_TRIM_MAX_DEG, ILC_HEADING_TRIM_MAX_DEG)

    alongs, crosses, endpoint_dists = [], [], []
    rel_errs = {}
    body_min = min_body_clearance(robots)
    min_edge = min(body_edge_clearance(r) for r in robots)

    for r in robots:
        target_x = goal_x + r.slot_x
        target_y = goal_y + r.slot_y
        ex = target_x - r.est.x
        ey = target_y - r.est.y
        e_along = ex * tx + ey * ty
        e_cross = ex * nx + ey * ny
        v_along = r.est.vx * tx + r.est.vy * ty
        v_cross = r.est.vx * nx + r.est.vy * ny

        # Direct moving-slot pursuit.  If a robot gets ahead, e_along becomes
        # negative and forward command falls all the way to zero; it NEVER
        # reverses.  The target continues forward and naturally catches up.
        forward = (
            goal_speed
            + 0.62 * e_along
            + 0.14 * (goal_speed - v_along)
        )
        forward = clamp(forward, 0.0, MOVING_ROBOT_FORWARD_MAX_MM_S)

        lateral = 0.92 * e_cross - 0.18 * v_cross
        lateral = clamp(lateral, -MOVING_REL_CROSS_MAX_MM_S, MOVING_REL_CROSS_MAX_MM_S)
        lateral += math.tan(math.radians(trim_deg)) * max(0.0, forward)

        # Keep the vector square-like.  A large cross-track error is corrected
        # gradually while still moving mainly along the active side.
        rail_ax, rail_ay = a[0] + r.slot_x, a[1] + r.slot_y
        rail_bx, rail_by = b[0] + r.slot_x, b[1] + r.slot_y
        along = (r.est.x - rail_ax) * tx + (r.est.y - rail_ay) * ty
        cross = (r.est.x - rail_ax) * nx + (r.est.y - rail_ay) * ny
        remaining = L - along
        alongs.append(along)
        crosses.append(cross)
        endpoint_dists.append(math.hypot(r.est.x - rail_bx, r.est.y - rail_by))
        rel_errs[r.name] = (e_along, e_cross)

        cone = MOVING_RECOVERY_CONE_DEG if abs(cross) > 220.0 else MOVING_HEADING_CONE_DEG
        lateral_cap = math.tan(math.radians(cone)) * max(35.0, forward)
        lateral = clamp(lateral, -lateral_cap, lateral_cap)

        vx = forward * tx + lateral * nx
        vy = forward * ty + lateral * ny

        # Very small short-range bumper only.
        svx, svy, body_clear = sep[r.name]
        svx, svy = _cap_vector(svx, svy, MOVING_BUMPER_CAP_MM_S)
        if body_clear < MOVING_BUMPER_START_MM:
            q = clamp((MOVING_BUMPER_START_MM - body_clear) /
                      max(1.0, MOVING_BUMPER_START_MM - MOVING_BUMPER_OVERLAP_MM),
                      0.0, 1.0)
            w_sep = 0.03 + 0.10 * q
            vx += w_sep * svx
            vy += w_sep * svy

        bvx, bvy, clearance = boundary_vector(r)
        recovery = False
        local_max = max_cmd
        if clearance < RECENTER_TRIGGER_MM:
            # Safety remains the only layer allowed to violate the square cone.
            vx = 0.35 * vx + 0.95 * bvx
            vy = 0.35 * vy + 0.95 * bvy
            local_max = min(local_max, 105)
            recovery = True
            r.mode = "BOUNDARY_RECOVER"
        elif body_clear <= MOVING_BUMPER_OVERLAP_MM:
            r.mode = "COLLISION_BUMPER"
            local_max = min(local_max, 120)
        else:
            r.mode = "MOVING_ENTRY" if phase == "ENTRY" else "MOVING_RUN"

        if not recovery and math.hypot(vx, vy) > 8.0:
            h_side = heading_of(tx, ty)
            h_cmd = heading_of(vx, vy)
            safe_cone = MOVING_RECOVERY_CONE_DEG if abs(cross) > 220.0 else MOVING_HEADING_CONE_DEG
            dh = clamp(wrap180(h_cmd - h_side), -safe_cone, safe_cone)
            vm = math.hypot(vx, vy)
            hh = math.radians(wrap360(h_side + dh))
            vx, vy = vm * math.cos(hh), vm * math.sin(hh)

        r.slot_error_mm = math.hypot(ex, ey)
        r.rail_along_mm = along
        r.rail_cross_mm = cross
        r.rail_remaining_mm = remaining
        r.rail_forward_cmd = forward
        r.rail_sync_cmd = e_along
        r.rail_target_x = target_x
        r.rail_target_y = target_y
        r.dbg_target_x, r.dbg_target_y = target_x, target_y
        r.dbg_common_vx = goal_speed * tx
        r.dbg_common_vy = goal_speed * ty
        r.dbg_slot_vx = (forward-goal_speed) * tx + lateral * nx
        r.dbg_slot_vy = (forward-goal_speed) * ty + lateral * ny
        r.dbg_sep_vx, r.dbg_sep_vy = svx, svy
        r.dbg_boundary_vx, r.dbg_boundary_vy = bvx, bvy
        r.dbg_final_vx, r.dbg_final_vy = vx, vy

        # min_cmd is intentionally LOW now.  Static friction is handled by a
        # short kick; normal rolling speed is closed-loop from Vicon.
        command_robot(r, vx, vy, local_max, dt, recovery,
                      min_cmd=DRIVE_ROLLING_CMD_MIN)

    spread = max(alongs) - min(alongs) if alongs else 0.0
    center_cross_actual = (cx - a[0]) * nx + (cy - a[1]) * ny
    center_along_actual = (cx - a[0]) * tx + (cy - a[1]) * ty
    return {
        "tx": tx, "ty": ty, "nx": nx, "ny": ny, "L": L,
        "center_cross": center_cross_actual,
        "center_along": center_along_actual,
        "goal_lag": (goal_x - cx) * tx + (goal_y - cy) * ty,
        "spread": spread,
        "max_abs_cross": max((abs(v) for v in crosses), default=0.0),
        "max_endpoint_dist": max(endpoint_dists, default=0.0),
        "body_min": body_min,
        "pair_min": pair_min(robots),
        "min_edge": min_edge,
        "crms": crms,
        "rel_errs": rel_errs,
        "ilc_trim_deg": trim_deg,
    }


def update_moving_learning(
    robots: Sequence[Robot], side_idx: int, stats: dict,
    dt: float, path_ilc: dict, clean: bool,
) -> None:
    """Small bounded adaptive feed-forward; never changes startup calibration."""
    if not clean:
        return

    # --- Global square ILC: systematic centroid cross-track -> side heading trim.
    idx = int(clamp(side_idx, 0, ILC_SIDE_COUNT - 1))
    alpha = 1.0 - math.exp(-max(1e-4, dt) / ILC_CROSS_EMA_TC_S)
    emas = path_ilc["side_cross_ema_mm"]
    emas[idx] += alpha * (stats["center_cross"] - emas[idx])
    target_trim = clamp(
        -ILC_TRIM_PER_MM_DEG * emas[idx],
        -ILC_HEADING_TRIM_MAX_DEG,
        ILC_HEADING_TRIM_MAX_DEG,
    )
    beta = 1.0 - math.exp(-max(1e-4, dt) / ILC_TRIM_ADAPT_TC_S)
    trims = path_ilc["side_heading_trim_deg"]
    trims[idx] += beta * (target_trim - trims[idx])
    trims[idx] = clamp(trims[idx], -ILC_HEADING_TRIM_MAX_DEG, ILC_HEADING_TRIM_MAX_DEG)
    path_ilc["side_samples"][idx] += 1

    # Increase virtual-leader pace only while tracking is genuinely clean.
    if (
        abs(stats["goal_lag"]) < 150.0
        and abs(stats["center_cross"]) < 75.0
        and stats["crms"] < 120.0
        and stats["spread"] < 130.0
    ):
        path_ilc["cruise_scale"] = min(
            ILC_CRUISE_SCALE_MAX,
            path_ilc["cruise_scale"] + ILC_CRUISE_ADAPT_UP_PER_S * dt,
        )
    elif abs(stats["goal_lag"]) > 300.0 or stats["crms"] > 240.0:
        path_ilc["cruise_scale"] = max(
            ILC_CRUISE_SCALE_MIN,
            path_ilc["cruise_scale"] - ILC_CRUISE_ADAPT_DOWN_PER_S * dt,
        )

    # --- Per-robot formation feed-forward.
    a = 1.0 - math.exp(-max(1e-4, dt) / MOVING_LEARN_EMA_TC_S)
    b = 1.0 - math.exp(-max(1e-4, dt) / MOVING_LEARN_BLEND_TC_S)
    for r in robots:
        rel_along, rel_cross = stats["rel_errs"].get(r.name, (0.0, 0.0))
        r.learn_along_ema += a * (rel_along - r.learn_along_ema)
        r.learn_cross_ema += a * (rel_cross - r.learn_cross_ema)

        target_speed_scale = clamp(
            1.0 + MOVING_SPEED_TRIM_PER_MM * r.learn_along_ema,
            SPEED_SCALE_MIN, SPEED_SCALE_MAX,
        )
        r.speed_scale += b * (target_speed_scale - r.speed_scale)
        r.speed_scale = clamp(r.speed_scale, SPEED_SCALE_MIN, SPEED_SCALE_MAX)

        target_form_trim = clamp(
            MOVING_FORM_HEADING_PER_MM * r.learn_cross_ema,
            -MOVING_FORM_HEADING_MAX_DEG,
            MOVING_FORM_HEADING_MAX_DEG,
        )
        r.formation_trim_deg += b * (target_form_trim - r.formation_trim_deg)
        r.formation_trim_deg = clamp(
            r.formation_trim_deg,
            -MOVING_FORM_HEADING_MAX_DEG,
            MOVING_FORM_HEADING_MAX_DEG,
        )
        r.learning_samples += 1


# =============================================================================
# Mission
# =============================================================================

def run_mission(
    vicon: ViconSystem, robots: List[Robot], side_mm: float, laps: int,
    max_cmd: int, timeout_s: float, log_path: Path,
    show_digital_twin: bool = True,
) -> None:
    """reference tethered moving-goal square swarm with robust Vicon continuity.

    HOME is only a brief initial formation acquisition.  ENTRY and RUN have no
    static goal acceptance, no CORNER_HOLD and no return-to-goal correction.
    A virtual centroid target moves continuously along the square, while each
    robot tracks a fixed relative formation slot around it.
    """
    stop_requested = False

    def sigint(_sig=None, _frame=None):
        nonlocal stop_requested
        stop_requested = True

    old_sig = signal.signal(signal.SIGINT, sigint)
    start = time.monotonic()
    last_t = start
    last_print = -1e9
    last_learning_save = start
    last_log_flush = start

    update_all(vicon, robots)
    choose_slots(robots)
    route = square_midpoint_route(side_mm)
    twin = DigitalTwin(side_mm, robots=robots, enabled=show_digital_twin)
    path_ilc = load_path_ilc()

    home_x, home_y = 0.0, 0.0
    phase = "HOME"
    side_idx = 0
    completed_laps = 0
    boundary_hold_active = False
    stable_since = None
    home_phase_start = start

    # Moving reference state. ENTRY is one continuous segment from HOME to the
    # bottom midpoint. RUN then moves around the five-segment midpoint square.
    ref_s = 0.0
    ref_speed = 0.0
    goal_x = home_x
    goal_y = home_y
    goal_lag = 0.0

    print("TETHERED MOVING-LOOKAHEAD SQUARE SWARM:")
    print(f"  global square: {side_mm:.0f} x {side_mm:.0f} mm centred at (0,0)")
    print("  ENTRY/RUN use a centroid-tethered moving lookahead: NO corner holds, NO reverse return-to-goal.")
    print("  Virtual leader keeps moving; each Sphero tracks a moving formation slot.")
    print(
        f"  cruise={MOVING_CRUISE_MM_S:.0f} mm/s, corner={MOVING_CORNER_SPEED_MM_S:.0f} mm/s, "
        f"rolling floor >= {MOVING_MIN_COMMAND_FLOOR:.0f}, breakaway {STICTION_KICK_MIN_CMD:.0f}-{STICTION_KICK_MAX_CMD:.0f}."
    )
    for r in robots:
        print(
            f"  {r.name}: fixed formation slot=({r.slot_x:+.1f},{r.slot_y:+.1f}) mm, "
            f"learned floor={r.learned_rolling_floor_cmd:.0f}, kick={r.learned_breakaway_cmd:.0f}"
        )

    fields = [
        "t_s", "phase", "lap", "side",
        "score_ref_x", "score_ref_y",
        "virtual_speed_mm_s", "goal_lag_mm", "ilc_side_trim_deg", "ilc_cruise_scale",
        "centroid_x", "centroid_y", "centroid_vx", "centroid_vy",
        "centroid_score_error_mm", "centroid_path_cross_mm",
        "formation_rms_mm", "pair_min_mm", "body_clearance_min_mm", "min_edge_mm",
        "group_progress_mm", "progress_spread_mm", "rail_flow",
        "robot", "x", "y", "yaw", "vx", "vy", "speed",
        "target_x", "target_y", "rail_along_mm", "rail_cross_mm",
        "rail_remaining_mm", "rail_forward_cmd", "rail_sync_cmd",
        "slot_error_mm", "mode", "cmd_world_heading", "cmd_speed",
        "heading_bias_deg", "speed_scale", "formation_trim_deg", "learning_samples",
        "breakaway_cmd", "rolling_floor_cmd", "drive_gain_mm_s_per_cmd", "stiction_kicks",
    ]

    def reacquire_vicon() -> bool:
        """Re-seed Vicon from a short run of mutually-consistent live frames.

        Critically, this does NOT require the recovered pose to return near the
        last stale estimate.  The robots are stopped and the moving reference is
        frozen while we collect several consistent frames at the robots' *current*
        physical locations.
        """
        print("*** VICON DATA LOSS: holding robots; moving reference is frozen.")
        stop_all(robots)
        last_msg = time.monotonic()
        prev = None
        prev_t = None
        good_count = 0
        latest = None
        recover_start = time.monotonic()

        while not stop_requested:
            try:
                poses = vicon.read_all()
                now_r = time.monotonic()
                visible = all(not p.occluded for p in poses.values())

                # Basic workspace sanity only.  Do NOT compare against stale r.est.
                in_workspace = visible and all(
                    AO_X_MIN_MM - VICON_REACQUIRE_AO_MARGIN_MM <= poses[r.name].x <= AO_X_MAX_MM + VICON_REACQUIRE_AO_MARGIN_MM
                    and AO_Y_MIN_MM - VICON_REACQUIRE_AO_MARGIN_MM <= poses[r.name].y <= AO_Y_MAX_MM + VICON_REACQUIRE_AO_MARGIN_MM
                    for r in robots
                )

                consistent = in_workspace
                if consistent and prev is not None and prev_t is not None:
                    dtp = max(1e-3, now_r - prev_t)
                    step_limit = (
                        VICON_REACQUIRE_CONSISTENCY_BASE_MM
                        + VICON_REACQUIRE_MAX_SPEED_MM_S * min(dtp, VICON_REACQUIRE_DT_CAP_S)
                    )
                    for r in robots:
                        p0, p1 = poses[r.name], prev[r.name]
                        if math.hypot(p0.x - p1.x, p0.y - p1.y) > step_limit:
                            consistent = False
                            break

                if in_workspace and consistent:
                    good_count += 1
                    latest = poses
                elif in_workspace:
                    # The current visible frame may be the first frame of a new
                    # stable sequence.  Keep it as the new baseline instead of
                    # forcing recovery to an obsolete coordinate.
                    good_count = 1
                    latest = poses
                else:
                    good_count = 0
                    latest = None

                prev = poses if in_workspace else None
                prev_t = now_r if in_workspace else None

                if good_count >= VICON_REACQUIRE_GOOD_SAMPLES and latest is not None:
                    now2 = time.monotonic()
                    for r in robots:
                        r.est = Estimate()
                        r.est.update(latest[r.name], now2)
                        r.cmd_speed = 0.0
                        r.cmd_heading_world = None
                        r.smooth_vx = r.smooth_vy = 0.0
                        r.drive_speed_i_cmd = 0.0
                        r.stall_ref_t = now2
                        r.stall_ref_x = latest[r.name].x
                        r.stall_ref_y = latest[r.name].y
                    print(
                        f"*** VICON REACQUIRED in {now2 - recover_start:.2f}s: "
                        "re-seeded at CURRENT poses; continuing the SAME moving reference."
                    )
                    return True
            except Exception as exc:
                good_count = 0
                latest = None
                prev = None
                prev_t = None

            if time.monotonic() - last_msg >= TRANSIENT_OCCLUSION_PRINT_S:
                print(
                    f"  waiting for live Vicon frames... stable={good_count}/{VICON_REACQUIRE_GOOD_SAMPLES} "
                    f"({time.monotonic() - recover_start:.1f}s)"
                )
                last_msg = time.monotonic()
            time.sleep(0.03)
        return False

    with log_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        try:
            while not stop_requested:
                now = time.monotonic()
                elapsed = now - start
                if timeout_s > 0 and elapsed >= timeout_s:
                    print("Timeout reached; stopping all robots.")
                    break
                dt = clamp(now - last_t, 1.0 / 120.0, 0.10)
                last_t = now

                try:
                    update_all(vicon, robots, now)
                except RuntimeError as exc:
                    if "Vicon occlusion" in str(exc) or "Vicon pose glitch" in str(exc) or "Vicon pose loss" in str(exc):
                        if not reacquire_vicon():
                            break
                        last_t = time.monotonic()
                        continue
                    raise

                cx, cy, cvx, cvy = centroid(robots)
                crms = formation_rms(robots, cx, cy)
                pmin = pair_min(robots)
                body_min = min_body_clearance(robots)
                min_edge = min(body_edge_clearance(r) for r in robots)

                # Safety boundary can freeze the virtual reference; it never
                # restarts HOME or changes square progress.
                if (not boundary_hold_active) and min_edge < RECENTER_TRIGGER_MM:
                    boundary_hold_active = True
                    print(
                        f"*** BOUNDARY HOLD: bodyEdge={min_edge:.0f} mm. "
                        "Freezing virtual leader; square progress preserved."
                    )
                elif boundary_hold_active and min_edge > RECENTER_TRIGGER_MM + BOUNDARY_HOLD_RELEASE_MARGIN_MM:
                    boundary_hold_active = False
                    print("*** BOUNDARY CLEAR: virtual leader resumes from the same place.")

                stats = None
                score_ref_x = goal_x
                score_ref_y = goal_y
                score_cross = 0.0
                group_progress = ref_s
                progress_spread = 0.0
                rail_flow = 0.0
                ilc_trim = 0.0

                if phase == "HOME":
                    # Keep HOME brief.  It is only initial collision-safe assembly,
                    # not a precision waypoint.
                    max_home_err, pmin, body_min, min_edge = point_slot_commands(
                        robots, home_x, home_y, min(max_cmd, 165), dt
                    )
                    cx, cy, cvx, cvy = centroid(robots)
                    crms = formation_rms(robots, cx, cy)
                    enough = (
                        max_home_err <= 300.0
                        and crms <= 240.0
                        and body_min > BODY_CLEAR_CRITICAL_MM
                    )
                    fallback = (
                        elapsed - (home_phase_start - start) >= 6.0
                        and max_home_err <= 430.0
                        and body_min > BODY_CLEAR_EXTREME_MM
                    )
                    if enough or fallback:
                        stable_since = stable_since or now
                        if fallback or now - stable_since >= 0.08:
                            phase = "ENTRY"
                            ref_s = 0.0
                            stable_since = None
                            for r in robots:
                                r.smooth_vx = r.smooth_vy = 0.0
                                r.cmd_speed = max(r.cmd_speed, MOVING_MIN_COMMAND_FLOOR)
                            print(
                                f"HOME RELEASE: max slot error={max_home_err:.0f} mm, "
                                f"formRMS={crms:.0f}. Starting MOVING ENTRY; no endpoint hold."
                            )
                    else:
                        stable_since = None

                else:
                    if phase == "ENTRY":
                        a = (home_x, home_y)
                        b = route[0]
                        active_side = 0
                    else:
                        a = route[side_idx]
                        b = route[side_idx + 1]
                        active_side = side_idx

                    tx, ty = unit(b[0]-a[0], b[1]-a[1])
                    nx, ny = -ty, tx
                    L = math.hypot(b[0]-a[0], b[1]-a[1])

                    # v24 TETHERED moving lookahead.  The target is always
                    # ahead of actual centroid progress on THIS straight side,
                    # but cannot free-run metres away from the swarm.
                    centroid_along = (cx - a[0]) * tx + (cy - a[1]) * ty
                    centroid_cross_now = (cx - a[0]) * nx + (cy - a[1]) * ny

                    desired_lookahead_s = clamp(
                        centroid_along + TETHER_LOOKAHEAD_MM, 0.0, L
                    )
                    # Never move the reference backwards.  If the real swarm
                    # overshoots, snap the reference FORWARD to catch up.
                    ref_s = max(ref_s, desired_lookahead_s)
                    max_lead_s = clamp(
                        centroid_along + TETHER_MAX_LEAD_MM, 0.0, L
                    )

                    ss = clamp(ref_s, 0.0, L)
                    goal_x = a[0] + tx * ss
                    goal_y = a[1] + ty * ss
                    goal_lag = ss - centroid_along

                    ref_speed = moving_reference_speed(
                        phase, ss, L, max(0.0, goal_lag), crms, path_ilc
                    )
                    # If the swarm is severely off the current corridor or badly
                    # stretched, freeze TARGET ADVANCE only.  Robots still track
                    # the current moving slots; no old corner target exists.
                    severe_off_path = (
                        abs(centroid_cross_now) > TETHER_MAX_CENTROID_CROSS_MM
                        or crms > TETHER_BAD_FORM_RMS_MM
                    )
                    if boundary_hold_active or severe_off_path:
                        ref_speed = 0.0

                    stats = moving_virtual_leader_commands(
                        robots, a, b, goal_x, goal_y, ref_speed,
                        max_cmd, dt, phase, active_side, path_ilc,
                        boundary_hold=boundary_hold_active,
                    )
                    group_progress = ref_s
                    progress_spread = stats["spread"]
                    rail_flow = clamp(
                        ref_speed / max(1.0, MOVING_CRUISE_MM_S), 0.0, 1.2
                    )
                    score_cross = stats["center_cross"]
                    ilc_trim = stats["ilc_trim_deg"]

                    clean_learning = (
                        phase == "RUN"
                        and ss > MOVING_CORNER_ZONE_MM
                        and (L - ss) > MOVING_CORNER_ZONE_MM
                        and abs(stats["center_cross"]) < 180.0
                        and stats["crms"] < 220.0
                        and stats["spread"] < 220.0
                        and stats["body_min"] > 5.0
                        and stats["min_edge"] > BOUNDARY_SOFT_MM
                        and not boundary_hold_active
                        and not any(r.mode == "BOUNDARY_RECOVER" for r in robots)
                    )
                    update_moving_learning(
                        robots, active_side, stats, dt, path_ilc, clean_learning
                    )

                    # Advance at a bounded rate, but never beyond the centroid
                    # tether.  No waypoint arrival test and no return-to-goal.
                    if not boundary_hold_active and not severe_off_path:
                        ref_s = min(L, max(ref_s, min(max_lead_s, ref_s + ref_speed * dt)))

                    # HANDOFF is based on REAL centroid progress, not exact goal
                    # arrival.  Overshoot simply triggers the next side.
                    turn_now = centroid_along >= (L - TETHER_TURN_EARLY_MM)
                    if turn_now:
                        if phase == "ENTRY":
                            phase = "RUN"
                            side_idx = 0
                            ref_s = 0.0
                            print(
                                "TETHERED ENTRY HANDOFF -> square side 1; "
                                "no endpoint stop and no return correction."
                            )
                        else:
                            old = side_idx
                            side_idx += 1
                            if side_idx >= len(route) - 1:
                                side_idx = 0
                                completed_laps += 1
                                path_ilc["laps_learned"] = int(path_ilc.get("laps_learned", 0)) + 1
                                print(
                                    f"TETHERED SQUARE LAP COMPLETE: {completed_laps}; "
                                    f"ILC trims={[round(v,2) for v in path_ilc['side_heading_trim_deg']]} "
                                    f"cruiseScale={path_ilc['cruise_scale']:.3f}"
                                )
                                if laps > 0 and completed_laps >= laps:
                                    stop_requested = True
                            else:
                                print(
                                    f"TETHERED CORNER HANDOFF: segment {old+1}->{side_idx+1}; "
                                    "moving goal continues on the next side."
                                )
                            ref_s = 0.0

                # Diagnostics-only course monitor.  Startup calibration stays fixed.
                update_runtime_course_lock(robots, dt, False)

                if now - last_learning_save >= LEARNING_SAVE_PERIOD_S:
                    save_learning(robots)
                    save_path_ilc(path_ilc)
                    last_learning_save = now

                cx, cy, cvx, cvy = centroid(robots)
                crms = formation_rms(robots, cx, cy)
                centroid_score_err = math.hypot(cx-score_ref_x, cy-score_ref_y)

                for r in robots:
                    writer.writerow({
                        "t_s": f"{elapsed:.3f}", "phase": phase, "lap": completed_laps,
                        "side": side_idx + 1 if phase == "RUN" else 0,
                        "score_ref_x": f"{score_ref_x:.2f}", "score_ref_y": f"{score_ref_y:.2f}",
                        "virtual_speed_mm_s": f"{ref_speed:.2f}",
                        "goal_lag_mm": f"{goal_lag:.2f}",
                        "ilc_side_trim_deg": f"{ilc_trim:.3f}",
                        "ilc_cruise_scale": f"{path_ilc.get('cruise_scale',1.0):.4f}",
                        "centroid_x": f"{cx:.2f}", "centroid_y": f"{cy:.2f}",
                        "centroid_vx": f"{cvx:.2f}", "centroid_vy": f"{cvy:.2f}",
                        "centroid_score_error_mm": f"{centroid_score_err:.2f}",
                        "centroid_path_cross_mm": f"{score_cross:.2f}",
                        "formation_rms_mm": f"{crms:.2f}",
                        "pair_min_mm": f"{pair_min(robots):.2f}",
                        "body_clearance_min_mm": f"{min_body_clearance(robots):.2f}",
                        "min_edge_mm": f"{min(body_edge_clearance(q) for q in robots):.2f}",
                        "group_progress_mm": f"{group_progress:.2f}",
                        "progress_spread_mm": f"{progress_spread:.2f}",
                        "rail_flow": f"{rail_flow:.3f}",
                        "robot": r.name, "x": f"{r.est.x:.2f}", "y": f"{r.est.y:.2f}",
                        "yaw": f"{r.est.yaw_deg:.2f}", "vx": f"{r.est.vx:.2f}",
                        "vy": f"{r.est.vy:.2f}", "speed": f"{r.est.speed:.2f}",
                        "target_x": f"{r.dbg_target_x:.2f}", "target_y": f"{r.dbg_target_y:.2f}",
                        "rail_along_mm": f"{r.rail_along_mm:.2f}",
                        "rail_cross_mm": f"{r.rail_cross_mm:.2f}",
                        "rail_remaining_mm": f"{r.rail_remaining_mm:.2f}",
                        "rail_forward_cmd": f"{r.rail_forward_cmd:.2f}",
                        "rail_sync_cmd": f"{r.rail_sync_cmd:.2f}",
                        "slot_error_mm": f"{r.slot_error_mm:.2f}", "mode": r.mode,
                        "cmd_world_heading": "" if r.cmd_heading_world is None else f"{r.cmd_heading_world:.2f}",
                        "cmd_speed": f"{r.cmd_speed:.1f}", "heading_bias_deg": f"{r.heading_bias_deg:.3f}",
                        "speed_scale": f"{r.speed_scale:.4f}",
                        "formation_trim_deg": f"{r.formation_trim_deg:.3f}",
                        "learning_samples": r.learning_samples,
                        "breakaway_cmd": f"{r.learned_breakaway_cmd:.1f}",
                        "rolling_floor_cmd": f"{r.learned_rolling_floor_cmd:.1f}",
                        "drive_gain_mm_s_per_cmd": f"{r.drive_gain_mm_s_per_cmd:.3f}",
                        "stiction_kicks": r.stiction_kicks,
                    })

                if now - last_log_flush >= LOG_FLUSH_PERIOD_S:
                    f.flush()
                    last_log_flush = now

                # The ATC target is now the ACTUAL moving virtual leader.
                guide_vx = guide_vy = 0.0
                if stats is not None:
                    guide_vx = stats["tx"] * ref_speed
                    guide_vy = stats["ty"] * ref_speed
                twin.update(
                    robots, phase, completed_laps, side_idx,
                    score_ref_x, score_ref_y, guide_vx, guide_vy,
                    cx, cy, crms, pair_min(robots), min_body_clearance(robots),
                    min(body_edge_clearance(q) for q in robots),
                    rail_flow=rail_flow,
                    progress_spread_mm=progress_spread,
                    max_cross_mm=(stats["max_abs_cross"] if stats else 0.0),
                    ref_speed=ref_speed,
                    goal_lag=goal_lag,
                    centroid_cross=(stats["center_cross"] if stats else 0.0),
                    ilc_trim=ilc_trim,
                    ilc_scale=path_ilc.get("cruise_scale", 1.0),
                )

                if now - last_print >= 1.0 / PRINT_HZ:
                    print(
                        f"t={elapsed:6.1f}s phase={phase:6s} lap={completed_laps:2d} "
                        f"side={(side_idx+1 if phase=='RUN' else 0)} "
                        f"goal=({score_ref_x:+6.0f},{score_ref_y:+6.0f}) "
                        f"vRef={ref_speed:5.0f} lag={goal_lag:+5.0f} "
                        f"centCross={(stats['center_cross'] if stats else 0):+5.0f} "
                        f"formRMS={crms:5.0f} spread={progress_spread:4.0f} "
                        f"pair={pair_min(robots):5.0f} "
                        f"ILC={ilc_trim:+4.1f}° scale={path_ilc.get('cruise_scale',1.0):.3f}"
                    )
                    last_print = now

                spent = time.monotonic() - now
                sleep = 1.0 / CONTROL_HZ - spent
                if sleep > 0:
                    time.sleep(sleep)

        finally:
            twin.close()
            stop_all(robots)
            save_learning(robots)
            save_path_ilc(path_ilc)
            signal.signal(signal.SIGINT, old_sig)
            print(f"Log: {log_path}")


# =============================================================================
# Dry-run simulator
# =============================================================================

class SimDriver:
    def __init__(self, body, name: str) -> None:
        self.body = body
        self.name = name
        self.basis = HeadingBasis(1.0, 0.0, 0.0, 1.0)
        self.last_h = 0
        self.last_speed = 0

    def set_basis(self, basis: HeadingBasis) -> None:
        self.basis = basis

    def command_internal(self, heading: float, speed: int) -> None:
        self.last_h = int(round(heading)) % 360
        self.last_speed = int(speed)
        self.body.target_heading = wrap360(
            self.basis.internal_to_world(heading) + self.body.command_error_deg
        )
        self.body.target_cmd = int(speed)

    def command_world(self, world_deg: float, speed: int, heading_bias_deg: float = 0.0) -> None:
        self.body.target_heading = wrap360(
            world_deg + heading_bias_deg + self.body.command_error_deg
        )
        self.body.target_cmd = int(speed)
        self.last_speed = int(speed)

    def stop_hold(self, force: bool = False) -> None:
        self.body.target_cmd = 0
        self.last_speed = 0


@dataclass
class SimBody:
    x: float
    y: float
    yaw: float
    command_error_deg: float = 0.0
    speed_gain: float = 1.0
    speed: float = 0.0
    target_heading: float = 0.0
    target_cmd: int = 0
    # Dry-run-only loaded-chariot friction model.  Below static_cmd a stopped
    # simulated robot does not move; once rolling, a much lower command can
    # sustain it.  This specifically exercises the v22 anti-stiction/auto-advance logic.
    static_cmd: int = 125
    rolling_cmd: int = 32


class SimVicon:
    def __init__(self, bodies: Dict[str, SimBody]) -> None:
        self.bodies = bodies
        self.last = time.monotonic()

    def read_all(self) -> Dict[str, Pose]:
        now = time.monotonic()
        dt = clamp(now - self.last, 0.0, 0.035)
        self.last = now
        for b in self.bodies.values():
            # Smooth chariot-ish response.
            err = wrap180(b.target_heading - b.yaw)
            b.yaw = wrap360(b.yaw + clamp(err, -210.0 * dt, 210.0 * dt))
            effective_cmd = b.target_cmd
            if b.speed < 14.0 and effective_cmd < b.static_cmd:
                effective_cmd = 0
            elif b.speed >= 14.0 and effective_cmd < b.rolling_cmd:
                effective_cmd = 0
            target_v = effective_cmd * MM_S_PER_SPEED_CMD * b.speed_gain
            tau = 0.25 if target_v > b.speed else 0.16
            b.speed += (target_v - b.speed) * clamp(dt / tau, 0.0, 1.0)
            # Less translation while badly misaligned.
            align = max(0.15, math.cos(math.radians(min(80.0, abs(err)))))
            b.x += b.speed * align * math.cos(math.radians(b.yaw)) * dt
            b.y += b.speed * align * math.sin(math.radians(b.yaw)) * dt
        return {n: Pose(b.x, b.y, b.yaw, False) for n, b in self.bodies.items()}

    def close(self) -> None:
        pass


def make_dry_robots() -> Tuple[SimVicon, List[Robot]]:
    # Similar spread to a representative hardware run.
    names = [item[0] for item in ROBOT_CONFIGS]
    starts = {
        names[0]: SimBody(-272.5, -87.3, 296.8, -18.0, 0.88, static_cmd=175, rolling_cmd=58),
        names[1]: SimBody(12.8, -57.5, 45.1, -65.0, 1.05, static_cmd=155, rolling_cmd=52),
        names[2]: SimBody(353.1, 32.9, 303.1, +85.0, 0.86, static_cmd=165, rolling_cmd=55),
    }
    vicon = SimVicon(starts)
    robots = []
    for name, subject, segment in ROBOT_CONFIGS:
        d = SimDriver(starts[name], name)
        robots.append(Robot(name, subject, segment, d))
    return vicon, robots


# =============================================================================
# CLI
# =============================================================================

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--side-mm", type=float, default=DEFAULT_SIDE_MM)
    p.add_argument("--laps", type=int, default=DEFAULT_LAPS, help="0 = continuous")
    p.add_argument("--max-speed", type=int, default=DEFAULT_MAX_SPEED_CMD)
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S, help="0 = no timeout")
    p.add_argument("--log", type=str, default=LOG_FILE)
    p.add_argument("--reuse-calibration", action="store_true", help="explicitly reuse the last VERIFIED reference calibration; default is a fresh hardware calibration every run")
    p.add_argument("--recalibrate", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-digital-twin", action="store_true", help="disable the live Tkinter Vicon/controller digital twin window")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    side = clamp(args.side_mm, MIN_SIDE_MM, MAX_SIDE_MM)
    max_cmd = int(clamp(args.max_speed, 100, 255))
    print(f"Controller: {CONTROLLER_VERSION}")
    print(f"RUNNING FILE: {Path(__file__).resolve()}")
    print(f"BOUNDARY POLICY: workspace comes from local configuration; optional extension={BOUNDARY_EXTENSION_MM:.0f} mm per side; recovery preserves square progress.")
    print(
        "Plan: MANDATORY fresh heading calibration -> two-axis CLOSED-LOOP Vicon command proof -> brief HOME -> TETHERED moving lookahead through ENTRY and around the square -> moving formation-slot tracking -> high-torque stiction recovery -> bounded collision bumper -> persistent per-side ILC + per-robot formation/speed learning -> separate-process professional ATC twin. No corner holds and no return-to-goal recorrection."
    )
    print("Robots: using three locally configured Sphero/Vicon mappings")

    if args.dry_run:
        vicon, robots = make_dry_robots()
        for r in robots:
            r.driver.set_basis(HeadingBasis(1.0, 0.0, 0.0, 1.0))
            r.heading_bias_deg = 0.0
        print("DRY-RUN: injecting asymmetric course errors and loaded-chariot stiction to test tethered moving-lookahead tracking.")
        verify_all_courses(vicon, robots)
        dry_laps = args.laps if args.laps > 0 else 1
        print(f"DRY-RUN: no hidden timeout; running {dry_laps} complete lap(s) unless --timeout is explicitly supplied.")
        run_mission(vicon, robots, side, dry_laps, max_cmd, args.timeout, Path(args.log), show_digital_twin=False)
        return

    with ExitStack() as stack:
        print(f"Connecting to Vicon {VICON_SERVER}...")
        vicon = ViconSystem(ROBOT_CONFIGS)
        stack.callback(vicon.close)
        poses = vicon.read_all()
        print("Connecting to all three Spheros...")
        robots = connect_hardware(stack, poses)
        stop_all(robots)

        # Fresh calibration is intentionally the DEFAULT.  an earlier revision silently reused
        # old/saturated trims, which is unsafe for a chariot whose mechanics can
        # change between placements.
        use_saved = bool(args.reuse_calibration) and (not args.recalibrate) and load_calibrations(robots)
        if use_saved:
            print("REUSING prior VERIFIED reference calibration because --reuse-calibration was explicitly requested.")
        else:
            print("FRESH CALIBRATION REQUIRED: static 0/90 displacement + two-axis closed-loop Vicon command verification.")
            calibrate_all(vicon, robots)
        load_learning(robots)

        print("Starting Vicon-controlled swarm in 1.5 seconds. Ctrl+C stops all robots.")
        time.sleep(1.5)
        run_mission(vicon, robots, side, args.laps, max_cmd, args.timeout, Path(args.log).resolve(), show_digital_twin=not args.no_digital_twin)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted.")
    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}")
        raise