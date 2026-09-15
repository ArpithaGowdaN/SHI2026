"""
benchmark.py — Owner: CS (Arpitha)
Load external .mp4 + optional truth CSV, run benchmark mode, compute metrics
against the PS's Benchmark Performance-2 evaluation stage (30% of marks).

STATUS: NOT YET BUILT. This is the ISRO-provided-video bypass path — the
system must generalize to arbitrary noisy .mp4 files handed out on the day,
not just synthetic Layer 1 output. simulation.py's video mode already reads
.mp4 via cv2.VideoCapture; this file drives that mode end-to-end and scores it.
"""

from interfaces import TelemetryRow


def load_truth_csv(path: str):
    """TODO: optional ground-truth centroid CSV for scoring, if provided."""
    raise NotImplementedError


def run_benchmark(video_path: str, truth_csv_path: str = None) -> dict:
    """TODO: run full pipeline (simulation.video_mode -> tracking -> predictor
    -> control -> analytics) over the video, compute RMSE, acquisition time,
    re-acquisition time, lock retention rate, FPS vs the PS's numeric targets
    in config.py, and return a metrics dict."""
    raise NotImplementedError
