import time
from picamera2 import Picamera2
from mqtt_pi import MQTTPiClient
import cv2

try:
    camera = Picamera2()
    camera.stop()
    cam_config = camera.create_video_configuration(main={"format": 'RGB888'})
    cam_config["controls"]["FrameRate"] = 15
    camera.configure(cam_config)

    camera.start()
    time.sleep(1)

    Client = MQTTPiClient()
    while True:
        frame = camera.capture_array("main")
        
        _, frame = cv2.imencode('.jpeg', frame)
        frame = frame.tobytes()   

        Client.publish("ShedSense/node/frame", frame)

except KeyboardInterrupt:
    camera.stop()