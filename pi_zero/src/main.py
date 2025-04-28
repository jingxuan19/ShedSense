from mqtt.mqtt import MQTTPiClient      
from picamera2 import Picamera2
import cv2
import time
import argparse
import logging
import json
import numpy as np
import datetime
# from utils.sort import *

CAMERA_ID = "entrance"
DEVICE = "pi_zero"

logger = logging.getLogger(__name__)
handler = logging.FileHandler(f"/home/shedsense2/ShedSense/{DEVICE}/logs/{datetime.date.today()}")
       
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def main():
    # is_recorded = "/home/shedsense1/Desktop/recordings/2025-02-21_09-33-10.mp4"
        
    # Default to LOI implementation  
    camera = Picamera2()
    camera.stop()
    cam_config = camera.create_video_configuration(main={"format": 'RGB888'})
    cam_config["controls"]["FrameRate"] = 15
    camera.configure(cam_config)

    camera.start()
    time.sleep(1)
        
    prev_frame_grey = None
    wakeup_time_left = 0
    wakeup_time_left = 0
    
    video = None
    
    #MQTT setup
    Node_MQTT_client = MQTTPiClient()

    try:
        while True:        
            start = time.time()

            frame = camera.capture_array("main")   
            
            if video is None:
                # for recording purpose during testing
                video = cv2.VideoWriter(f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (frame.shape[1], frame.shape[0]))
            video.write(frame)
            
                    
            # Grayscale to calculate frame difference
            # 2 thresholds here, 1 is how much change per pixel to determine if the pixel changed.
            # The other is how many pixels much change to determine that we need to start recording
            frame_grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_frame_grey is None:
                prev_frame_grey = frame_grey
            
            frame_difference = cv2.absdiff(prev_frame_grey, frame_grey)
            
            _, filter_frame = cv2.threshold(frame_difference, 20, 255, cv2.THRESH_BINARY)
            
            pixels_changed = np.sum(filter_frame)/255
            logger.info(f"no. of pixels_changed: {pixels_changed}")
            
            
            if pixels_changed > 9400:
                wakeup_time_left = 1 # How many more frames does it take before it decides that an event is over
                logger.info("Pixels changed")
            
            if wakeup_time_left > 0:
                frame = cv2.resize(frame, (640, 640))
                
                # Publish frame        
                _, payload = cv2.imencode('.jpeg', frame)
                # print(payload.dtype, payload.size)
                Node_MQTT_client.publish("ShedSense/pi_zero/frame", payload.tobytes())
                
                wakeup_time_left -= 1
                
            prev_frame_grey = frame_grey
                        
            end = time.time()
            logger.info(f"Time taken to process frame: {end-start}s")
    except KeyboardInterrupt:
        logger.warning("Commencing shutdown, releasing resources")
        video.release()
        Node_MQTT_client.disconnect()   
    
if __name__ == "__main__":
    main()