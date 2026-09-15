"""
config.py — Shared parameter file (owner: CS, per Task Distribution doc)
All tunable values MUST come from here. Nobody hardcodes values elsewhere.

Values below default to the official ISRO PS 26169 spec sheet.
"""

# ---------------------------------------------------------------------------
# World / Scene
# ---------------------------------------------------------------------------
WORLD_WIDTH_PX = 2000
WORLD_HEIGHT_PX = 2000

# ---------------------------------------------------------------------------
# Camera / Viewport
# ---------------------------------------------------------------------------
CAMERA_RES_WIDTH_PX = 640
CAMERA_RES_HEIGHT_PX = 480
CAMERA_FOV_DEG_X = 4.0
CAMERA_FOV_DEG_Y = 3.0
CAMERA_UPDATE_RATE_HZ = 30
CAMERA_INITIAL_POSITION = "center"  # centre of the 2000x2000 world

# ---------------------------------------------------------------------------
# Target
# ---------------------------------------------------------------------------
TARGET_TYPE = "beacon_spot"
TARGET_COUNT_DEFAULT = 1
TARGET_SHAPE_DEFAULT = "square"
TARGET_SIZE_MIN_PX = 5
TARGET_SIZE_MAX_PX = 20
TARGET_SIZE_DEFAULT_PX = 10
TARGET_INITIAL_LOCATION_DEFAULT = "random"
TARGET_MOTIONS = [
    "straight_line", "circular", "figure_8", "random",   # mandatory (>=4)
    "spiral", "sinusoidal",                               # optional
]

# ---------------------------------------------------------------------------
# Camera motion constraints
# ---------------------------------------------------------------------------
MAX_PAN_SPEED_DEG_S = 5.0    # user-defined range 5-10
MAX_TILT_SPEED_DEG_S = 5.0   # user-defined range 5-10
CONTROL_UPDATE_INTERVAL_HZ = 20  # minimum

# ---------------------------------------------------------------------------
# Performance targets (for self-check against PS requirements, not tuning)
# ---------------------------------------------------------------------------
ACQUISITION_TIME_MAX_S = 2.0
TRACKING_ERROR_MAX_PX = 10
TARGET_LOSS_MAX_PCT = 5.0
REACQUISITION_TIME_MAX_S = 1.0
PROCESSING_SPEED_MIN_FPS = 20

# ---------------------------------------------------------------------------
# Noise / Disturbance engine
# ---------------------------------------------------------------------------
NOISE_TYPES = ["salt_pepper", "gaussian", "poisson"]  # user-selectable, one or more
SALT_PEPPER_DENSITY_DEFAULT = 0.10       # ~10% of image
NOISE_MAX_STD_DEV_PX = 20
CAMERA_JITTER_MAX_PX_PER_FRAME = 20
ATMOSPHERIC_DISTURBANCES = ["clear", "haze", "fog", "rain", "low_light"]
PLATFORM_MOTION_MAX_PX_PER_FRAME = 20
PLATFORM_MOTION_DEFAULT = "linear"
PLATFORM_MOTION_OPTIONAL = ["circular", "random", "spiral", "figure_8"]

# ---------------------------------------------------------------------------
# Controller gains (Electrical B / control.py — tune here, not inline)
# ---------------------------------------------------------------------------
PID_KP = 0.6
PID_KI = 0.0
PID_KD = 0.15

# ---------------------------------------------------------------------------
# Search / reacquisition thresholds (Electrical B / control.py)
# ---------------------------------------------------------------------------
LOST_THRESHOLD_FRAMES = 5        # consecutive frames w/o valid detection -> LOST
SEARCH_PATTERN = "expanding_spiral"

# ---------------------------------------------------------------------------
# Export options (CS / reporting.py)
# ---------------------------------------------------------------------------
EXPORT_FORMATS = ["csv", "json", "xlsx"]
OUTPUT_DIR = "outputs/"
