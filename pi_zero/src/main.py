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

logger = logging.getLogger(__name__)
handler = logging.FileHandler(f"/home/shedsense1/ShedSense/node/logs/{datetime.date.today()}")
       
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def main(shutdown_event, is_recorded, frame_buffer):
    # is_recorded = "/home/shedsense1/Desktop/recordings/2025-02-21_09-33-10.mp4"
    if is_recorded:
        logger.info("Pulling stream from recording")
        
        cap = cv2.VideoCapture(is_recorded)
    else:      
        video = None
        
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
    
    #MQTT setup
    Node_MQTT_client = MQTTPiClient()

    while not shutdown_event.is_set():        
        start = time.time()
        
        if is_recorded:       
            ret, frame = cap.read()
            
            if not ret:        
                print("flag")      
                break
        else:
            frame = camera.capture_array("main")   

            if not video:
                # for recording purpose during testing
                video = cv2.VideoWriter(f"/home/shedsense1/Desktop/recordings/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (frame.shape[1], frame.shape[0]))
            video.write(frame)
            
        
        _, payload = cv2.imencode('.jpeg', frame)
        # print(payload.dtype, payload.size)

        # Publish frame
        Node_MQTT_client.publish("ShedSense/node/frame", payload.tobytes())
        
        # Grayscale to calculate frame difference
        # 2 thresholds here, 1 is how much change per pixel to determine if the pixel changed.
        # The other is how many pixels much change to determine that we need to start recording
        frame_grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if prev_frame_grey is None:
            prev_frame_grey = frame_grey
            frame_buffer.put(frame)           
        
        frame_difference = cv2.absdiff(prev_frame_grey, frame_grey)
        
        _, filter_frame = cv2.threshold(frame_difference, 30, 255, cv2.THRESH_BINARY)
        
        _, payload = cv2.imencode('.jpeg', filter_frame)
        Node_MQTT_client.publish("ShedSense/node/filtered_frame", payload.tobytes())
        
        pixels_changed = np.sum(filter_frame)/255
        logger.info(f"no. of pixels_changed: {pixels_changed}")
        
        
        if pixels_changed > 5000:
            wakeup_time_left = 1 # How many more frames does it take before it decides that an event is over
            logger.info(f"Pixels changed")
        
        if wakeup_time_left > 0:
            frame = cv2.resize(frame, (640, 640))
            
            if frame_buffer.full():
                frame_buffer.get()
                
            frame_buffer.put(frame)
            wakeup_time_left -= 1
            
        prev_frame_grey = frame_grey
                    
        end = time.time()
        logger.info(f"Time taken to process frame: {end-start}s")
    
    logger.warning("Commencing shutdown, releasing resources")
    
    if not is_recorded:
        video.release()
    else:
        cap.release()
    Node_MQTT_client.disconnect()
    cv2.destroyAllWindows()
   
    
if __name__ == "__main__":
    main()