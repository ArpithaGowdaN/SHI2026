"""
control.py — Owner: Electrical B
PTZ motion commands: PID control on pixel error, speed saturation, the
PAT state machine (SEARCH / ACQUIRE / TRACK / LOST / REACQUIRE /
HANDOVER_READY), and an expanding-spiral reacquisition search pattern.
Built from scratch to match the ControlCommand contract in interfaces.py.
"""

import math

from config import (
    MAX_PAN_SPEED_DEG_S, MAX_TILT_SPEED_DEG_S,
    PID_KP, PID_KI, PID_KD,
    LOST_THRESHOLD_FRAMES,
    CAMERA_FOV_DEG_X, CAMERA_FOV_DEG_Y,
    CAMERA_RES_WIDTH_PX, CAMERA_RES_HEIGHT_PX,
)
from interfaces import PredictionResult, ControlCommand

DEG_PER_PX_X = CAMERA_FOV_DEG_X / CAMERA_RES_WIDTH_PX
DEG_PER_PX_Y = CAMERA_FOV_DEG_Y / CAMERA_RES_HEIGHT_PX

ACQUIRE_STABLE_FRAMES = 5     # consecutive good-detection frames before ACQUIRE -> TRACK
SEARCH_ANGULAR_STEP_DEG = 12  # spiral angle step per frame
SEARCH_RADIUS_GROWTH_PX = 4   # spiral radius growth per frame
SEARCH_RADIUS_MAX_PX = 300    # cap so the spiral doesn't run off the world


class ControlState:
    def __init__(self):
        self.pat_state = "SEARCH"
        self.lost_frame_count = 0
        self.stable_track_count = 0
        self.search_angle_deg = 0.0
        self.search_radius_px = 20.0
        self.pid_integral_pan = 0.0
        self.pid_integral_tilt = 0.0
        self.prev_error_pan = 0.0
        self.prev_error_tilt = 0.0


_state = ControlState()


def reset():
    """Call at the start of a new run (e.g. new simulation session)."""
    global _state
    _state = ControlState()


def _pixel_offset_to_deg(centroid_px: tuple) -> tuple:
    """Same linear FOV mapping analytics.py uses, kept local here so
    control.py has no dependency on analytics.py (they're independent
    files per the PS's ownership split)."""
    dx_px = centroid_px[0] - CAMERA_RES_WIDTH_PX / 2
    dy_px = centroid_px[1] - CAMERA_RES_HEIGHT_PX / 2
    return dx_px * DEG_PER_PX_X, dy_px * DEG_PER_PX_Y


def _pid_step(error_pan_deg: float, error_tilt_deg: float, dt: float) -> tuple:
    """Simple PID with integral clamping (anti-windup)."""
    _state.pid_integral_pan = max(-50, min(50, _state.pid_integral_pan + error_pan_deg * dt))
    _state.pid_integral_tilt = max(-50, min(50, _state.pid_integral_tilt + error_tilt_deg * dt))

    deriv_pan = (error_pan_deg - _state.prev_error_pan) / dt if dt > 0 else 0.0
    deriv_tilt = (error_tilt_deg - _state.prev_error_tilt) / dt if dt > 0 else 0.0

    pan_speed = PID_KP * error_pan_deg + PID_KI * _state.pid_integral_pan + PID_KD * deriv_pan
    tilt_speed = PID_KP * error_tilt_deg + PID_KI * _state.pid_integral_tilt + PID_KD * deriv_tilt

    _state.prev_error_pan = error_pan_deg
    _state.prev_error_tilt = error_tilt_deg

    return pan_speed, tilt_speed


def _saturate(pan_speed: float, tilt_speed: float, dt: float) -> tuple:
    """Clamp commanded speed to the PS's max pan/tilt speed, and convert
    speed (deg/s) into this frame's actual angle delta (deg)."""
    saturated = False
    if abs(pan_speed) > MAX_PAN_SPEED_DEG_S:
        pan_speed = math.copysign(MAX_PAN_SPEED_DEG_S, pan_speed)
        saturated = True
    if abs(tilt_speed) > MAX_TILT_SPEED_DEG_S:
        tilt_speed = math.copysign(MAX_TILT_SPEED_DEG_S, tilt_speed)
        saturated = True
    return pan_speed * dt, tilt_speed * dt, saturated


def run_search_pattern(dt: float) -> tuple:
    """
    Expanding-spiral search: sweeps outward from the last known position
    so a lost target re-enters the FOV even if it moved during the gap,
    without needing a full raster scan of the whole world.
    Returns (pan_delta_deg, tilt_delta_deg) for this frame.
    """
    _state.search_angle_deg = (_state.search_angle_deg + SEARCH_ANGULAR_STEP_DEG) % 360
    _state.search_radius_px = min(SEARCH_RADIUS_MAX_PX,
                                   _state.search_radius_px + SEARCH_RADIUS_GROWTH_PX)

    theta = math.radians(_state.search_angle_deg)
    # convert this frame's incremental spiral step (in pixel-equivalents)
    # into a small pan/tilt delta, capped by the max slew speed
    step_px = SEARCH_RADIUS_GROWTH_PX + 0.1 * _state.search_radius_px
    pan_delta = step_px * DEG_PER_PX_X * math.cos(theta)
    tilt_delta = step_px * DEG_PER_PX_Y * math.sin(theta)

    max_pan_delta = MAX_PAN_SPEED_DEG_S * dt
    max_tilt_delta = MAX_TILT_SPEED_DEG_S * dt
    pan_delta = max(-max_pan_delta, min(max_pan_delta, pan_delta))
    tilt_delta = max(-max_tilt_delta, min(max_tilt_delta, tilt_delta))

    return pan_delta, tilt_delta


def update_pat_state(track_valid: bool, confidence: float) -> str:
    """
    Advances the PAT state machine by one frame and returns the new state.
    track_valid: True if this frame had a real detection (not prediction-only).
    """
    s = _state

    if s.pat_state == "SEARCH":
        if track_valid and confidence > 0.5:
            s.pat_state = "ACQUIRE"
            s.stable_track_count = 1
        # else stay in SEARCH

    elif s.pat_state == "ACQUIRE":
        if track_valid and confidence > 0.5:
            s.stable_track_count += 1
            if s.stable_track_count >= ACQUIRE_STABLE_FRAMES:
                s.pat_state = "TRACK"
        else:
            s.stable_track_count = 0
            s.pat_state = "SEARCH"

    elif s.pat_state == "TRACK":
        if track_valid:
            s.lost_frame_count = 0
        else:
            s.lost_frame_count += 1
            if s.lost_frame_count >= LOST_THRESHOLD_FRAMES:
                s.pat_state = "LOST"

    elif s.pat_state == "LOST":
        s.pat_state = "REACQUIRE"
        s.search_angle_deg = 0.0
        s.search_radius_px = 20.0

    elif s.pat_state == "REACQUIRE":
        if track_valid and confidence > 0.5:
            s.pat_state = "ACQUIRE"
            s.stable_track_count = 1
            s.lost_frame_count = 0
        # else keep spiraling

    return s.pat_state


def compute_command(frame_id: int, prediction: PredictionResult,
                     track_valid: bool, confidence: float,
                     dt: float = 1 / 30) -> ControlCommand:
    """
    Main entry point: call once per frame. Advances the PAT state machine,
    then either runs PID toward the predicted target position (TRACK/
    ACQUIRE) or runs the search pattern (SEARCH/REACQUIRE).
    """
    new_state = update_pat_state(track_valid, confidence)

    if new_state in ("SEARCH", "REACQUIRE"):
        pan_delta, tilt_delta = run_search_pattern(dt)
        saturated = False
    else:  # ACQUIRE or TRACK
        error_pan_deg, error_tilt_deg = _pixel_offset_to_deg(prediction.predicted_centroid_px)
        pan_speed, tilt_speed = _pid_step(error_pan_deg, error_tilt_deg, dt)
        pan_delta, tilt_delta, saturated = _saturate(pan_speed, tilt_speed, dt)

    return ControlCommand(
        frame_id=frame_id,
        pan_delta_deg=pan_delta,
        tilt_delta_deg=tilt_delta,
        pat_state=new_state,
        saturated=saturated,
    )
