import cv2
import torch
from roi.detection.YOLOmodel import YOLOmodel

def roi_detection(is_cpu: bool, camera):
    Yolomodel = YOLOmodel(is_cpu)

    while True:
        frame = camera.capture_array("main")       
        result = Yolomodel.detect(frame)   
        
        cv2.imshow("Camera", result[0].plot())

        detected_objects = Yolomodel.separate_objects(result) # box, score, c_id, c_name
        if len(detected_objects[2]):
            class_count = torch.bincount(detected_objects[2])
            print(f"number of bikes: {class_count[1]}")
            print(f"number of people: {class_count[0]}")
        else:
            print(f"number of bikes: 0")
            print(f"number of people: 0")
        
        
        if cv2.waitKey(1) == ord('q'):
            break