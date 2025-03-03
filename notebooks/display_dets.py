import cv2
from ultralytics import YOLO

model = YOLO("/home/shedsense1/ShedSense/node/src/models/yolov10n_saved_model/yolov10n_full_integer_quant_edgetpu.tflite", task="detect")

cap = cv2.VideoCapture()