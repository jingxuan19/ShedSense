import cv2
import torch
from models.YOLOmodel import YOLOmodel

def roi_detection(is_cpu: bool, camera):
    Yolomodel = YOLOmodel(is_cpu)

    while True:
        frame = camera.capture_array("main")       
        result = Yolomodel.detect(frame)   
        
        cv2.imshow("Camera", result[0].plot())

        detected_objects = Yolomodel.separate_objects(result) # boxes, score, class_id, class_name
        bikes = 0
        people = 0
        for detected in detected_objects:
            if detected["class_id"] == 0:
                people += 1
            elif detected["class_id"] == 1:
                bikes += 1

        print(f"number of bikes: {bikes}")
        print(f"number of people: {people}")
        
        
        if cv2.waitKey(1) == ord('q'):
            break