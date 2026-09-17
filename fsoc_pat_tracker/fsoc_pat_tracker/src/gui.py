"""
gui.py — Owner: CS (Arpitha)
Tkinter control-panel GUI. Sits entirely on top of app.SimulationSession
and never touches simulation/tracking/predictor/control/analytics/
reporting directly — matches the layering app.py's docstring describes.

Run with: python gui.py
Requires: Pillow (pip install pillow) in addition to the project's
existing OpenCV/numpy/pandas/matplotlib dependencies.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import cv2
from PIL import Image, ImageTk

from app import SimulationSession
from config import CAMERA_RES_WIDTH_PX, CAMERA_RES_HEIGHT_PX, CAMERA_UPDATE_RATE_HZ, TARGET_MOTIONS

DISPLAY_SCALE = 1          # bump to 1.5 / 2 if the 640x480 feed feels too small on your monitor
TICK_MS = int(1000 / CAMERA_UPDATE_RATE_HZ)

PAT_STATE_COLORS = {
    "SEARCH": "#888888",
    "ACQUIRE": "#e6b800",
    "TRACK": "#2e9e44",
    "LOST": "#cc3333",
    "REACQUIRE": "#e07b00",
    "HANDOVER_READY": "#1a73e8",
}


class TrackerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("FSOC Virtual PAT Tracker")
        self.session = None
        self.running = False
        self.after_id = None

        self._build_layout()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_layout(self):
        container = ttk.Frame(self.root, padding=10)
        container.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # --- Left: configuration ---
        controls = ttk.LabelFrame(container, text="Configuration", padding=10)
        controls.grid(row=0, column=0, sticky="n", padx=(0, 10))

        ttk.Label(controls, text="Mode").grid(row=0, column=0, sticky="w")
        self.mode_var = tk.StringVar(value="simulation")
        mode_frame = ttk.Frame(controls)
        mode_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Radiobutton(mode_frame, text="Simulation", variable=self.mode_var,
                         value="simulation", command=self._on_mode_change).pack(side="left")
        ttk.Radiobutton(mode_frame, text="Video (benchmark)", variable=self.mode_var,
                         value="video", command=self._on_mode_change).pack(side="left")

        ttk.Label(controls, text="Motion type").grid(row=2, column=0, sticky="w")
        default_motion = "random" if "random" in TARGET_MOTIONS else TARGET_MOTIONS[0]
        self.motion_var = tk.StringVar(value=default_motion)
        self.motion_combo = ttk.Combobox(controls, textvariable=self.motion_var,
                                          values=TARGET_MOTIONS, state="readonly", width=15)
        self.motion_combo.grid(row=2, column=1, sticky="w", pady=2)

        ttk.Label(controls, text="Num. targets").grid(row=3, column=0, sticky="w")
        self.targets_var = tk.IntVar(value=1)
        ttk.Spinbox(controls, from_=1, to=5, textvariable=self.targets_var, width=5).grid(
            row=3, column=1, sticky="w", pady=2)

        ttk.Label(controls, text="Seed (optional)").grid(row=4, column=0, sticky="w")
        self.seed_var = tk.StringVar(value="")
        ttk.Entry(controls, textvariable=self.seed_var, width=10).grid(row=4, column=1, sticky="w", pady=2)

        self.video_row = ttk.Frame(controls)
        self.video_row.grid(row=5, column=0, columnspan=2, sticky="we", pady=2)
        self.video_path_var = tk.StringVar(value="")
        ttk.Entry(self.video_row, textvariable=self.video_path_var, width=18, state="readonly").pack(side="left")
        ttk.Button(self.video_row, text="Browse…", command=self._browse_video).pack(side="left", padx=(4, 0))
        self.video_row.grid_remove()  # hidden until "video" mode is selected

        ttk.Separator(controls, orient="horizontal").grid(row=6, column=0, columnspan=2, sticky="we", pady=8)

        btns = ttk.Frame(controls)
        btns.grid(row=7, column=0, columnspan=2, sticky="we")
        self.start_btn = ttk.Button(btns, text="Start", command=self._on_start)
        self.start_btn.pack(side="left", padx=2)
        self.pause_btn = ttk.Button(btns, text="Pause", command=self._on_pause, state="disabled")
        self.pause_btn.pack(side="left", padx=2)
        self.stop_btn = ttk.Button(btns, text="Stop", command=self._on_stop, state="disabled")
        self.stop_btn.pack(side="left", padx=2)

        self.export_btn = ttk.Button(controls, text="Export Results…", command=self._on_export, state="disabled")
        self.export_btn.grid(row=8, column=0, columnspan=2, sticky="we", pady=(10, 0))

        # --- Middle: camera view ---
        view_frame = ttk.LabelFrame(container, text="Camera View", padding=5)
        view_frame.grid(row=0, column=1, sticky="n")
        self.canvas = tk.Canvas(view_frame, width=CAMERA_RES_WIDTH_PX * DISPLAY_SCALE,
                                 height=CAMERA_RES_HEIGHT_PX * DISPLAY_SCALE, bg="black")
        self.canvas.pack()
        self._blank_canvas()

        # --- Right: live telemetry ---
        telemetry = ttk.LabelFrame(container, text="Live Telemetry", padding=10)
        telemetry.grid(row=0, column=2, sticky="n", padx=(10, 0))

        self.pat_state_var = tk.StringVar(value="—")
        self.frame_var = tk.StringVar(value="0")
        self.detected_var = tk.StringVar(value="—")
        self.confidence_var = tk.StringVar(value="—")
        self.error_var = tk.StringVar(value="—")
        self.pan_var = tk.StringVar(value="0.00°")
        self.tilt_var = tk.StringVar(value="0.00°")
        self.azimuth_var = tk.StringVar(value="—")
        self.elevation_var = tk.StringVar(value="—")
        self.fps_var = tk.StringVar(value="—")
        self.handover_var = tk.StringVar(value="No")

        self._telemetry_row("Frame", self.frame_var, telemetry, 0)
        self._telemetry_row("PAT State", self.pat_state_var, telemetry, 1, is_state=True)
        self._telemetry_row("Detected", self.detected_var, telemetry, 2)
        self._telemetry_row("Confidence", self.confidence_var, telemetry, 3)
        self._telemetry_row("Tracking error (px)", self.error_var, telemetry, 4)
        self._telemetry_row("Pan angle", self.pan_var, telemetry, 5)
        self._telemetry_row("Tilt angle", self.tilt_var, telemetry, 6)
        self._telemetry_row("Target azimuth", self.azimuth_var, telemetry, 7)
        self._telemetry_row("Target elevation", self.elevation_var, telemetry, 8)
        self._telemetry_row("Processing FPS", self.fps_var, telemetry, 9)
        self._telemetry_row("Handover ready", self.handover_var, telemetry, 10)

    def _telemetry_row(self, label, var, parent, row, is_state=False):
        ttk.Label(parent, text=f"{label}:").grid(row=row, column=0, sticky="w", pady=2)
        if is_state:
            self.pat_state_label = tk.Label(parent, textvariable=var, width=14,
                                             bg=PAT_STATE_COLORS.get("SEARCH"), fg="white")
            self.pat_state_label.grid(row=row, column=1, sticky="w", padx=(6, 0))
        else:
            ttk.Label(parent, textvariable=var).grid(row=row, column=1, sticky="w", padx=(6, 0))

    def _blank_canvas(self):
        self.canvas.delete("all")
        self.canvas.create_text(
            CAMERA_RES_WIDTH_PX * DISPLAY_SCALE // 2, CAMERA_RES_HEIGHT_PX * DISPLAY_SCALE // 2,
            text="Press Start", fill="white", font=("Segoe UI", 14),
        )

    # ------------------------------------------------------------------
    # UI events
    # ------------------------------------------------------------------
    def _on_mode_change(self):
        if self.mode_var.get() == "video":
            self.video_row.grid()
            self.motion_combo.configure(state="disabled")
        else:
            self.video_row.grid_remove()
            self.motion_combo.configure(state="readonly")

    def _browse_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if path:
            self.video_path_var.set(path)

    def _on_start(self):
        if self.session is not None:
            self.session.close()

        mode = self.mode_var.get()
        seed = None
        if self.seed_var.get().strip():
            try:
                seed = int(self.seed_var.get().strip())
            except ValueError:
                messagebox.showerror("Invalid seed", "Seed must be an integer.")
                return

        try:
            if mode == "video":
                video_path = self.video_path_var.get().strip()
                if not video_path:
                    messagebox.showerror("No video selected", "Choose a video file first.")
                    return
                self.session = SimulationSession(mode="video", video_path=video_path)
            else:
                self.session = SimulationSession(
                    mode="simulation",
                    motion_type=self.motion_var.get(),
                    num_targets=self.targets_var.get(),
                    seed=seed,
                )
        except (FileNotFoundError, ValueError) as e:
            messagebox.showerror("Could not start", str(e))
            return

        self._blank_canvas()
        self.running = True
        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal", text="Pause")
        self.stop_btn.configure(state="normal")
        self.export_btn.configure(state="disabled")
        self._tick()

    def _on_pause(self):
        self.running = not self.running
        self.pause_btn.configure(text="Resume" if not self.running else "Pause")
        if self.running:
            self._tick()
        elif self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def _on_stop(self):
        self.running = False
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled", text="Pause")
        self.stop_btn.configure(state="disabled")
        if self.session is not None and self.session.telemetry_rows:
            self.export_btn.configure(state="normal")

    def _on_export(self):
        if self.session is None or not self.session.telemetry_rows:
            messagebox.showinfo("Nothing to export", "Run a session first.")
            return
        try:
            paths = self.session.export_results(prefix="gui_run")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))
            return
        message = "\n".join(f"{k}: {v}" for k, v in paths.items())
        messagebox.showinfo("Export complete", message)

    def _on_close(self):
        self.running = False
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
        if self.session is not None:
            self.session.close()
        self.root.destroy()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def _tick(self):
        if not self.running or self.session is None:
            return

        result = self.session.step()
        if result is None:
            self._on_stop()
            messagebox.showinfo("Run finished", "End of video / session complete.")
            return

        self._render_frame(result)
        self._update_telemetry(result)

        self.after_id = self.root.after(TICK_MS, self._tick)

    def _render_frame(self, result):
        image = result["image"]
        track = result["track"]

        display = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if image.ndim == 2 else image.copy()
        h, w = display.shape[:2]
        cx, cy = w // 2, h // 2

        # boresight crosshair (where the camera is currently pointed)
        cv2.drawMarker(display, (cx, cy), (0, 255, 0), markerType=cv2.MARKER_CROSS,
                        markerSize=14, thickness=1)

        # predicted/detected centroid: yellow ring = real detection this
        # frame, red ring = prediction-only (blackout/occlusion)
        pred = result["prediction"]
        px, py = int(pred.predicted_centroid_px[0]), int(pred.predicted_centroid_px[1])
        color = (0, 255, 255) if track.detected else (0, 0, 255)
        cv2.circle(display, (px, py), 10, color, 2)

        if DISPLAY_SCALE != 1:
            display = cv2.resize(display, (w * DISPLAY_SCALE, h * DISPLAY_SCALE),
                                  interpolation=cv2.INTER_NEAREST)

        rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
        photo = ImageTk.PhotoImage(image=Image.fromarray(rgb))
        self.canvas.image = photo  # keep a reference so Tkinter doesn't garbage-collect it
        self.canvas.create_image(0, 0, anchor="nw", image=photo)

    def _update_telemetry(self, result):
        row = result["telemetry_row"]
        track = result["track"]
        angle = result["angle_data"]
        cmd = result["command"]

        self.frame_var.set(str(row.frame_id))
        self.pat_state_var.set(cmd.pat_state)
        self.pat_state_label.configure(bg=PAT_STATE_COLORS.get(cmd.pat_state, "#555555"))
        self.detected_var.set("Yes" if track.detected else "No")
        self.confidence_var.set(f"{track.confidence:.2f}")
        self.error_var.set(f"{row.tracking_error_px:.2f}" if row.tracking_error_px is not None else "—")
        self.pan_var.set(f"{row.pan_angle_deg:.2f}\u00b0")
        self.tilt_var.set(f"{row.tilt_angle_deg:.2f}\u00b0")
        self.azimuth_var.set(f"{angle.target_azimuth_deg:.2f}\u00b0" if angle.target_azimuth_deg is not None else "—")
        self.elevation_var.set(f"{angle.target_elevation_deg:.2f}\u00b0" if angle.target_elevation_deg is not None else "—")
        self.fps_var.set(f"{row.fps:.1f}" if row.fps else "—")
        self.handover_var.set("YES" if result["handover_ready"] else "No")


def main():
    root = tk.Tk()
    TrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
