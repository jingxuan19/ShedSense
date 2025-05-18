from ultralytics import YOLO
import logging
import datetime

class YOLOmodel:
    def __init__(self, is_cpu: bool):
        # if is_cpu:
        #     self.model = YOLO("/home/shedsense1/ShedSense/node/src/models/yolov10n.pt", task="detect")
        # else:
        #     self.model = YOLO("/home/shedsense1/ShedSense/node/src/models/yolov10n_saved_model/yolov10n_full_integer_quant_edgetpu.tflite", task="detect")
        self.model = YOLO(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\ShedSense\node\src\models\yolov10n_saved_model\yolov10n_float32.tflite", task="detect")

        
        # self.logger = logging.getLogger(__name__)
        # self.handler = logging.FileHandler(f"/home/shedsense1/ShedSense/node/logs/{datetime.date.today()}")
        
        # self.logger.setLevel(logging.INFO)
        # self.logger.addHandler(self.handler)        

    def detect(self, frame):
        result = self.model.predict(frame, classes=[0,1])
        return result
    
    def separate_objects(self, result):
        boxes = result[0].boxes.xyxy
        scores = result[0].boxes.conf
        class_ids = result[0].boxes.cls # 0:person, 1:bicycle
        class_names = [self.model.names[int(c_id)] for c_id in class_ids]

        detected_objects = []
        for box, score, c_id, c_name in zip(boxes, scores, class_ids, class_names):
            detected_objects.append({
                "box": box,
                "score": score,
                "class_id": c_id,
                "class_name": c_name
            })    
            
            # self.logger.info(f"Detected object {c_name} with confidence {score} at {box}")
        
        return detected_objects

