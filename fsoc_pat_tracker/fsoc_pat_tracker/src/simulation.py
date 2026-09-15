"""
simulation.py — Owner: Electrical A (Arpitha)
Generate scene, beacon target, camera crop/viewport, motion patterns, disturbance injection.

STATUS: Mostly done. Port from your existing Layer 1 (target generator) and
Layer 2 (ingestion) code — this file is a rename/merge job, not new work:
  - Layer 1 -> generate_world_frame() / build_targets()
  - Layer 2 -> get_next_frame() (handles simulation vs .mp4 video-bypass mode)
  - camera_viewport.py -> apply_camera_crop()

Must output a FramePacket (see interfaces.py) every call.
"""

from config import WORLD_WIDTH_PX, WORLD_HEIGHT_PX, CAMERA_RES_WIDTH_PX, CAMERA_RES_HEIGHT_PX
from interfaces import FramePacket


def build_targets(motion_type: str, num_targets: int = 1, seed: int = None):
    """TODO: port from Layer 1. Returns target state generator (position per frame)."""
    raise NotImplementedError


def generate_world_frame(frame_id: int, targets) -> "np.ndarray":
    """TODO: port from Layer 1. Renders the 2000x2000 world frame with targets drawn."""
    raise NotImplementedError


def apply_camera_crop(world_frame, camera_center_xy) -> "np.ndarray":
    """TODO: port from camera_viewport.py. Crops world frame to the 640x480 / 4x3deg FOV view."""
    raise NotImplementedError


def get_next_frame(mode: str, frame_id: int, video_capture=None) -> FramePacket:
    """
    TODO: port from Layer 2 (layer2_ingestion.py).
    mode == "simulation": calls build_targets() + generate_world_frame() directly, no file needed.
    mode == "video": reads a real .mp4 via cv2.VideoCapture (video_capture).
    Both paths must converge on apply_camera_crop() before returning.
    """
    raise NotImplementedError
