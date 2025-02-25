from picamera2 import Picamera2
import cv2
import time
import argparse
import logging
import json
from loi.detection.loi_detection import loi_detection
from models.YOLOmodel import YOLOmodel
from loi.detection.load_lines import load_lines
from mqtt.mqtt_pi import MQTTPiClient
import datetime
from utils.sort import *

CAMERA_ID = "test_1"

logger = logging.getLogger("Live feed")
handler = logging.FileHandler(f"/home/shedsense1/ShedSense/rpi/logs/live_feed/{datetime.date.today()}_livefeed")
       
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def main(is_cpu, is_recorded):
    if is_recorded:
        cap = cv2.VideoCapture(is_recorded)
    else:      
        video = None
        
        # Default to LOI implementation  
        camera = Picamera2()
        cam_config = camera.create_video_configuration(main={"format": 'RGB888'})
        camera.configure(cam_config)

        camera.start()
        time.sleep(1)
    
    #MQTT setup
    Pi_MQTT_client = MQTTPiClient()
    
    # Everything concerning the region of interest (shed) can be calculated beforehand
    borders = load_lines(CAMERA_ID)
            
    # yolo_roi = masking(WINDOW_SIZE, borders)

    # Yolomodel
    Yolomodel = YOLOmodel(is_cpu)
    
    person_tracker = Sort(max_age=20, min_hits=2, iou_threshold=0.3)
    bike_tracker = Sort(max_age=20, min_hits=2, iou_threshold=0.3)
    
    try:
        while True:
            start = time.time()
            
            if is_recorded:
                ret, frame = cap.read()
                if not ret:
                    return
            else:
                frame = camera.capture_array("main")   

                if not video:
                    video = cv2.VideoWriter(f"/home/shedsense1/Desktop/recordings/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (frame.shape[1], frame.shape[0]))
                video.write(frame)
            
            annotated_frame = loi_detection(frame, borders, Yolomodel, person_tracker, bike_tracker)
            
            for line in borders:
            # line coords must be in (x,y)
                cv2.line(annotated_frame, line.pt1, line.pt2, color=(0, 255, 0), thickness=5)

            _, payload = cv2.imencode('.jpeg', annotated_frame)
            # print(payload.dtype, payload.size)

            Pi_MQTT_client.publish("ShedSense/node/frame", payload.tobytes())
            
            end = time.time()
            logger.info(f"Time taken to process frame: {end-start}s")
    except KeyboardInterrupt:
        Pi_MQTT_client.disconnect()
        if is_recorded:
            cap.release()
        else:
            video.release()
        
    
    # if img_path:
    #     draw_line(img_path)
    #     input()
    # elif is_loi:
    #     loi_detection(is_cpu, camera)
    
    # ROI IMPLEMENTATION DEPRACATED
    # else:
    #     if imgtest:
    #         roi_test(is_cpu, imgtest)
    #     else:
    #         roi_detection(is_cpu, camera)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Starts live feed of Pi camera")
    parser.add_argument("--cpu", help="Use CPU model (default is tflite)", action="store_true")
    parser.add_argument("--recorded", help="Use recorded video for detection", default=None)
    # parser.add_argument("--roi", help="Region-of-Interst implementation", action="store_true")
    # parser.add_argument("--loi", help="Line-of-Interst implementation", action="store_true")
    # parser.add_argument("--imgtest", help="Testing of model on provided file path")
    
    args = parser.parse_args()   
    
    # assert (args.roi or args.loi), "One of the implementations (roi or loi) must be selected"   
    # assert not (args.roi and args.loi), "Only one of the implementations (roi or loi) can be selected"   
    
    main(args.cpu, args.recorded)