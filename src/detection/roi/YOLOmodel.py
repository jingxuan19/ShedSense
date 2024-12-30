from ultralytics import YOLO

class YOLOmodel:
    def __init__(self, ver: int):
        self.ver = ver
        self.model = YOLO("/home/shedsense1/ShedSense/src/detection/yolov10n_saved_model/yolov10n_full_integer_quant_edgetpu.tflite", task="detect")

    def detect(self, frame):
        result = self.model.predict(frame)
        return result[0].plot()

