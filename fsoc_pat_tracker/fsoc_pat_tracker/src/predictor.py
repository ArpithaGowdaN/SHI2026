"""
predictor.py — Owner: Electrical B
Kalman filter prediction: tracks target position + velocity in pixel
space, updates on real detections, and keeps predicting through frames
where tracking.py reports no detection (blackout / occlusion / noise
dropout). Built from scratch to match the PredictionResult contract in
interfaces.py.

Uses a constant-velocity linear Kalman filter (4-state: x, y, vx, vy).
This is the right model for this PS: even the "circular"/"figure_8"/
"spiral" target motions are locally well-approximated by constant
velocity over the short prediction gaps (missed-frame runs) this filter
actually has to bridge — a full nonlinear EKF only pays off if the
process model itself is nonlinear, which isn't needed here.
"""

import numpy as np
import cv2

from interfaces import TrackResult, PredictionResult


class TrackerKF:
    """Wraps cv2.KalmanFilter with a constant-velocity model."""

    def __init__(self, dt: float = 1 / 30, process_noise: float = 5.0,
                 measurement_noise: float = 2.0):
        self.kf = cv2.KalmanFilter(4, 2)  # state: [x, y, vx, vy], measurement: [x, y]

        self.kf.transitionMatrix = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ], dtype=np.float32)

        self.kf.measurementMatrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
        ], dtype=np.float32)

        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * process_noise
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * measurement_noise
        # Start with high uncertainty so early measurements are trusted
        # strongly and velocity converges quickly, rather than the filter
        # assuming it already knows the state.
        self.kf.errorCovPost = np.eye(4, dtype=np.float32) * 500.0

        self.initialized = False

    def init_state(self, x: float, y: float):
        self.kf.statePost = np.array([[x], [y], [0], [0]], dtype=np.float32)
        self.initialized = True

    def predict(self) -> tuple:
        """Advance the filter one step, return (x, y, vx, vy) prediction."""
        pred = self.kf.predict().flatten()
        return float(pred[0]), float(pred[1]), float(pred[2]), float(pred[3])

    def correct(self, x: float, y: float) -> tuple:
        """Feed in a real measurement, return the corrected (x, y, vx, vy)."""
        measurement = np.array([[x], [y]], dtype=np.float32)
        corrected = self.kf.correct(measurement).flatten()
        return float(corrected[0]), float(corrected[1]), float(corrected[2]), float(corrected[3])


# One filter instance persists across frames — created lazily on first call.
_kf = None


def reset():
    """Call this at the start of a new tracking session (e.g. after RE-ACQUIRE)."""
    global _kf
    _kf = None


def predict(frame_id: int, track: TrackResult, dt: float = 1 / 30) -> PredictionResult:
    """
    Main entry point: call once per frame with that frame's TrackResult.
    Handles both cases:
      - track.detected == True  -> predict then correct with the measurement
      - track.detected == False -> predict only, holding through the gap
    """
    global _kf

    if track.detected and not (_kf and _kf.initialized):
        # first-ever detection: initialize the filter here rather than
        # predicting from an undefined state
        _kf = TrackerKF(dt=dt)
        _kf.init_state(*track.centroid_px)
        return PredictionResult(
            frame_id=frame_id,
            predicted_centroid_px=track.centroid_px,
            predicted_velocity_px_s=(0.0, 0.0),
            is_prediction_only=False,
        )

    if _kf is None or not _kf.initialized:
        # nothing detected yet at all — no state to predict from
        return PredictionResult(
            frame_id=frame_id,
            predicted_centroid_px=(0.0, 0.0),
            predicted_velocity_px_s=(0.0, 0.0),
            is_prediction_only=True,
        )

    x, y, vx, vy = _kf.predict()

    if track.detected:
        x, y, vx, vy = _kf.correct(*track.centroid_px)
        return PredictionResult(
            frame_id=frame_id,
            predicted_centroid_px=(x, y),
            predicted_velocity_px_s=(vx, vy),
            is_prediction_only=False,
        )
    else:
        return PredictionResult(
            frame_id=frame_id,
            predicted_centroid_px=(x, y),
            predicted_velocity_px_s=(vx, vy),
            is_prediction_only=True,
        )
