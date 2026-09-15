"""
tracking.py — Owner: EC
Preprocess frame, detect beacon, compute centroid, reject false detections,
compute confidence, handle disturbance robustness.

STATUS: NOT YET BUILT by EC. Arpitha's Layer 4 (layer4_tracker.py) already has
a working BlobDetector (Otsu thresholding + image-moment centroiding, with a
max-area sanity check to reject false all-blob frames) — hand that to EC as a
reference starting point rather than building from zero.
"""

from interfaces import FramePacket, TrackResult


def preprocess(frame: "np.ndarray") -> "np.ndarray":
    """TODO: denoise/filter (adaptive per disturbance type)."""
    raise NotImplementedError


def detect_beacon(frame: "np.ndarray") -> TrackResult:
    """TODO: threshold + blob detect + centroid + confidence score.
    Reference: Arpitha's BlobDetector class in layer4_tracker.py."""
    raise NotImplementedError


def process_frame(packet: FramePacket) -> TrackResult:
    pre = preprocess(packet.image)
    return detect_beacon(pre)
