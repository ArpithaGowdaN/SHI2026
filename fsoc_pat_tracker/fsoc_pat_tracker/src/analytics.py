"""
analytics.py — Owner: Electrical A (Arpitha)
Converts pixel-domain tracking results into angle-domain PAT quantities:
pan/tilt angle offset, absolute target azimuth/elevation, angular error,
range estimate, and the fine-alignment handover condition.

Built from scratch. Uses only config.py's FOV/resolution constants, so it
does not need tracking.py / predictor.py / control.py to exist yet — only
their *output shapes*, as defined in interfaces.py.
"""

import math
from dataclasses import dataclass
from typing import Optional

from config import (
    CAMERA_FOV_DEG_X, CAMERA_FOV_DEG_Y,
    CAMERA_RES_WIDTH_PX, CAMERA_RES_HEIGHT_PX,
)
from interfaces import TrackResult, PredictionResult, AngleData

# Degrees of angular offset per pixel, along each axis. Assumes the FOV
# maps linearly across the sensor — true for a narrow FOV like 4deg x 3deg,
# where the small-angle approximation holds well.
DEG_PER_PX_X = CAMERA_FOV_DEG_X / CAMERA_RES_WIDTH_PX
DEG_PER_PX_Y = CAMERA_FOV_DEG_Y / CAMERA_RES_HEIGHT_PX


def pixel_to_angle_offset(centroid_px: tuple) -> tuple:
    """
    Convert a centroid's pixel position into (pan_offset_deg, tilt_offset_deg)
    relative to the frame center (the camera's current boresight).

    Positive pan_offset_deg = target is to the right of boresight.
    Positive tilt_offset_deg = target is BELOW boresight (image y grows
    downward), matching typical image coordinate convention.
    """
    frame_center_x = CAMERA_RES_WIDTH_PX / 2
    frame_center_y = CAMERA_RES_HEIGHT_PX / 2

    dx_px = centroid_px[0] - frame_center_x
    dy_px = centroid_px[1] - frame_center_y

    pan_offset_deg = dx_px * DEG_PER_PX_X
    tilt_offset_deg = dy_px * DEG_PER_PX_Y

    return (pan_offset_deg, tilt_offset_deg)


def estimate_range(target_size_px: float, known_target_size_m: float = None,
                    focal_length_px: float = None) -> Optional[float]:
    """
    Optional range estimate via the standard pinhole 'similar triangles'
    relation: range = (known_real_size * focal_length_px) / apparent_size_px.
    Returns None if the physical target size isn't known (which is the
    normal case for this PS — range is explicitly optional/unspecified).
    """
    if known_target_size_m is None or focal_length_px is None or target_size_px <= 0:
        return None
    return (known_target_size_m * focal_length_px) / target_size_px


def compute_angle_data(
    frame_id: int,
    track: TrackResult,
    prediction: PredictionResult,
    current_pan_deg: float,
    current_tilt_deg: float,
) -> AngleData:
    """
    Combine the camera's current boresight (from control.py, once it
    exists — passed in as a plain float here so this file has zero
    dependency on control.py) with the pixel offset to get absolute
    target azimuth/elevation and the angular pointing error.

    Uses the PREDICTED centroid (not just the raw detection), so this
    still returns a valid angle even on frames where the target wasn't
    directly detected (prediction.is_prediction_only == True).
    """
    pan_offset_deg, tilt_offset_deg = pixel_to_angle_offset(prediction.predicted_centroid_px)

    target_azimuth_deg = current_pan_deg + pan_offset_deg
    target_elevation_deg = current_tilt_deg - tilt_offset_deg  # tilt convention: up is positive

    # angular error = straight-line angular distance from boresight to target
    angular_error_deg = math.hypot(pan_offset_deg, tilt_offset_deg)

    range_estimate_m = None
    if track.detected and track.blob_area_px:
        approx_size_px = math.sqrt(track.blob_area_px)
        range_estimate_m = estimate_range(approx_size_px)  # None unless caller supplies real params

    return AngleData(
        frame_id=frame_id,
        pan_angle_deg=current_pan_deg,
        tilt_angle_deg=current_tilt_deg,
        target_azimuth_deg=target_azimuth_deg,
        target_elevation_deg=target_elevation_deg,
        angular_error_deg=angular_error_deg,
        range_estimate_m=range_estimate_m,
    )


def check_handover_ready(angular_error_deg: float, stable_frame_count: int,
                          threshold_deg: float = 0.5, required_frames: int = 30) -> bool:
    """
    Fine-alignment handover condition: True once the angular pointing
    error has stayed under threshold_deg for required_frames consecutive
    frames (default: 0.5deg held for 30 frames, i.e. 1 second at 30fps).
    """
    return angular_error_deg <= threshold_deg and stable_frame_count >= required_frames
