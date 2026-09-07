import cv2
import time

from ingestion import VideoIngestion
import config


video = VideoIngestion(
    video_path=config.VIDEO_PATH,
    mode=config.MODE
)


print("========== LAYER 2 ==========")
print("Mode:", config.MODE)
print("FPS:", video.fps)
print("Width:", video.width)
print("Height:", video.height)
print("=============================")


while True:

    start_time = time.time()

    data = video.read_frame()

    if data is None:
        break

    frame = data["frame"]

    cv2.imshow(
        "Layer 2 - Simulation",
        frame
    )

    # Maintain approximately 30 FPS
    elapsed = time.time() - start_time

    delay = max(
        1,
        int((1 / video.fps - elapsed) * 1000)
    )

    key = cv2.waitKey(delay) & 0xFF

    if key == ord("q"):
        break


video.release()

cv2.destroyAllWindows()