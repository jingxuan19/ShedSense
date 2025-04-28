import logging
import datetime
import json
# import numpy as np
import cv2
import time
import math
from enum import Enum
from math import inf
import yaml
import numpy as np
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
        self.Node_MQTT_Client = MQTTPiClient()        
        # NOTE: I set people to 1 for testing
        self.status = {"people": 1, "bikes": 0, "alert": Alert_status.Clear, "cam_2_people_locations": []}
        
        self.cam1_person_tracker = Sort(max_age=20, min_hits=2, iou_threshold=0.3)
        self.cam1_bike_tracker = Sort(max_age=20, min_hits=2, iou_threshold=0.3)
        
        self.cam2_person_tracker = Sort(max_age=20, min_hits=2, iou_threshold=0)
        with open("/home/shedsense1/ShedSense/node/config/calibration.yaml", "r") as f:
            config = yaml.safe_load(f)
        self.homography_matrix = np.array(config["H"] )
        
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
        
        # anomaly detection heuristic, Loitering
        # NOTE: alert status can only be downgraded by server
        # count is the number of people in the shed past threshold
        if count > 0:
            if max_time_stay > threshold*2:
                # time spent in shed by any 1 individual exceeds twice the threshold
                self.status["alert"] = Alert_status.High
            elif count > 3:
                # more than 3 people have spent above threshold in the shed
                self.status["alert"] = Alert_status.High
            elif self.status["alert"] != Alert_status.High:
                self.status["alert"] = Alert_status.Moderate
        # else:
        #     self.status["alert"] = Alert_status.Clear
    
    
    def cam2_bike_lot_history_update(self, detections):
        people_locations = []
        for x1, _, x2, y2, score in detections:
            xo, yo = (x2-x1)/2+x1, y2
            
            # Homography
            point = np.array([[[xo, yo]]], dtype=np.float64)
            point = cv2.perspectiveTransform(point, self.homography_matrix)
            xo, yo = point[0, 0, :]
            # Size of point
            xh1, xh2 = xo-10, xo+10
            yh1, yh2 = yo-10, yo+10           
            people_locations.append([xh1, yh1, xh2, yh2, score])
            # people_locations.append([xo, yo, score])
            
        
        if detections == []:
            people_locations = np.empty((0,5))
        else:
            people_locations = np.array(people_locations)
            

        people_predictions = self.cam2_person_tracker.update(people_locations)
        # people_predictions = []
        
        lot_index_with_people = []
        people_locations = []
        for x1, y1, x2, y2, id in people_predictions:
            cx = x1+(x2-x1)/2
            cy = y1+(y2-y1)/2
            people_locations.append([cx, cy, id])
        
            if id not in self.cam2_person_history:
                self.cam2_person_history[id] = {"time_start": time.time()}
                self.cam2_person_history[id]["coords"] = []
                
            self.cam2_person_history[id]["last_update"] = time.time()
            self.cam2_person_history[id]["coords"].append([cx, cy])
            
            # is the point in a lot?
            if self.lots is not None:
                for id in self.lots:
                    xl1, xl2 ,yl1, yl2 = self.lots[id]["coords"]
                    if (cx <= xl2) and (cx >= xl1):
                        if (cy <= yl2) and (cy >= yl1):
                            lot_index_with_people.append(id)
             
        for lot_index in lot_index_with_people:
            if lot_index in self.cam2_lot_history:
                self.cam2_lot_history[lot_index][id] += 1 
                if self.cam2_lot_history[lot_index][id] > 20:
                    self.lots[lot_index]["is_occupied"] = not self.lots[lot_index]["is_occupied"]
                    print("CHANGED!")
                    self.cam2_lot_history[lot_index][id] = -inf
                    
            else:
                self.cam2_lot_history[lot_index] = {id: 1}   
        
        print(people_locations)
        self.status["cam_2_people_locations"] = people_locations
        self.status["lot_status"] = self.lots
        
        self.cam2_anomaly_detection()
        
        # Remove old values
        for id in self.cam2_person_history.copy():
            if time.time() - self.cam2_person_history[id]["last_update"] > 60:
                self.cam2_person_history.pop(id)
    
    def cam2_anomaly_detection(self, people_locations):
        ids_found = []
        for x, y, id in people_locations:
            ids_found.append(id)
            
            history_coords = self.cam2_person_history[id]["coords"]
            prev_coords = []
            lines = []
            for coords in history_coords:
                if prev_coords == []:
                    prev_coords = coords
                    continue
                x1, y1 = prev_coords
                x2, y2 = coords
                lines.append([x2-x1, y2-y1])
            
            prev_line = []
            all_angles = []
            for line in lines:
                if prev_line == []:
                    prev_line = line
                    continue
                dot_product = line[0]*prev_line[0] + line[1]*prev_line[1]
                magnitude_prev = math.sqrt(prev_line[0]**2+prev_line[1]**2)
                magnitude_curr = math.sqrt(line[0]**2+line[1]**2)
                angle = math.degrees(math.acos(dot_product/magnitude_curr/magnitude_prev)) # Always less than 180
                all_angles.append(angle)
            # Test for erratic movement
            # high average angle and many high angles
            all_angles = np.array(all_angles)
            avg_angle = np.average(all_angles)
            if avg_angle > 135:
                self.status["alert"] = Alert_status.High
            elif avg_angle > 45 and self.status["alert"] != Alert_status.High:
                self.status["alert"] = Alert_status.Moderate
            # If more than 5 high angles
            if np.sum(all_angles>135) > 10:
                self.status["alert"] = Alert_status.High
            elif np.sum(all_angles>135) > 5 and self.status["alert"] != Alert_status.High:
                self.status["alert"] = Alert_status.Moderate
                
    
    def person_bike_matching(self, people_locations):
        for x, y, id in people_locations:
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
        
 

            
        