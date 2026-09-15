"""
analytics.py — Owner: Electrical A (Arpitha)
Convert pixels to angles: pan/tilt angle, target azimuth/elevation, angular
error, range, PAT state interpretation.

STATUS: NOT YET BUILT. This is the one module with no existing code to port —
start here after simulation.py is confirmed working end-to-end.

Core idea: camera FOV (4deg x 3deg) maps linearly across the 640x480 frame,
so a pixel offset from frame-center converts directly to an angular offset
from the camera's current boresight.
"""

from config import CAMERA_FOV_DEG_X, CAMERA_FOV_DEG_Y, CAMERA_RES_WIDTH_PX, CAMERA_RES_HEIGHT_PX
from interfaces import TrackResult, PredictionResult, AngleData


def pixel_to_angle_offset(centroid_px: tuple) -> tuple:
    """
    TODO: Convert a centroid's pixel offset from frame-center into
    (pan_offset_deg, tilt_offset_deg) using linear FOV mapping:
        deg_per_px_x = CAMERA_FOV_DEG_X / CAMERA_RES_WIDTH_PX
        deg_per_px_y = CAMERA_FOV_DEG_Y / CAMERA_RES_HEIGHT_PX
    """
    raise NotImplementedError


def compute_angle_data(
    frame_id: int,
    track: TrackResult,
    prediction: PredictionResult,
    current_pan_deg: float,
    current_tilt_deg: float,
) -> AngleData:
    """
    TODO: Combine current camera boresight (pan/tilt) with the pixel offset
    from pixel_to_angle_offset() to produce absolute target azimuth/elevation,
    angular error, and (optionally) a range estimate if target size is known.
    """
    raise NotImplementedError


def check_handover_ready(angular_error_deg: float, stable_frame_count: int, threshold_deg: float = 0.5,
                          required_frames: int = 30) -> bool:
    """TODO: Fine-alignment handover flag — True once error stays under
    threshold_deg for required_frames consecutive frames."""
    raise NotImplementedError
