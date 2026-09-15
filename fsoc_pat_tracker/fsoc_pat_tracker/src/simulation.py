"""
simulation.py — Owner: Electrical A (Arpitha)
Generates the world scene, moving beacon target(s), and the camera
viewport crop. Also handles reading a real .mp4 for benchmark/video mode.
Built from scratch to match the FramePacket contract in interfaces.py.
"""

import math
import random
import numpy as np
import cv2

from config import (
    WORLD_WIDTH_PX, WORLD_HEIGHT_PX,
    CAMERA_RES_WIDTH_PX, CAMERA_RES_HEIGHT_PX,
    CAMERA_FOV_DEG_X, CAMERA_FOV_DEG_Y,
    TARGET_SIZE_DEFAULT_PX, TARGET_SHAPE_DEFAULT,
)
from interfaces import FramePacket


# ---------------------------------------------------------------------------
# Target state
# ---------------------------------------------------------------------------
class Target:
    """One moving beacon target."""

    def __init__(self, motion_type: str, size_px: int = TARGET_SIZE_DEFAULT_PX,
                 shape: str = TARGET_SHAPE_DEFAULT, start_xy: tuple = None,
                 seed: int = None):
        self.motion_type = motion_type
        self.size_px = size_px
        self.shape = shape
        self.rng = random.Random(seed)

        cx, cy = WORLD_WIDTH_PX / 2, WORLD_HEIGHT_PX / 2
        if start_xy is not None:
            self.x, self.y = start_xy
        elif motion_type in ("circular", "figure_8", "spiral"):
            # keep these motions close enough to center that a camera
            # starting at center can realistically acquire them
            self.x = cx + self.rng.uniform(-150, 150)
            self.y = cy + self.rng.uniform(-150, 150)
        else:
            self.x = self.rng.uniform(200, WORLD_WIDTH_PX - 200)
            self.y = self.rng.uniform(200, WORLD_HEIGHT_PX - 200)

        self.origin_x, self.origin_y = self.x, self.y
        self.t = 0.0
        self.vx, self.vy = self.rng.uniform(-40, 40), self.rng.uniform(-40, 40)

    def step(self, dt: float):
        self.t += dt
        if self.motion_type == "straight_line":
            self.x += self.vx * dt
            self.y += self.vy * dt
        elif self.motion_type == "circular":
            radius = 120
            self.x = self.origin_x + radius * math.cos(self.t)
            self.y = self.origin_y + radius * math.sin(self.t)
        elif self.motion_type == "figure_8":
            radius = 120
            self.x = self.origin_x + radius * math.sin(self.t)
            self.y = self.origin_y + radius * math.sin(self.t) * math.cos(self.t)
        elif self.motion_type == "random":
            self.vx += self.rng.uniform(-15, 15)
            self.vy += self.rng.uniform(-15, 15)
            self.vx = max(-60, min(60, self.vx))
            self.vy = max(-60, min(60, self.vy))
            self.x += self.vx * dt
            self.y += self.vy * dt
        elif self.motion_type == "spiral":
            radius = 20 + 8 * self.t
            self.x = self.origin_x + radius * math.cos(self.t)
            self.y = self.origin_y + radius * math.sin(self.t)
        elif self.motion_type == "sinusoidal":
            self.x = self.origin_x + 60 * self.t
            self.y = self.origin_y + 100 * math.sin(self.t)
        else:
            raise ValueError(f"Unknown motion_type: {self.motion_type}")

        # keep target inside world bounds
        self.x = max(0, min(WORLD_WIDTH_PX, self.x))
        self.y = max(0, min(WORLD_HEIGHT_PX, self.y))

    @property
    def position(self) -> tuple:
        return (self.x, self.y)


def build_targets(motion_type: str = "random", num_targets: int = 1,
                   seed: int = None) -> list:
    """Create `num_targets` Target objects with the given motion type."""
    targets = []
    for i in range(num_targets):
        t_seed = None if seed is None else seed + i
        targets.append(Target(motion_type=motion_type, seed=t_seed))
    return targets


def generate_world_frame(targets: list) -> np.ndarray:
    """Render the full 2000x2000 monochrome world frame with targets drawn."""
    frame = np.zeros((WORLD_HEIGHT_PX, WORLD_WIDTH_PX), dtype=np.uint8)
    for t in targets:
        x, y = int(t.position[0]), int(t.position[1])
        half = t.size_px // 2
        if t.shape == "square":
            cv2.rectangle(frame, (x - half, y - half), (x + half, y + half), 255, -1)
        else:  # circle
            cv2.circle(frame, (x, y), half, 255, -1)
    return frame


def apply_camera_crop(world_frame: np.ndarray, camera_center_xy: tuple) -> np.ndarray:
    """
    Crop the world frame down to the camera's 640x480 view centered at
    camera_center_xy, clamping so the crop never runs off the world edges.
    """
    cx, cy = camera_center_xy
    half_w, half_h = CAMERA_RES_WIDTH_PX // 2, CAMERA_RES_HEIGHT_PX // 2

    x0 = int(max(0, min(WORLD_WIDTH_PX - CAMERA_RES_WIDTH_PX, cx - half_w)))
    y0 = int(max(0, min(WORLD_HEIGHT_PX - CAMERA_RES_HEIGHT_PX, cy - half_h)))
    x1, y1 = x0 + CAMERA_RES_WIDTH_PX, y0 + CAMERA_RES_HEIGHT_PX

    return world_frame[y0:y1, x0:x1].copy()


def get_next_frame(mode: str, frame_id: int, timestamp_s: float,
                    camera_center_xy: tuple, targets: list = None,
                    video_capture: cv2.VideoCapture = None) -> FramePacket:
    """
    Returns one FramePacket.
    mode == "simulation": renders from `targets` directly, no file needed.
    mode == "video": reads the next frame from `video_capture` (a real .mp4).
    """
    if mode == "simulation":
        world_frame = generate_world_frame(targets)
        cropped = apply_camera_crop(world_frame, camera_center_xy)
        return FramePacket(
            frame_id=frame_id,
            timestamp_s=timestamp_s,
            image=cropped,
            camera_center_world_xy=camera_center_xy,
            source="simulation",
        )
    elif mode == "video":
        if video_capture is None:
            raise ValueError("video_capture is required when mode='video'")
        ok, frame = video_capture.read()
        if not ok:
            return None  # end of video
        if frame.ndim == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # ISRO benchmark videos already come as the camera's own 640x480
        # view, so no crop is applied here — passed through as-is.
        return FramePacket(
            frame_id=frame_id,
            timestamp_s=timestamp_s,
            image=frame,
            camera_center_world_xy=camera_center_xy,
            source="video",
        )
    else:
        raise ValueError(f"Unknown mode: {mode!r} (expected 'simulation' or 'video')")
