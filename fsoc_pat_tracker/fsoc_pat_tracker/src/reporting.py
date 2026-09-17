"""
reporting.py — Owner: CS (Arpitha)
CSV / JSON / Excel export of per-frame telemetry, a JSON performance
summary matching the PS's required Performance Log fields (simulation
duration, FPS, acquisition time, avg/max tracking error, lock retention
rate, reacquisition timing), and the four required plots: pointing error
vs frame, camera angle vs frame, reacquisition timing, control command
vs frame. Built from scratch to match the TelemetryRow contract in
interfaces.py.
"""

import os
import json
import csv as csv_module

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless-safe backend, no GUI window required
import matplotlib.pyplot as plt

from config import OUTPUT_DIR
from interfaces import TelemetryRow


def _ensure_dir(path: str):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def rows_to_dataframe(rows: list) -> pd.DataFrame:
    """Convert a list of TelemetryRow into a flat pandas DataFrame."""
    return pd.DataFrame([vars(r) for r in rows])


def export_csv(rows: list, filename: str):
    _ensure_dir(filename)
    df = rows_to_dataframe(rows)
    df.to_csv(filename, index=False)
    return filename


def export_excel(rows: list, filename: str):
    _ensure_dir(filename)
    df = rows_to_dataframe(rows)
    df.to_excel(filename, index=False, sheet_name="telemetry")
    return filename


def compute_summary(rows: list) -> dict:
    """
    Aggregate metrics matching the PS's Performance Log requirements:
    simulation duration, FPS, acquisition time, avg/max tracking error,
    lock retention rate, reacquisition timing, processing time.
    """
    if not rows:
        return {}

    df = rows_to_dataframe(rows)
    duration_s = df["timestamp_s"].iloc[-1] - df["timestamp_s"].iloc[0]
    total_frames = len(df)

    fps_values = df["fps"].dropna()
    avg_fps = float(fps_values.mean()) if len(fps_values) else None

    # acquisition time: first frame that reaches TRACK
    track_rows = df[df["pat_state"] == "TRACK"]
    acquisition_time_s = None
    if len(track_rows):
        acquisition_time_s = float(track_rows["timestamp_s"].iloc[0] - df["timestamp_s"].iloc[0])

    err = df["tracking_error_px"].dropna()
    avg_tracking_error_px = float(err.mean()) if len(err) else None
    max_tracking_error_px = float(err.max()) if len(err) else None

    # lock retention: fraction of frames in TRACK (once tracking has
    # started at least once) that stayed detected/on-target
    detected_frames = int(df["detected"].sum())
    lock_retention_rate = detected_frames / total_frames if total_frames else None

    # reacquisition episodes: each contiguous run of REACQUIRE, timed
    # from its start to the next ACQUIRE/TRACK frame
    reacquisition_durations_s = []
    in_reacq = False
    reacq_start_t = None
    for _, row in df.iterrows():
        if row["pat_state"] == "REACQUIRE" and not in_reacq:
            in_reacq = True
            reacq_start_t = row["timestamp_s"]
        elif row["pat_state"] in ("ACQUIRE", "TRACK") and in_reacq:
            in_reacq = False
            reacquisition_durations_s.append(row["timestamp_s"] - reacq_start_t)
    avg_reacquisition_time_s = (
        sum(reacquisition_durations_s) / len(reacquisition_durations_s)
        if reacquisition_durations_s else None
    )

    return {
        "total_frames": total_frames,
        "simulation_duration_s": round(duration_s, 3),
        "average_fps": round(avg_fps, 2) if avg_fps is not None else None,
        "acquisition_time_s": round(acquisition_time_s, 3) if acquisition_time_s is not None else None,
        "average_tracking_error_px": round(avg_tracking_error_px, 2) if avg_tracking_error_px is not None else None,
        "max_tracking_error_px": round(max_tracking_error_px, 2) if max_tracking_error_px is not None else None,
        "lock_retention_rate": round(lock_retention_rate, 4) if lock_retention_rate is not None else None,
        "reacquisition_count": len(reacquisition_durations_s),
        "average_reacquisition_time_s": round(avg_reacquisition_time_s, 3) if avg_reacquisition_time_s is not None else None,
    }


def export_json_summary(rows: list, filename: str):
    _ensure_dir(filename)
    summary = compute_summary(rows)
    with open(filename, "w") as f:
        json.dump(summary, f, indent=2)
    return filename


# ---------------------------------------------------------------------------
# The four required plots
# ---------------------------------------------------------------------------

def plot_pointing_error(rows: list, filename: str):
    df = rows_to_dataframe(rows)
    _ensure_dir(filename)
    plt.figure(figsize=(8, 4))
    plt.plot(df["frame_id"], df["tracking_error_px"], linewidth=1)
    plt.xlabel("Frame")
    plt.ylabel("Pointing / Tracking Error (px)")
    plt.title("Pointing Error vs Frame")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    return filename


def plot_camera_angle(rows: list, filename: str):
    df = rows_to_dataframe(rows)
    _ensure_dir(filename)
    plt.figure(figsize=(8, 4))
    plt.plot(df["frame_id"], df["pan_angle_deg"], label="Pan", linewidth=1)
    plt.plot(df["frame_id"], df["tilt_angle_deg"], label="Tilt", linewidth=1)
    plt.xlabel("Frame")
    plt.ylabel("Camera Angle (deg)")
    plt.title("Camera Angle vs Frame")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    return filename


def plot_reacquisition_timing(rows: list, filename: str):
    """Bar chart of each REACQUIRE episode's duration."""
    df = rows_to_dataframe(rows)
    _ensure_dir(filename)

    durations = []
    in_reacq = False
    start_t = None
    for _, row in df.iterrows():
        if row["pat_state"] == "REACQUIRE" and not in_reacq:
            in_reacq = True
            start_t = row["timestamp_s"]
        elif row["pat_state"] in ("ACQUIRE", "TRACK") and in_reacq:
            in_reacq = False
            durations.append(row["timestamp_s"] - start_t)

    plt.figure(figsize=(8, 4))
    if durations:
        plt.bar(range(1, len(durations) + 1), durations)
        plt.xlabel("Reacquisition Episode #")
        plt.ylabel("Duration (s)")
    else:
        plt.text(0.5, 0.5, "No reacquisition episodes recorded", ha="center", va="center")
    plt.title("Reacquisition Timing")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    return filename


def plot_control_command(rows: list, filename: str):
    """Uses pan_angle_deg / tilt_angle_deg frame-to-frame delta as a
    proxy for the commanded motion, since TelemetryRow logs absolute
    angle, not the raw ControlCommand deltas."""
    df = rows_to_dataframe(rows)
    _ensure_dir(filename)
    pan_delta = df["pan_angle_deg"].diff().fillna(0)
    tilt_delta = df["tilt_angle_deg"].diff().fillna(0)

    plt.figure(figsize=(8, 4))
    plt.plot(df["frame_id"], pan_delta, label="Pan command (deg/frame)", linewidth=1)
    plt.plot(df["frame_id"], tilt_delta, label="Tilt command (deg/frame)", linewidth=1)
    plt.xlabel("Frame")
    plt.ylabel("Commanded Angle Change (deg)")
    plt.title("Control Command vs Frame")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    return filename


def export_all(rows: list, output_dir: str = OUTPUT_DIR, prefix: str = "run"):
    """Convenience: writes CSV, Excel, JSON summary, and all 4 plots in
    one call, under outputs/logs/ and outputs/plots/ as the project
    folder structure expects."""
    logs_dir = os.path.join(output_dir, "logs")
    plots_dir = os.path.join(output_dir, "plots")

    paths = {
        "csv": export_csv(rows, os.path.join(logs_dir, f"{prefix}_telemetry.csv")),
        "excel": export_excel(rows, os.path.join(logs_dir, f"{prefix}_telemetry.xlsx")),
        "json_summary": export_json_summary(rows, os.path.join(logs_dir, f"{prefix}_summary.json")),
        "plot_pointing_error": plot_pointing_error(rows, os.path.join(plots_dir, f"{prefix}_pointing_error.png")),
        "plot_camera_angle": plot_camera_angle(rows, os.path.join(plots_dir, f"{prefix}_camera_angle.png")),
        "plot_reacquisition": plot_reacquisition_timing(rows, os.path.join(plots_dir, f"{prefix}_reacquisition.png")),
        "plot_control_command": plot_control_command(rows, os.path.join(plots_dir, f"{prefix}_control_command.png")),
    }
    return paths
