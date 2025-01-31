import cv2
import numpy as np
from models.YOLOmodel import YOLOmodel
import yaml
from loi.detection.masking import masking
from loi.detection.load_lines import load_lines

def loi_detection(camera, borders, model):   
    frame = camera.capture_array("main")   
    # print(frame.shape)
    
    for line in borders:
        # line coords must be in (x,y)
        cv2.line(frame, line.pt1, line.pt2, color=(0, 255, 0), thickness=5)
            
    result = model.detect(frame)   
    # detected_objects = model.separate_objects(result) # boxes, score, c_id, c_name

    # for detected in detected_objects:
    #     # filter bikes and people
    #     if detected.class_id not in (0,1):
    #         continue
        
    #     object_mask = np.zeros(window_size)
    #     cv2.rectangle(object_mask, detected.box[0], detected.box[1], 255, -1)
        
    #     # if np.sum(cv2.bitwise_and(, object_mask)) != 0:
    #     #     # there's an overlap between the object bounding box and the roi for yolo
    #     #     #Lucas-Kanade
    #     #     pass   
    
    # cv2.imshow("LOI implementation", result[0].plot())
    
    return result[0].plot()

    
    # if len(detected_objects[2]):
    #     class_count = torch.bincount(detected_objects[2])
    #     print(f"number of bikes: {class_count[1]}")
    #     print(f"number of people: {class_count[0]}")
    # else:
    #     print(f"number of bikes: 0")
    #     print(f"number of people: 0")
    
    
