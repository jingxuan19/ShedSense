from ultralytics import YOLO
import logging
import datetime

class YOLOmodel:
    def __init__(self, is_cpu: bool):
        if is_cpu:
            self.model = YOLO("/home/shedsense1/ShedSense/src/models/yolov10n.pt", task="detect")
        else:
            self.model = YOLO("/home/shedsense1/ShedSense/src/models/yolov10n_saved_model/yolov10n_float32.tflite", task="detect")
        
        logging.basicConfig(filename=f"/home/shedsense1/ShedSense/src/roi/logs/{datetime.date.today()}_YOLOlogging", level=logging.INFO)        
        
        self.logger = logging.getLogger(__name__)

    def detect(self, frame):
        result = self.model.predict(frame)
        return result
    
    def separate_objects(self, result):
        boxes = result[0].boxes.xyxy
        scores = result[0].boxes.conf
        class_ids = result[0].boxes.cls # 0:person, 1:bicycle
        class_names = [self.model.names[int(c_id)] for c_id in class_ids]

        for box, score, c_id, c_name in zip(boxes, scores, class_ids, class_names):
            self.logger.info(f"{datetime.datetime.now().time()} Detected object {c_name} with confidence {score} at {box}")        
        
        return boxes, scores, class_ids.int(), class_names

