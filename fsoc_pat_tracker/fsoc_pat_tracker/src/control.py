"""
control.py — Owner: Electrical B
PTZ motion commands: PID/PD control, saturation, dead-zone, feedforward,
reacquisition search, PAT state machine (SEARCH/ACQUIRE/TRACK/LOST/
REACQUIRE/HANDOVER_READY).

STATUS: NOT YET BUILT by Electrical B. Arpitha's Layer 5 (layer5_controller.py)
already has a working PID controller plus an expanding-spiral SearchPattern
(added after Layer 1 circular trajectories were found to start beyond the
camera's initial view). Tested closed-loop: 0.73s acquisition (spec: <=2s),
~50-65px settled pointing error, 93% lock retention over a 10s run. Hand that
over as the starting point.
"""

from config import MAX_PAN_SPEED_DEG_S, MAX_TILT_SPEED_DEG_S, PID_KP, PID_KI, PID_KD, LOST_THRESHOLD_FRAMES
from interfaces import PredictionResult, ControlCommand


def compute_command(frame_id: int, prediction: PredictionResult, pid_state) -> ControlCommand:
    """TODO: port from Arpitha's PID controller in layer5_controller.py.
    Must clamp to MAX_PAN_SPEED_DEG_S / MAX_TILT_SPEED_DEG_S and set
    ControlCommand.saturated=True when clamped."""
    raise NotImplementedError


def run_search_pattern(frame_id: int, search_state) -> ControlCommand:
    """TODO: port expanding-spiral SearchPattern from layer5_controller.py."""
    raise NotImplementedError


def update_pat_state(current_state: str, track_valid: bool, lost_frame_count: int) -> str:
    """TODO: state machine transitions between SEARCH/ACQUIRE/TRACK/LOST/
    REACQUIRE/HANDOVER_READY, using LOST_THRESHOLD_FRAMES."""
    raise NotImplementedError
