import logging
import datetime
import json
# import numpy as np
import cv2
from enum import Enum

from mqtt.mqtt_pi import MQTTPiClient
# from src.loi.detection.Border import Flow_status
from utils.sort import Sort

class Alert_status(str, Enum):
    Clear = 0
    Moderate = 1
    High = 2

class Shed_state:
    logger = None
    
    # MQTT communications
    Node_MQTT_Client = None
    annotated_frame = None
    # alert_status = None
    
    # Shed detections
    person_tracker = None
    bike_tracker = None
    status = None
    history = {}
    
    def __init__(self):
        self.Node_MQTT_Client = MQTTPiClient()        
        self.status = {"people": 0, "bikes": 0, "alert": Alert_status.Clear}
        
        self.person_tracker = Sort(max_age=20, min_hits=2, iou_threshold=0.3)
        self.bike_tracker = Sort(max_age=20, min_hits=2, iou_threshold=0.3)
        
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler(f"/home/shedsense1/ShedSense/node/logs/{datetime.date.today()}")
                    
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
               
        
    def history_update(self, measurements, bike_flag):
        history_copy = self.history.copy()
        for id in history_copy:
            if id%2 != bike_flag:
                continue
            if id in measurements:
                # id is found on frame and in history
                TIF = self.history[id]["TIF"]
                self.history[id] = {"center": measurements[id], "TTL": 20, "TIF": TIF+1}
            else:
                self.history[id]["TTL"] -= 1
                
                if self.history[id]["TTL"] == 0:
                    self.history.pop(id)
                else:
                    self.history[id]["TIF"] = 0
        
        for id in measurements:
            if id not in self.history:
                self.history[id] = {"center": measurements[id], "TTL": 20, "TIF": 0}
                    
    def anomaly_detection(self, threshold):
        count = 0
        max_time_stay = 0
        for id in self.history:
            if id%2 == 0:
                # Only sus out people
                if self.history[id]["TIF"] > threshold:
                    count += 1
                    if self.history[id]["TIF"] > max_time_stay:
                        max_time_stay = self.history[id]["TIF"]
        
        # anomaly detection heuristic
        if count > 0:
            if max_time_stay > threshold*2:
                # time spent in shed by any 1 individual exceeds twice the threshold
                self.status["alert"] = Alert_status.High
            elif count > 3:
                # more than 3 people have spent above threshold in the shed
                self.status["alert"] = Alert_status.High
            else:
                self.status["alert"] = Alert_status.Moderate
        else:
            self.status["alert"] = Alert_status.Clear
    
    def update_annotated_frame(self, frame):
        _, frame = cv2.imencode('.jpeg', frame)
        self.annotated_frame = frame.tobytes()
          
    
    def publish_shed_state(self):
        self.Node_MQTT_Client.publish("ShedSense/node/annotated_frame", self.annotated_frame)
        self.Node_MQTT_Client.publish("ShedSense/node/status", json.dumps(self.status))
        # self.Node_MQTT_Client.publish("ShedSense/node/alert", self.alert_status)
        
 

            
        