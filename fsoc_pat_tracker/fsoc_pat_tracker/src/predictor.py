"""
predictor.py — Owner: Electrical B
Kalman/EKF prediction, velocity estimation, missing-frame estimation.

STATUS: NOT YET BUILT by Electrical B. Arpitha's Layer 4 (layer4_tracker.py)
already has a working TrackerKF (constant-velocity Kalman filter) tested with
0.40px RMSE in normal tracking and ~79px RMSE holding through a 1.5s simulated
blackout (vs 157px for naive hold-last-position). Hand that over as the
starting point; upgrading it to a full nonlinear EKF is this role's add-on.
"""

from interfaces import TrackResult, PredictionResult


def predict(frame_id: int, track: TrackResult, kf_state) -> PredictionResult:
    """TODO: port from Arpitha's TrackerKF. Update on detection, predict-only
    on missed frames (is_prediction_only=True)."""
    raise NotImplementedError
