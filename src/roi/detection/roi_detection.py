import cv2
import torch
from models.YOLOmodel import YOLOmodel

def roi_detection(is_cpu: bool, camera):
    Yolomodel = YOLOmodel(is_cpu)

    while True:
        frame = camera.capture_array("main")       
        result = Yolomodel.detect(frame)   
        
        cv2.imshow("ROI implementation", result[0].plot())

        detected_objects = Yolomodel.separate_objects(result) # box, score, c_id, c_name
        class_count = torch.bincount(detected_objects[2])

        if len(class_count) == 0:
            print(f"number of bikes: 0")
            print(f"number of people: 0")
        elif len(class_count) == 1:
            print(f"number of bikes: 0")  
            print(f"number of people: {class_count[0]}")
        else:
            print(f"number of bikes: {class_count[1]}")
            print(f"number of people: {class_count[0]}")

        if cv2.waitKey(1) == ord('q'):
            break