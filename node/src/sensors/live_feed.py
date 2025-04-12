from picamera2 import Picamera2
import cv2
import time
import logging
import json
import numpy as np
from mqtt.mqtt_pi import MQTTPiClient
import datetime
# from utils.sort import *

CAMERA_ID = "test_1"

logger = logging.getLogger(__name__)
handler = logging.FileHandler(f"/home/shedsense1/ShedSense/node/logs/{datetime.date.today()}")
       
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def live_feed(shutdown_event, is_recorded, frame_buffer):
    # is_recorded = "/home/shedsense1/Desktop/recordings/2025-02-21_09-33-10.mp4"
    if is_recorded:
        logger.info("Pulling stream from recording")
        
        cap = cv2.VideoCapture(is_recorded)
    else:      
        video = None
        
        camera = Picamera2()
        camera.stop()
        cam_config = camera.create_video_configuration(main={"format": 'RGB888'})
        cam_config["controls"]["FrameRate"] = 15
        camera.configure(cam_config)

        camera.start()
        
   
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
            
            
        # Publish frame
        _, payload = cv2.imencode('.jpeg', frame)
        # print(payload.dtype, payload.size)
        Node_MQTT_client.publish("ShedSense/node/frame", payload.tobytes())
        
        # TODO: Undistort the frame
        
        
        
        frame = cv2.resize(frame, (640, 640))
        
        if frame_buffer.full():
            frame_buffer.get()
        frame_buffer.put(frame)
                                
        end = time.time()
        logger.info(f"Time taken to record frame: {end-start}s")
    
    logger.warning("Commencing shutdown, releasing resources")
    
    if not is_recorded:
        video.release()
    else:
        cap.release()
    Node_MQTT_client.disconnect()