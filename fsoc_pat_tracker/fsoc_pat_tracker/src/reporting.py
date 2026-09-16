"""
reporting.py — Owner: CS
Per-frame telemetry logging, CSV/JSON/Excel export, the PS-required
automatic performance log (simulation duration, FPS, acquisition time,
avg/max tracking error, lock retention rate, target loss %, reacquisition
time, processing speed), and the four required performance plots:
    1. Pointing error vs frame
    2. Camera angle vs frame
    3. Reacquisition time (per event)
    4. Control command vs frame

Built from scratch. Consumes the per-frame outputs of every other module
(TrackResult, PredictionResult, ControlCommand, AngleData) without
requiring any change to interfaces.py — it builds its own internal
superset log row (FrameLog) purely for logging/plotting purposes, since
interfaces.py is a shared file only CS should touch after team agreement.

Usage (from app.py):
    logger = PerformanceLogger()
    for frame in run:
        ...
        logger.log_frame(track, prediction, command, angle=angle_data, fps=current_fps)
    report = generate_report(logger, run_name="demo_run")

Dependencies: matplotlib (plots), openpyxl (xlsx export).
    pip install matplotlib openpyxl
"""

import os
import csv
import json
import math
import time
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import (
    OUTPUT_DIR, EXPORT_FORMATS, CAMERA_UPDATE_RATE_HZ,
    CAMERA_RES_WIDTH_PX, CAMERA_RES_HEIGHT_PX,
    ACQUISITION_TIME_MAX_S, TRACKING_ERROR_MAX_PX, TARGET_LOSS_MAX_PCT,
    REACQUISITION_TIME_MAX_S, PROCESSING_SPEED_MIN_FPS,
)
from interfaces import TrackResult, PredictionResult, ControlCommand, AngleData

FRAME_CENTER_PX = (CAMERA_RES_WIDTH_PX / 2, CAMERA_RES_HEIGHT_PX / 2)

TRACKED_STATES = ("TRACK", "HANDOVER_READY")
REACQUIRING_STATES = ("LOST", "REACQUIRE")


# ---------------------------------------------------------------------------
# Internal per-frame log row (superset of interfaces.TelemetryRow, kept
# local to reporting.py so the shared contract file stays untouched)
# ---------------------------------------------------------------------------
@dataclass
class FrameLog:
    frame_id: int
    timestamp_s: float
    detected: bool
    confidence: float
    tracking_error_px: Optional[float]
    angular_error_deg: Optional[float]
    pan_angle_deg: Optional[float]
    tilt_angle_deg: Optional[float]
    target_azimuth_deg: Optional[float]
    target_elevation_deg: Optional[float]
    range_estimate_m: Optional[float]
    pan_delta_deg: float
    tilt_delta_deg: float
    saturated: bool
    pat_state: str
    fps: Optional[float] = None


class PerformanceLogger:
    """Accumulates one FrameLog per frame across a run."""

    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.output_dir = output_dir
        self.rows: List[FrameLog] = []

    def reset(self):
        self.rows = []

    def log_frame(
        self,
        track: TrackResult,
        prediction: PredictionResult,
        command: ControlCommand,
        angle: Optional[AngleData] = None,
        timestamp_s: Optional[float] = None,
        fps: Optional[float] = None,
    ) -> FrameLog:
        """Call once per frame with that frame's outputs from every module."""
        dx = prediction.predicted_centroid_px[0] - FRAME_CENTER_PX[0]
        dy = prediction.predicted_centroid_px[1] - FRAME_CENTER_PX[1]
        tracking_error_px = math.hypot(dx, dy)

        row = FrameLog(
            frame_id=track.frame_id,
            timestamp_s=timestamp_s if timestamp_s is not None else track.frame_id / CAMERA_UPDATE_RATE_HZ,
            detected=track.detected,
            confidence=track.confidence,
            tracking_error_px=tracking_error_px,
            angular_error_deg=angle.angular_error_deg if angle else None,
            pan_angle_deg=angle.pan_angle_deg if angle else None,
            tilt_angle_deg=angle.tilt_angle_deg if angle else None,
            target_azimuth_deg=angle.target_azimuth_deg if angle else None,
            target_elevation_deg=angle.target_elevation_deg if angle else None,
            range_estimate_m=angle.range_estimate_m if angle else None,
            pan_delta_deg=command.pan_delta_deg,
            tilt_delta_deg=command.tilt_delta_deg,
            saturated=command.saturated,
            pat_state=command.pat_state,
            fps=fps,
        )
        self.rows.append(row)
        return row


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------
def compute_acquisition_time_s(rows: List[FrameLog]) -> Optional[float]:
    """Time from run start to the first frame reaching TRACK."""
    if not rows:
        return None
    for r in rows:
        if r.pat_state == "TRACK":
            return r.timestamp_s - rows[0].timestamp_s
    return None


def compute_reacquisition_times_s(rows: List[FrameLog]) -> List[float]:
    """Duration of every LOST/REACQUIRE run that is later recovered."""
    times = []
    reacquire_start = None
    for r in rows:
        if r.pat_state in REACQUIRING_STATES:
            if reacquire_start is None:
                reacquire_start = r.timestamp_s
        else:
            if reacquire_start is not None:
                times.append(r.timestamp_s - reacquire_start)
                reacquire_start = None
    return times


def compute_summary(rows: List[FrameLog]) -> Dict:
    """PS-required automatic performance log."""
    if not rows:
        return {}

    n = len(rows)
    duration_s = rows[-1].timestamp_s - rows[0].timestamp_s

    detected_count = sum(1 for r in rows if r.detected)
    target_loss_pct = 100.0 * (1 - detected_count / n)

    errors = [r.tracking_error_px for r in rows if r.tracking_error_px is not None]
    avg_error = sum(errors) / len(errors) if errors else None
    max_error = max(errors) if errors else None

    track_frames = sum(1 for r in rows if r.pat_state in TRACKED_STATES)
    lock_retention_pct = 100.0 * track_frames / n

    acquisition_time_s = compute_acquisition_time_s(rows)

    reacq_times = compute_reacquisition_times_s(rows)
    avg_reacq_s = sum(reacq_times) / len(reacq_times) if reacq_times else None
    max_reacq_s = max(reacq_times) if reacq_times else None

    fps_values = [r.fps for r in rows if r.fps is not None]
    avg_fps = sum(fps_values) / len(fps_values) if fps_values else (n / duration_s if duration_s > 0 else None)

    pat_state_counts: Dict[str, int] = {}
    for r in rows:
        pat_state_counts[r.pat_state] = pat_state_counts.get(r.pat_state, 0) + 1

    return {
        "total_frames": n,
        "simulation_duration_s": round(duration_s, 3),
        "avg_fps": round(avg_fps, 2) if avg_fps is not None else None,
        "acquisition_time_s": round(acquisition_time_s, 3) if acquisition_time_s is not None else None,
        "avg_tracking_error_px": round(avg_error, 3) if avg_error is not None else None,
        "max_tracking_error_px": round(max_error, 3) if max_error is not None else None,
        "target_loss_pct": round(target_loss_pct, 2),
        "lock_retention_pct": round(lock_retention_pct, 2),
        "reacquisition_events": len(reacq_times),
        "avg_reacquisition_time_s": round(avg_reacq_s, 3) if avg_reacq_s is not None else None,
        "max_reacquisition_time_s": round(max_reacq_s, 3) if max_reacq_s is not None else None,
        "pat_state_frame_counts": pat_state_counts,
        "spec_compliance": {
            "acquisition_time_ok": acquisition_time_s is not None and acquisition_time_s <= ACQUISITION_TIME_MAX_S,
            "tracking_error_ok": max_error is not None and max_error <= TRACKING_ERROR_MAX_PX,
            "target_loss_ok": target_loss_pct < TARGET_LOSS_MAX_PCT,
            "reacquisition_time_ok": max_reacq_s is None or max_reacq_s <= REACQUISITION_TIME_MAX_S,
            "fps_ok": avg_fps is None or avg_fps >= PROCESSING_SPEED_MIN_FPS,
        },
    }


# ---------------------------------------------------------------------------
# Export: CSV / JSON / Excel
# ---------------------------------------------------------------------------
def export_csv(rows: List[FrameLog], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(asdict(r))


def export_json(rows: List[FrameLog], summary: Dict, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"summary": summary, "frames": [asdict(r) for r in rows]}, f, indent=2)


def export_xlsx(rows: List[FrameLog], summary: Dict, path: str):
    from openpyxl import Workbook

    os.makedirs(os.path.dirname(path), exist_ok=True)
    wb = Workbook()

    ws_frames = wb.active
    ws_frames.title = "Frames"
    if rows:
        headers = list(asdict(rows[0]).keys())
        ws_frames.append(headers)
        for r in rows:
            ws_frames.append(list(asdict(r).values()))

    ws_summary = wb.create_sheet("Summary")
    ws_summary.append(["Metric", "Value"])
    for k, v in summary.items():
        ws_summary.append([k, json.dumps(v) if isinstance(v, dict) else v])

    wb.save(path)


# ---------------------------------------------------------------------------
# The four required performance plots
# ---------------------------------------------------------------------------
def plot_pointing_error(rows: List[FrameLog], path: str):
    frames = [r.frame_id for r in rows]
    errors_px = [r.tracking_error_px or 0 for r in rows]

    fig, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(frames, errors_px, color="tab:blue", label="Tracking error (px)")
    ax1.axhline(TRACKING_ERROR_MAX_PX, color="tab:blue", linestyle="--", alpha=0.5,
                label=f"Spec max ({TRACKING_ERROR_MAX_PX}px)")
    ax1.set_xlabel("Frame")
    ax1.set_ylabel("Tracking error (px)", color="tab:blue")
    ax1.grid(True, alpha=0.3)

    if any(r.angular_error_deg is not None for r in rows):
        ang = [r.angular_error_deg or 0 for r in rows]
        ax2 = ax1.twinx()
        ax2.plot(frames, ang, color="tab:orange", alpha=0.6, label="Angular error (deg)")
        ax2.set_ylabel("Angular error (deg)", color="tab:orange")

    fig.legend(loc="upper right")
    plt.title("Pointing Error vs Frame")
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close(fig)


def plot_camera_angle(rows: List[FrameLog], path: str):
    frames = [r.frame_id for r in rows]
    pan = [r.pan_angle_deg for r in rows]
    tilt = [r.tilt_angle_deg for r in rows]

    plt.figure(figsize=(10, 4))
    plt.plot(frames, pan, label="Pan angle (deg)")
    plt.plot(frames, tilt, label="Tilt angle (deg)")
    plt.xlabel("Frame")
    plt.ylabel("Angle (deg)")
    plt.title("Camera Angle vs Frame")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def plot_reacquisition_times(rows: List[FrameLog], path: str):
    times = compute_reacquisition_times_s(rows)

    plt.figure(figsize=(8, 4))
    if times:
        plt.bar(range(1, len(times) + 1), times, color="tab:red")
        plt.axhline(REACQUISITION_TIME_MAX_S, color="black", linestyle="--",
                    label=f"Spec max ({REACQUISITION_TIME_MAX_S}s)")
        plt.legend()
    else:
        plt.text(0.5, 0.5, "No reacquisition events", ha="center", va="center")
    plt.xlabel("Reacquisition event #")
    plt.ylabel("Reacquisition time (s)")
    plt.title("Reacquisition Time per Event")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def plot_control_command(rows: List[FrameLog], path: str):
    frames = [r.frame_id for r in rows]
    pan_delta = [r.pan_delta_deg for r in rows]
    tilt_delta = [r.tilt_delta_deg for r in rows]

    plt.figure(figsize=(10, 4))
    plt.plot(frames, pan_delta, label="Pan delta (deg/frame)")
    plt.plot(frames, tilt_delta, label="Tilt delta (deg/frame)")
    sat_frames = [r.frame_id for r in rows if r.saturated]
    if sat_frames:
        plt.scatter(sat_frames, [0] * len(sat_frames), color="red", marker="x",
                    s=15, label="Speed-saturated", zorder=5)
    plt.xlabel("Frame")
    plt.ylabel("Commanded delta (deg)")
    plt.title("Control Command vs Frame")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------
def generate_report(
    logger: PerformanceLogger,
    run_name: Optional[str] = None,
    formats: Optional[List[str]] = None,
) -> Dict:
    """
    Call once at the end of a run. Writes CSV/JSON/Excel logs to
    outputs/logs/ and all four plots to outputs/plots/, and returns the
    summary dict plus every file path written.
    """
    if not logger.rows:
        raise ValueError("No frames logged — call logger.log_frame() during the run first.")

    formats = formats or EXPORT_FORMATS
    run_name = run_name or time.strftime("run_%Y%m%d_%H%M%S")

    logs_dir = os.path.join(logger.output_dir, "logs")
    plots_dir = os.path.join(logger.output_dir, "plots")
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)

    summary = compute_summary(logger.rows)

    export_paths = {}
    if "csv" in formats:
        p = os.path.join(logs_dir, f"{run_name}.csv")
        export_csv(logger.rows, p)
        export_paths["csv"] = p
    if "json" in formats:
        p = os.path.join(logs_dir, f"{run_name}.json")
        export_json(logger.rows, summary, p)
        export_paths["json"] = p
    if "xlsx" in formats:
        p = os.path.join(logs_dir, f"{run_name}.xlsx")
        export_xlsx(logger.rows, summary, p)
        export_paths["xlsx"] = p

    plot_paths = {}
    plot_paths["pointing_error"] = os.path.join(plots_dir, f"{run_name}_pointing_error.png")
    plot_pointing_error(logger.rows, plot_paths["pointing_error"])

    plot_paths["camera_angle"] = os.path.join(plots_dir, f"{run_name}_camera_angle.png")
    plot_camera_angle(logger.rows, plot_paths["camera_angle"])

    plot_paths["reacquisition_time"] = os.path.join(plots_dir, f"{run_name}_reacquisition_time.png")
    plot_reacquisition_times(logger.rows, plot_paths["reacquisition_time"])

    plot_paths["control_command"] = os.path.join(plots_dir, f"{run_name}_control_command.png")
    plot_control_command(logger.rows, plot_paths["control_command"])

    return {"summary": summary, "export_paths": export_paths, "plot_paths": plot_paths}
