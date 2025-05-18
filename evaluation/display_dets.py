import cv2
import numpy as np
from ultralytics import YOLO
from sort import Sort
from loi_detection import loi_detection
from Shed_state import Shed_state
from load_lines import load_lines
# from ultralytics import YOLO

# cap = cv2.VideoCapture("/home/shedsense1/ShedSense/data/filtered_raw/02-26_raw.mp4")
cap = cv2.VideoCapture(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\recordings\Detections\02-26_raw.mp4")

timestamps = [cap.get(cv2.CAP_PROP_POS_MSEC)]

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# yolo_out = cv2.VideoWriter("/home/shedsense1/ShedSense/data/detect_sort/02-26_yolo.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (width, height))
# sort_out = cv2.VideoWriter("/home/shedsense1/ShedSense/data/detect_sort/02-26_sort.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (width, height))
# model = YOLO("/home/shedsense1/ShedSense/node/src/models/yolov10n_saved_model/yolov10n_float32.tflite", task="detect")

# yolo_out = cv2.VideoWriter(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\recordings\Detections\02-26_yolo.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (width, height))
sort_out = cv2.VideoWriter(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\recordings\Detections\02-26_sort_new.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (width, height))
model = YOLO(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\ShedSense\node\src\models\yolov10n_saved_model\yolov10n_float32.tflite", task="detect")

person_tracker = Sort(max_age=20, min_hits=2, iou_threshold=0.3)
bike_tracker = Sort(max_age=20, min_hits=2, iou_threshold=0.3)

Shedstate = Shed_state()

borders = load_lines("test_1")
try:
    while cap.isOpened():
        ret, frame =  cap.read()
        if not ret:
            break
        
        yolo_det, sort_det = loi_detection(frame, model, Shedstate, borders)
        
        for line in borders:
            # line coords must be in (x,y)
            cv2.line(sort_det, line.pt1, line.pt2, color=(0, 255, 0), thickness=5)
            
        # cv2.imshow("yolo", yolo_det)
        cv2.imshow("sort", sort_det)
        
        # yolo_out.write(yolo_det)
        sort_out.write(sort_det)
            
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
except KeyboardInterrupt:   
    cap.release()
    # yolo_out.release()
    sort_out.release()
    