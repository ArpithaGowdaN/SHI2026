"""
benchmark.py — Owner: CS (Arpitha)
Loads an external .mp4 (+ optional ground-truth centroid CSV), runs it
through the same simulation.py(video mode) -> tracking.py -> predictor.py
-> control.py pipeline used in simulation mode, and computes the metrics
the PS's Benchmark Performance-2 stage evaluates: centroid RMSE (if truth
provided), acquisition/re-acquisition time, lock retention rate, FPS.
Built from scratch.
"""

import time
import csv

import cv2
import pandas as pd

import simulation
import tracking
import predictor
import control
import reporting
from interfaces import TelemetryRow


def load_truth_csv(path: str) -> pd.DataFrame:
    """
    Optional ground-truth centroid CSV, expected columns: frame_id, x, y.
    Returns a DataFrame indexed by frame_id for fast lookup.
    """
    df = pd.read_csv(path)
    required = {"frame_id", "x", "y"}
    if not required.issubset(df.columns):
        raise ValueError(f"Truth CSV must have columns {required}, got {list(df.columns)}")
    return df.set_index("frame_id")


def run_benchmark(video_path: str, truth_csv_path: str = None,
                   fps: float = 30.0, save_outputs: bool = True,
                   output_prefix: str = "benchmark") -> dict:
    """
    Runs the full detection/prediction/control pipeline over an external
    video and returns a metrics dict. If save_outputs is True, also
    writes CSV/Excel/JSON/plots via reporting.export_all().
    """
    truth_df = load_truth_csv(truth_csv_path) if truth_csv_path else None

    predictor.reset()
    control.reset()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video: {video_path}")

    dt = 1.0 / fps
    rows = []
    cam_pan_deg, cam_tilt_deg = 0.0, 0.0
    squared_errors = []

    frame_id = 0
    wall_start = time.time()
    while True:
        pkt = simulation.get_next_frame(
            mode="video", frame_id=frame_id, timestamp_s=frame_id * dt,
            camera_center_xy=(0, 0), video_capture=cap,
        )
        if pkt is None:
            break  # end of video

        track = tracking.process_frame(pkt)
        pred = predictor.predict(frame_id, track, dt=dt)
        cmd = control.compute_command(frame_id, pred, track_valid=track.detected,
                                       confidence=track.confidence, dt=dt)

        cam_pan_deg += cmd.pan_delta_deg
        cam_tilt_deg += cmd.tilt_delta_deg

        tracking_error_px = None
        if track.detected and track.centroid_px:
            frame_center = (simulation.CAMERA_RES_WIDTH_PX / 2, simulation.CAMERA_RES_HEIGHT_PX / 2)
            tracking_error_px = (
                (track.centroid_px[0] - frame_center[0]) ** 2
                + (track.centroid_px[1] - frame_center[1]) ** 2
            ) ** 0.5

        # ground-truth comparison, if provided
        if truth_df is not None and frame_id in truth_df.index and track.centroid_px:
            tx, ty = truth_df.loc[frame_id, "x"], truth_df.loc[frame_id, "y"]
            err = ((track.centroid_px[0] - tx) ** 2 + (track.centroid_px[1] - ty) ** 2) ** 0.5
            squared_errors.append(err ** 2)

        rows.append(TelemetryRow(
            frame_id=frame_id, timestamp_s=frame_id * dt, detected=track.detected,
            tracking_error_px=tracking_error_px, pat_state=cmd.pat_state,
            pan_angle_deg=cam_pan_deg, tilt_angle_deg=cam_tilt_deg, fps=fps,
        ))
        frame_id += 1

    cap.release()
    wall_elapsed_s = time.time() - wall_start
    processing_fps = frame_id / wall_elapsed_s if wall_elapsed_s > 0 else None

    summary = reporting.compute_summary(rows)
    summary["frames_processed"] = frame_id
    summary["processing_wall_time_s"] = round(wall_elapsed_s, 3)
    summary["processing_speed_fps"] = round(processing_fps, 2) if processing_fps else None

    if squared_errors:
        rmse = (sum(squared_errors) / len(squared_errors)) ** 0.5
        summary["centroid_rmse_vs_truth_px"] = round(rmse, 2)
        summary["truth_frames_compared"] = len(squared_errors)

    if save_outputs and rows:
        reporting.export_all(rows, prefix=output_prefix)

    return summary
