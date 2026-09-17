"""
app.py — Owner: CS (Arpitha)
Main execution engine: calls every module in the correct order, once per
frame, for both simulation mode and video mode. This is the layer gui.py
sits on top of, and also what run_demo.bat / a headless script calls
directly without any GUI at all.

Pipeline order (per the project structure doc):
simulation.py -> tracking.py -> predictor.py -> control.py -> analytics.py
-> reporting.py
"""

import time

import simulation
import tracking
import predictor
import control
import analytics
import reporting
from interfaces import TelemetryRow
from config import (
    CAMERA_RES_WIDTH_PX, CAMERA_RES_HEIGHT_PX,
    WORLD_WIDTH_PX, WORLD_HEIGHT_PX,
)


class SimulationSession:
    """
    Holds all state for one run (simulation OR video mode) and advances
    it one frame at a time via step(). GUI-agnostic — gui.py drives this
    class; it never touches tracking/predictor/control/analytics directly.
    """

    def __init__(self, mode: str = "simulation", motion_type: str = "random",
                 num_targets: int = 1, seed: int = None,
                 video_path: str = None, dt: float = 1 / 30):
        self.mode = mode
        self.dt = dt
        self.frame_id = 0

        predictor.reset()
        control.reset()

        self.cam_pan_deg = 0.0
        self.cam_tilt_deg = 0.0
        self.cam_x = WORLD_WIDTH_PX / 2
        self.cam_y = WORLD_HEIGHT_PX / 2

        self.telemetry_rows = []
        self.stable_frame_count = 0  # for handover-ready tracking
        self.handover_ready = False

        if mode == "simulation":
            self.targets = simulation.build_targets(motion_type=motion_type,
                                                      num_targets=num_targets, seed=seed)
            self.video_capture = None
        elif mode == "video":
            if video_path is None:
                raise ValueError("video_path is required when mode='video'")
            import cv2
            self.video_capture = cv2.VideoCapture(video_path)
            if not self.video_capture.isOpened():
                raise FileNotFoundError(f"Could not open video: {video_path}")
            self.targets = None
        else:
            raise ValueError(f"Unknown mode: {mode!r}")

        self.finished = False

    def step(self):
        """
        Advance one frame through the full pipeline. Returns a dict with
        everything the GUI (or a headless caller) needs to display/log,
        or None if the session has ended (video mode ran out of frames).
        """
        if self.finished:
            return None

        if self.mode == "simulation":
            for t in self.targets:
                t.step(self.dt)
            pkt = simulation.get_next_frame(
                "simulation", self.frame_id, self.frame_id * self.dt,
                (self.cam_x, self.cam_y), targets=self.targets,
            )
        else:
            pkt = simulation.get_next_frame(
                "video", self.frame_id, self.frame_id * self.dt,
                (self.cam_x, self.cam_y), video_capture=self.video_capture,
            )
            if pkt is None:
                self.finished = True
                return None

        track = tracking.process_frame(pkt)
        pred = predictor.predict(self.frame_id, track, dt=self.dt)
        cmd = control.compute_command(self.frame_id, pred, track_valid=track.detected,
                                       confidence=track.confidence, dt=self.dt)

        self.cam_pan_deg += cmd.pan_delta_deg
        self.cam_tilt_deg += cmd.tilt_delta_deg

        # simulation mode: physically move the virtual camera in the world
        # by converting the commanded angle delta back into world pixels,
        # so next frame's crop actually reflects the pan/tilt motion
        if self.mode == "simulation":
            px_per_deg_x = CAMERA_RES_WIDTH_PX / simulation.CAMERA_FOV_DEG_X
            px_per_deg_y = CAMERA_RES_HEIGHT_PX / simulation.CAMERA_FOV_DEG_Y
            self.cam_x += cmd.pan_delta_deg * px_per_deg_x
            self.cam_y += cmd.tilt_delta_deg * px_per_deg_y

        angle_data = analytics.compute_angle_data(
            self.frame_id, track, pred, self.cam_pan_deg, self.cam_tilt_deg
        )

        if angle_data.angular_error_deg is not None and angle_data.angular_error_deg <= 0.5:
            self.stable_frame_count += 1
        else:
            self.stable_frame_count = 0
        self.handover_ready = analytics.check_handover_ready(
            angle_data.angular_error_deg or 999, self.stable_frame_count
        )

        tracking_error_px = None
        if track.detected and track.centroid_px:
            frame_center = (CAMERA_RES_WIDTH_PX / 2, CAMERA_RES_HEIGHT_PX / 2)
            tracking_error_px = (
                (track.centroid_px[0] - frame_center[0]) ** 2
                + (track.centroid_px[1] - frame_center[1]) ** 2
            ) ** 0.5

        row = TelemetryRow(
            frame_id=self.frame_id, timestamp_s=self.frame_id * self.dt,
            detected=track.detected, tracking_error_px=tracking_error_px,
            pat_state=cmd.pat_state, pan_angle_deg=self.cam_pan_deg,
            tilt_angle_deg=self.cam_tilt_deg, fps=1 / self.dt,
        )
        self.telemetry_rows.append(row)
        self.frame_id += 1

        return {
            "frame_id": row.frame_id,
            "image": pkt.image,
            "track": track,
            "prediction": pred,
            "command": cmd,
            "angle_data": angle_data,
            "handover_ready": self.handover_ready,
            "telemetry_row": row,
        }

    def run_headless(self, max_frames: int = 300):
        """Run to completion (or max_frames) with no display, for
        run_demo.bat / scripted use. Returns the reporting summary."""
        for _ in range(max_frames):
            result = self.step()
            if result is None:
                break
        return reporting.compute_summary(self.telemetry_rows)

    def export_results(self, output_dir: str = None, prefix: str = "run"):
        kwargs = {"prefix": prefix}
        if output_dir:
            kwargs["output_dir"] = output_dir
        return reporting.export_all(self.telemetry_rows, **kwargs)

    def close(self):
        if self.video_capture is not None:
            self.video_capture.release()


def run_demo(motion_type: str = "circular", num_frames: int = 300, seed: int = 42):
    """Entry point for run_demo.bat — a fully headless simulation-mode
    demo run, printing a summary at the end."""
    session = SimulationSession(mode="simulation", motion_type=motion_type, seed=seed)
    summary = session.run_headless(max_frames=num_frames)
    session.export_results(prefix="demo")
    session.close()
    print("Demo run complete.")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    return summary


if __name__ == "__main__":
    run_demo()
