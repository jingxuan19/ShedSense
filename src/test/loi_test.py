import cv2
import numpy as np
from models.YOLOmodel import YOLOmodel
import yaml
from loi.detection.masking import masking
from loi.detection.load_lines import load_lines

LOCATION = "test_1"
WINDOW_SIZE = (720, 1720)

def loi_detection(is_cpu: bool, camera):   
    # Everything concerning the region of interest (shed) can be calculated beforehand
    borders = load_lines(LOCATION)
            
    yolo_roi = masking(WINDOW_SIZE, borders)

    # Yolomodel
    Yolomodel = YOLOmodel(is_cpu)

    while True:
        frame = camera.capture_array("main")   
        # print(frame.shape)
        
        for line in borders:
            # line coords must be in (x,y)
            cv2.line(frame, line.pt1, line.pt2, color=(0, 255, 0), thickness=5)
                
        result = Yolomodel.detect(frame)   
        detected_objects = Yolomodel.separate_objects(result) # boxes, score, c_id, c_name

        for detected in detected_objects:
            # filter bikes and people
            if detected.class_id not in (0,1):
                continue
            
            object_mask = np.zeros(WINDOW_SIZE)
            cv2.rectangle(object_mask, detected.box[0], detected.box[1], 255, -1)
            
            if np.sum(cv2.bitwise_and(yolo_roi, object_mask)) != 0:
                # there's an overlap between the object bounding box and the roi for yolo
                #Lucas-Kanade
                pass   
        
        cv2.imshow("LOI implementation", result[0].plot())

       
        # if len(detected_objects[2]):
        #     class_count = torch.bincount(detected_objects[2])
        #     print(f"number of bikes: {class_count[1]}")
        #     print(f"number of people: {class_count[0]}")
        # else:
        #     print(f"number of bikes: 0")
        #     print(f"number of people: 0")
        
        
        if cv2.waitKey(1) == ord('q'):
            break