import cv2
import time


class VideoIngestion:

    def __init__(self, video_path=None, mode="video"):

        self.mode = mode
        self.video_path = video_path

        self.frame_number = 0

        if self.mode == "video":

            self.cap = cv2.VideoCapture(video_path)

            if not self.cap.isOpened():
                raise ValueError(
                    f"Could not open video: {video_path}"
                )

            self.fps = self.cap.get(cv2.CAP_PROP_FPS)

            self.width = int(
                self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            )

            self.height = int(
                self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            )

            self.total_frames = int(
                self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
            )

            self.validate_video()

        elif self.mode == "simulation":

            self.fps = 30
            self.width = 2000
            self.height = 2000
            self.total_frames = 0

            self.cap = None

        else:

            raise ValueError(
                "Mode must be 'video' or 'simulation'"
            )


    def validate_video(self):

        print("\n========== VIDEO VALIDATION ==========")

        if abs(self.fps - 30) <= 1:
            print("FPS: PASS")
        else:
            print("FPS: FAIL")

        if self.width == 2000 and self.height == 2000:
            print("Resolution: PASS")
        else:
            print("Resolution: FAIL")

        if self.total_frames > 0:
            print("Frame Count: PASS")
        else:
            print("Frame Count: FAIL")

        print("======================================\n")


    def read_frame(self):

        if self.mode == "video":

            ret, frame = self.cap.read()

            if not ret:
                return None

            timestamp = self.frame_number / self.fps

            data = {
                "frame": frame,
                "frame_number": self.frame_number,
                "timestamp": timestamp,
                "fps": self.fps,
                "width": self.width,
                "height": self.height
            }

            self.frame_number += 1

            return data

        elif self.mode == "simulation":

            # Create a blank virtual environment
            frame = (
                255 *
                cv2.UMat(
                    self.height,
                    self.width,
                    cv2.CV_8UC3
                )
            ).get()

            # Black background
            frame[:] = 0

            # Moving target
            x = int(
                self.width / 2 +
                600 *
                __import__("math").cos(
                    self.frame_number / 30
                )
            )

            y = int(
                self.height / 2 +
                600 *
                __import__("math").sin(
                    self.frame_number / 30
                )
            )

            # Draw 10 × 10 target
            cv2.rectangle(
                frame,
                (x - 5, y - 5),
                (x + 5, y + 5),
                (255, 255, 255),
                -1
            )

            timestamp = self.frame_number / self.fps

            data = {
                "frame": frame,
                "frame_number": self.frame_number,
                "timestamp": timestamp,
                "fps": self.fps,
                "width": self.width,
                "height": self.height
            }

            self.frame_number += 1

            return data


    def release(self):

        if self.cap is not None:
            self.cap.release()