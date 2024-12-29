from picamera2 import Picamera2
import cv2
import time
from detection.roi.YOLOmodel import YOLOmodel

camera = Picamera2()
cam_config = camera.create_video_configuration(main={"format": 'RGB888'})
camera.configure(cam_config)

camera.start()
time.sleep(1)

Yolomodel = YOLOmodel(10)

while True:
    frame = camera.capture_array("main")
    result = Yolomodel.detect(frame)
    cv2.imshow("Camera", result)

    if cv2.waitKey(1) == ord('q'):
        break