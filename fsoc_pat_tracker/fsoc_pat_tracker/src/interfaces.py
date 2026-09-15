"""
interfaces.py — Shared data contract (owner: CS, per Task Distribution doc)

Every module talks to every other module ONLY through these types.
If a field is fixed here, integration stays easy. Nobody renames a field
after it's in use without full-team agreement.

Pipeline: simulation.py -> tracking.py -> predictor.py -> control.py
                        -> analytics.py -> reporting.py -> app.py/gui.py
"""

from dataclasses import dataclass, field
from typing import Optional, Literal


# ---------------------------------------------------------------------------
# simulation.py -> tracking.py
# ---------------------------------------------------------------------------
@dataclass
class FramePacket:
    """One frame handed from the world/camera simulation to the tracker."""
    frame_id: int
    timestamp_s: float
    image: "np.ndarray"          # 480x640 (or camera res) frame, post-viewport-crop
    camera_center_world_xy: tuple  # (x, y) of camera center in the 2000x2000 world
    source: Literal["simulation", "video"]


# ---------------------------------------------------------------------------
# tracking.py -> predictor.py
# ---------------------------------------------------------------------------
@dataclass
class TrackResult:
    """Detection output for one frame."""
    frame_id: int
    detected: bool
    centroid_px: Optional[tuple]   # (x, y) in camera-frame pixel coords, None if not detected
    confidence: float              # 0.0-1.0
    blob_area_px: Optional[float] = None


# ---------------------------------------------------------------------------
# predictor.py -> control.py / analytics.py
# ---------------------------------------------------------------------------
@dataclass
class PredictionResult:
    """KF/EKF state estimate, used even during blackout frames."""
    frame_id: int
    predicted_centroid_px: tuple   # (x, y), always populated (holds through loss)
    predicted_velocity_px_s: tuple  # (vx, vy)
    is_prediction_only: bool       # True if this frame had no real detection


# ---------------------------------------------------------------------------
# control.py -> simulation.py (camera actuation) / analytics.py
# ---------------------------------------------------------------------------
@dataclass
class ControlCommand:
    """PTZ command issued this frame."""
    frame_id: int
    pan_delta_deg: float
    tilt_delta_deg: float
    pat_state: Literal["SEARCH", "ACQUIRE", "TRACK", "LOST", "REACQUIRE", "HANDOVER_READY"]
    saturated: bool = False        # True if speed clamp (5-10 deg/s) was hit


# ---------------------------------------------------------------------------
# analytics.py -> reporting.py (Electrical A's angle/FOV/range layer — TODO, not yet built)
# ---------------------------------------------------------------------------
@dataclass
class AngleData:
    """Pixel-to-angle domain interpretation. Currently unimplemented (Electrical A role)."""
    frame_id: int
    pan_angle_deg: float
    tilt_angle_deg: float
    target_azimuth_deg: Optional[float] = None
    target_elevation_deg: Optional[float] = None
    angular_error_deg: Optional[float] = None
    range_estimate_m: Optional[float] = None


# ---------------------------------------------------------------------------
# Everything -> reporting.py (one row per frame, exported to CSV/JSON/Excel)
# ---------------------------------------------------------------------------
@dataclass
class TelemetryRow:
    frame_id: int
    timestamp_s: float
    detected: bool
    tracking_error_px: Optional[float]
    pat_state: str
    pan_angle_deg: Optional[float] = None
    tilt_angle_deg: Optional[float] = None
    fps: Optional[float] = None
