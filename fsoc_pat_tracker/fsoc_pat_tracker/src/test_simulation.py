"""
test_simulation.py — quick local test for simulation.py
Run this from inside your src/ folder: python test_simulation.py

It doesn't use a testing framework (no pytest needed) — it just runs the
functions, prints pass/fail for each check, and saves a few sample frames
as .png images so you can SEE the camera view and world view with your
own eyes, not just trust printed numbers.
"""

import os
import cv2
from simulation import build_targets, get_next_frame, generate_world_frame

OUT_DIR = "test_output"
os.makedirs(OUT_DIR, exist_ok=True)


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")


# ---------------------------------------------------------------------------
# Test 1: every motion type runs without crashing and produces a 640x480 frame
# ---------------------------------------------------------------------------
print("\n--- Test 1: motion types ---")
for motion in ["straight_line", "circular", "figure_8", "random", "spiral", "sinusoidal"]:
    targets = build_targets(motion_type=motion, num_targets=1, seed=42)
    pkt = None
    for f in range(30):  # run 1 second worth of frames at 30fps
        targets[0].step(dt=1 / 30)
        pkt = get_next_frame("simulation", frame_id=f, timestamp_s=f / 30,
                              camera_center_xy=(1000, 1000), targets=targets)
    check(f"{motion}: produced a frame", pkt is not None)
    check(f"{motion}: frame is 640x480", pkt.image.shape == (480, 640))

    # save one sample frame per motion type so you can look at it
    cv2.imwrite(os.path.join(OUT_DIR, f"sample_{motion}.png"), pkt.image)

# ---------------------------------------------------------------------------
# Test 2: multi-target mode
# ---------------------------------------------------------------------------
print("\n--- Test 2: multi-target ---")
targets = build_targets(motion_type="random", num_targets=3, seed=1)
pkt = get_next_frame("simulation", 0, 0.0, (1000, 1000), targets=targets)
check("3 targets created", len(targets) == 3)
check("frame still 640x480 with multiple targets", pkt.image.shape == (480, 640))
cv2.imwrite(os.path.join(OUT_DIR, "sample_multi_target.png"), pkt.image)

# ---------------------------------------------------------------------------
# Test 3: camera crop clamps at world edges (shouldn't crash or shrink)
# ---------------------------------------------------------------------------
print("\n--- Test 3: edge clamping ---")
targets = build_targets(motion_type="random", num_targets=1, seed=1)
pkt_corner = get_next_frame("simulation", 0, 0.0, (10, 10), targets=targets)
check("corner crop still 640x480 (didn't crash/shrink)", pkt_corner.image.shape == (480, 640))
cv2.imwrite(os.path.join(OUT_DIR, "sample_corner_crop.png"), pkt_corner.image)

# ---------------------------------------------------------------------------
# Test 4: visually confirm camera tracking a moving target actually keeps
# it centered vs a static camera losing it
# ---------------------------------------------------------------------------
print("\n--- Test 4: tracking vs static camera (visual) ---")
targets = build_targets(motion_type="circular", num_targets=1, seed=5)
for f in range(60):
    targets[0].step(dt=1 / 30)

# perfect tracking: camera follows the target exactly
pkt_tracking = get_next_frame("simulation", 60, 2.0, targets[0].position, targets=targets)
cv2.imwrite(os.path.join(OUT_DIR, "tracking_camera_centered.png"), pkt_tracking.image)

# static camera: stayed at world center the whole time
pkt_static = get_next_frame("simulation", 60, 2.0, (1000, 1000), targets=targets)
cv2.imwrite(os.path.join(OUT_DIR, "static_camera_may_have_lost_target.png"), pkt_static.image)

print(f"\nDone. Open the '{OUT_DIR}' folder and look at the .png files:")
print("  - sample_<motion>.png x6  -> one frame per trajectory type")
print("  - sample_multi_target.png -> 3 targets visible in one frame")
print("  - sample_corner_crop.png  -> camera pushed to world edge, still valid size")
print("  - tracking_camera_centered.png            -> target should be near frame CENTER")
print("  - static_camera_may_have_lost_target.png  -> target may be OFF to one side or missing")
