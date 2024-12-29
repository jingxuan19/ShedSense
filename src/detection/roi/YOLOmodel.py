from ultralytics import YOLO
import cv2
import numpy as np

class YOLOmodel:
    def __init__(self, ver: int):
        self.ver = ver
        self.model = YOLO("/home/shedsense1/ShedSense/src/detection/roi/yolov10n.pt")

        self.model.export(format="edgetpu")

    def detect(self, frame):
        result = self.model(frame)
        return result[0].plot()

