"""
reporting.py — Owner: CS (Arpitha)
CSV/Excel/JSON export, save logs to outputs/.

STATUS: Mostly done. Port the CSV/summary exporter from your existing
layer6_gui.py performance-log code; add JSON and Excel (xlsx) output formats
to match config.EXPORT_FORMATS.
"""

from config import OUTPUT_DIR, EXPORT_FORMATS
from interfaces import TelemetryRow


def export_csv(rows: list, filename: str):
    """TODO: port existing CSV export from layer6_gui.py."""
    raise NotImplementedError


def export_json_summary(rows: list, filename: str):
    """TODO: aggregate metrics (acquisition time, avg/max tracking error,
    lock retention rate, FPS) into a JSON summary — the PS's required
    Performance Log fields."""
    raise NotImplementedError


def export_excel(rows: list, filename: str):
    """TODO: xlsx export, same data as export_csv."""
    raise NotImplementedError
