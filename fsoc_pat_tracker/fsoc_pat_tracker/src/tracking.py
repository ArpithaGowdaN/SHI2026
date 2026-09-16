"""
tracking.py — Owner: EC
Preprocesses each frame, detects the beacon target, computes its centroid,
rejects false detections, and scores confidence. Built from scratch to
match the TrackResult contract in interfaces.py.
"""

import cv2
import numpy as np

from interfaces import FramePacket, TrackResult
from config import TARGET_SIZE_MIN_PX, TARGET_SIZE_MAX_PX

# Reject blobs way outside the expected target size range (rules out
# large noise clumps or a nearly-all-white frame being read as "the target")
MIN_BLOB_AREA_PX = (TARGET_SIZE_MIN_PX ** 2) * 0.3
MAX_BLOB_AREA_PX = (TARGET_SIZE_MAX_PX ** 2) * 20


def preprocess(frame: np.ndarray) -> np.ndarray:
    """
    Denoise the frame before thresholding. Median blur handles salt-and-
    pepper noise well without smearing the beacon's sharp edges as much
    as a Gaussian blur would.
    """
    if frame.ndim == 3:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.medianBlur(frame, 5)


def detect_beacon(frame: np.ndarray) -> TrackResult:
    """
    Threshold + connected-components blob detection + centroid via image
    moments + confidence scoring + false-positive rejection by blob size.
    """
    # Otsu's method auto-picks the threshold, so it adapts to changing
    # brightness (haze/low-light disturbances) instead of using one fixed
    # cutoff for every frame.
    _, binary = cv2.threshold(frame, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphological opening (erode then dilate) strips out small noise
    # specks that survive thresholding, without shrinking the real beacon
    # blob much, since it's larger than the noise-speck kernel.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

    if num_labels <= 1:
        # label 0 is always the background; nothing else found
        return TrackResult(frame_id=-1, detected=False, centroid_px=None, confidence=0.0)

    # Consider every blob except the background (label 0), keep only ones
    # that are a plausible beacon size, and pick the best-scoring one.
    best_label = None
    best_score = -1.0
    for label in range(1, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        if area < MIN_BLOB_AREA_PX or area > MAX_BLOB_AREA_PX:
            continue  # too small (noise speck) or too large (not a beacon)

        # Score by how compact/square the blob is (a real beacon square
        # has width ~= height; noise blobs are often irregular strips)
        w = stats[label, cv2.CC_STAT_WIDTH]
        h = stats[label, cv2.CC_STAT_HEIGHT]
        aspect_penalty = abs(w - h) / max(w, h, 1)
        score = area * (1.0 - min(aspect_penalty, 1.0))

        if score > best_score:
            best_score = score
            best_label = label

    if best_label is None:
        return TrackResult(frame_id=-1, detected=False, centroid_px=None, confidence=0.0)

    cx, cy = centroids[best_label]
    area = stats[best_label, cv2.CC_STAT_AREA]

    # Confidence: 1.0 for a clean, well-sized, square blob; degrades
    # smoothly for odd aspect ratios or sizes near the reject boundary.
    w = stats[best_label, cv2.CC_STAT_WIDTH]
    h = stats[best_label, cv2.CC_STAT_HEIGHT]
    aspect_score = 1.0 - min(abs(w - h) / max(w, h, 1), 1.0)
    size_mid = (MIN_BLOB_AREA_PX + MAX_BLOB_AREA_PX) / 2
    size_score = 1.0 - min(abs(area - size_mid) / size_mid, 1.0)
    confidence = max(0.0, min(1.0, 0.6 * aspect_score + 0.4 * size_score))

    return TrackResult(
        frame_id=-1,  # filled in by process_frame from the packet
        detected=True,
        centroid_px=(float(cx), float(cy)),
        confidence=confidence,
        blob_area_px=float(area),
    )


def process_frame(packet: FramePacket) -> TrackResult:
    """Entry point: takes a FramePacket, returns a TrackResult."""
    pre = preprocess(packet.image)
    result = detect_beacon(pre)
    result.frame_id = packet.frame_id
    return result
