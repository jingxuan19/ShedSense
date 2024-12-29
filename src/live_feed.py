from picamera2 import Picamera2
import cv2
import time
from detection.roi.YOLOmodel import ROI_detection

camera = Picamera2()
cam_config = camera.create_video_configuration(main={"format": 'RGB888'})
camera.configure(cam_config)

camera.start()
time.sleep(1)

while True:
    frame = camera.capture_array("main")
    ROI_detection(frame)
    if cv2.waitKey(1) == ord('q'):
        break