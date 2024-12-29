from ultralytics import YOLOv10
import cv2
import numpy as np

def ROI_detection(frame):
    model = YOLOv10()

    results = model(frame)
    

