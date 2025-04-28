import logging
import datetime
import json
# import numpy as np
import cv2
from enum import Enum
from math import inf
import yaml
import numpy as np
# from src.loi.detection.Border import Flow_status
from sort import Sort

class Alert_status(str, Enum):
    Clear = 0
    Moderate = 1
    High = 2

class Shed_state:   
    # MQTT communications
    Node_MQTT_Client = None
    annotated_frame = None
    # alert_status = None
    
    # Shed detections
    bike_in_flag = False
    
    # cam 1
    cam1_person_tracker = None
    cam1_bike_tracker = None
    status = None
    history = {}
    lots = None

    # cam 2
    cam2_person_tracker = None
    homography_matrix = None
    cam2_lot_history = {}
    cam2_person_history = {}
    
    def __init__(self):
        self.status = {"people": 0, "bikes": 0, "alert": Alert_status.Clear, "cam_2_people_locations": {}}
        
        self.cam1_person_tracker = Sort(max_age=20, min_hits=2, iou_threshold=0.3)
        self.cam1_bike_tracker = Sort(max_age=20, min_hits=2, iou_threshold=0.3)
        
        self.cam2_person_tracker = Sort(max_age=20, min_hits=2, iou_threshold=0.3)
        with open(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\ShedSense\node\config\calibration.yaml", "r") as f:
            config = yaml.safe_load(f)
        self.homography_matrix = config["H"]                   
               
        
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
    
    
    def cam2_bike_lot_history_update(self, predictions):
        people_locations = []
        lot_index_with_people = []
        for x1, _, x2, y2, person_id in predictions:
            xo, yo = (x2-x1)/2+x1, y2
            
            # Homography
            point = np.array([[[xo, yo]]], dtype=np.float64)
            point = cv2.perspectiveTransform(point, self.homography_matrix)
            xo, yo = point[0, 0, :]           
            people_locations.append(point[0,0,:])
            
            if person_id not in self.cam2_person_history:
                self.cam2_person_history[person_id] = []
            self.cam2_person_history[person_id].append(point[0,0,:])
            
            # is the point in a lot?
            for id in self.lots:
                xl1, xl2 ,yl1, yl2 = self.lots[id]["coords"]
                if (xo <= xl2) and (xo >= xl1):
                    if (yo <= yl2) and (yo >= yl1):
                        lot_index_with_people.append(id)
             
        for lot_index in lot_index_with_people:
            if lot_index in self.cam2_lot_history:
                self.cam2_lot_history[lot_index][person_id] += 1 
                if self.cam2_lot_history[lot_index][person_id] > 20:
                    self.lots[lot_index]["is_occupied"] = not self.lots[lot_index]["is_occupied"]
                    self.cam2_lot_history[lot_index][person_id] = -inf
                    
            else:
                self.cam2_lot_history[lot_index] = {person_id: 1}   
        
        self.status["cam_2_people_locations"] = people_locations  

    
    def person_bike_matching(self, people_measurement, bike_measurement):
        for p_id in people_measurement:
            pass
        
            
        # history_copy = self.cam2_lot_history        
        # for x1,y1,x2,y2,_ in predictions:
        #     lot_index, area = self.greatest_intersection_lot((x1,x2,y1,y2))
            
        #     # NOTE: Area threshold here
        #     if area > 10:
        #         if lot_index in self.cam2_bike_lot_history:
        #             self.cam2_lot_history[lot_index]["TIF"] += 1
        #             self.cam2_lot_history[lot_index]["TTL"] = 21
                    
                    
        #             # NOTE: Time spent in lot threshold here
        #             if self.cam2_lot_history[lot_index]["TIF"] > 20:
        #                 if self.lots[lot_index][-1] == (0, 255, 0):
        #                     self.lots[lot_index][-1] = (255, 0, 0)
        #                 elif self.lots[lot_index][-1] == (255, 0, 0):
        #                     self.lots[lot_index][-1] = (0, 255, 0)
                    
        #         else:
        #             self.cam2_lot_history[lot_index] = {"TTL": 21, "TIF": 0}
                    
        # for lot_index in history_copy:
        #     self.cam2_lot_history[lot_index]["TTL"] -= 1
        #     if self.cam2_lot_history[lot_index]["TTL"] == 0:
        #         self.cam2_lot_history.pop(lot_index)
                    
                
    
    def cam2_anomaly_detection(self, predictions):
        pass
    
    # def greatest_intersection_lot(self, bounding_box):
    #     max_area = 0
    #     id_of_max = None
    #     for i, xl1, xl2, yl1, yl2, _ in enumerate(self.lots):
    #         x1, x2, y1, y2 = bounding_box
    #         x_left = max(xl1, x1)
    #         x_right = min(xl2, x2)
    #         y_top = max(yl1, y1)
    #         y_bottom = min(yl2, y2)
    
    #         if x_right < x_left or y_bottom < y_top:
    #             continue

    #         area = (x_right - x_left) * (y_bottom - y_top)       
    #         if area > max_area:
    #             max_area = area
    #             id_of_max = i

    #     return id_of_max, max_area            
            
            
            
    
    def update_annotated_frame(self, frame):
        _, frame = cv2.imencode('.jpeg', frame)
        self.annotated_frame = frame.tobytes()
          
    def publish_shed_state(self):
        # self.Node_MQTT_Client.publish("ShedSense/node/annotated_frame", self.annotated_frame)
        self.Node_MQTT_Client.publish("ShedSense/node/status", json.dumps(self.status))
    
        # self.Node_MQTT_Client.publish("ShedSense/node/alert", self.alert_status)
        
 

            
        