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
from scipy.optimize import linear_sum_assignment

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
    people_predictions = None
    person_history = {}
    people_locations = []
    
    
    # cam 1
    cam1_person_tracker = None
    cam1_bike_tracker = None
    cam_1_bike_detections = []
    cam_1_people_detections = []
    cam2_homography_matrix = None
    
    status = None
    history = {}
    lots = None

    # cam 2
    cam2_person_tracker = None
    cam_2_bike_detections = [] 
    cam_2_people_detections = [] 
    cam2_homography_matrix = None
    cam2_lot_history = {}
    
    def __init__(self):
        self.Node_MQTT_Client = MQTTPiClient()        
        # NOTE: I set people to 1 for testing
        self.status = {"people": 0, "bikes": 0, "alert": Alert_status.Clear, "cam_2_people_locations": [], "lot_status": []}
        
        self.cam1_person_tracker = Sort(max_age=10, min_hits=1, iou_threshold=0.2)
        self.cam1_bike_tracker = Sort(max_age=10, min_hits=1, iou_threshold=0.2)
        
        self.cam2_person_tracker = Sort(max_age=20, min_hits=2, iou_threshold=0)
        
        with open("/home/shedsense1/ShedSense/node/config/calibration.yaml", "r") as f:
            config = yaml.safe_load(f)
        self.cam1_homography_matrix = np.array(config["H1"] )
        self.cam2_homography_matrix = np.array(config["H2"] )
        
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler(f"/home/shedsense1/ShedSense/node/logs/{datetime.date.today()}.log")
                    
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)

          
    def cam1_update_bike_detections(self, bike_detections):
        """Update with bike detections from Camera 1

        Args:
            bike_detections (np.array): Bike detections [x,y,x,y,score]
        """
        self.cam_1_bike_detections = bike_detections
        
        # perform bike-lot assignment
        self.bike_to_lot_assignment()
                
                    
    def anomaly_detection(self):
        """Anomaly detection, loitering and erratic movement
        """
        # Anomaly detection:: loitering
        for id in self.person_history:
            if time.time()-self.person_history[id]["time_start"] > 300:
                self.status["alert"] = Alert_status.High
                self.Node_MQTT_Client.publish("ShedSense/node/alert_upgrade", f"Upgraded alert level to {self.status['alert']} due to time in shed")            
            if (time.time()-self.person_history[id]["time_start"] > 180) and (self.status["alert"]!=Alert_status.High):
                self.status["alert"] = Alert_status.Moderate
                self.Node_MQTT_Client.publish("ShedSense/node/alert_upgrade", f"Upgraded alert level to {self.status['alert']} due to time in shed")
        
        # Anomaly detection: erratic movement
        ids_found = []
        for x, y, id in self.people_locations:
            ids_found.append(id)
            
            history_coords = self.person_history[id]["coords"]
            prev_coords = []
            lines = []
            
            # Requires 3 to make an angle. If there is only 1, skip
            if len(history_coords) < 3:
                continue
            
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
            if avg_angle > 120:
                self.status["alert"] = Alert_status.High
                self.Node_MQTT_Client.publish("ShedSense/node/alert_upgrade", f"Upgraded alert level to {self.status['alert']} due to high average angle")
            elif avg_angle > 90 and self.status["alert"] != Alert_status.High:
                self.status["alert"] = Alert_status.Moderate
                self.Node_MQTT_Client.publish("ShedSense/node/alert_upgrade", f"Upgraded alert level to {self.status['alert']} due to high average angle")

            # If more than 5 high angles
            if np.sum(all_angles>90) > 5:
                self.status["alert"] = Alert_status.High
                self.Node_MQTT_Client.publish("ShedSense/node/alert_upgrade", f"Upgraded alert level to {self.status['alert']} due to many large angles")
            elif np.sum(all_angles>90) > 3 and self.status["alert"] != Alert_status.High:
                self.status["alert"] = Alert_status.Moderate
                self.Node_MQTT_Client.publish("ShedSense/node/alert_upgrade", f"Upgraded alert level to {self.status['alert']} due to many large angles")
            
    
    def bike_to_lot_assignment(self):
        """Assign bikes to bike lots
        """
        # Here starts static object detection
        if self.lots is not None:
            bike_locations = []
            
            for x1, y1, x2, y2, score in self.cam_1_bike_detections:
                xo, yo = (x2-x1)/2+x1, y2
                # Homography
                point = np.array([[[xo, yo]]], dtype=np.float64)
                point = cv2.perspectiveTransform(point, self.cam1_homography_matrix)
                xo, yo = point[0, 0, :]
                # Size of point
                xh1, xh2 = xo, xo+50
                yh1, yh2 = yo-35, yo+35           
                bike_locations.append([xh1, yh1, xh2, yh2, score])
            
            for x1, y1, x2, y2, score in self.cam_2_bike_detections:
                xo, yo = (x2-x1)/2+x1, y2
                # Homography
                point = np.array([[[xo, yo]]], dtype=np.float64)
                point = cv2.perspectiveTransform(point, self.cam2_homography_matrix)
                xo, yo = point[0, 0, :]
                # Size of point
                xh1, xh2 = xo-25, xo+25
                yh1, yh2 = yo-70, yo           
                bike_locations.append([xh1, yh1, xh2, yh2, score])
            
            # IOU as a cost matrix, for linear sum assignment
            cost_matrix = np.zeros((len(bike_locations), len(self.lots)))
            for bike_id, bike_data in enumerate(bike_locations):
                x1, y1, x2, y2, _ = bike_data
                for lot_id in self.lots:
                    a1, b1, a2, b2 = self.lots[lot_id]["coords"]
                    # Calculate IOU, these are intersection areas
                    left = max(x1, a1)
                    top = max(y1, b1)
                    right = min(x2, a2)
                    bottom = min(y2, b2)
                    
                    intersection_area = (right-left)*(bottom-top)
                    
                    bike_area = (x2-x1)*(y2-y1)
                    lot_area = (a2-a1)*(b2-b1)
                    union_area = bike_area + lot_area - intersection_area
                    
                    IOU_area = intersection_area/union_area
                    
                    cost_matrix[bike_id, lot_id] = -IOU_area

            cost_matrix[cost_matrix==0] = np.inf
            _, occupied_lots = linear_sum_assignment(cost_matrix)
            
            # Update shed state
            for id in self.lots:
                if id in occupied_lots:
                    self.lots[id]["is_occupied"] = True
                else:
                    self.lots[id]["is_occupied"] = False
            
                 
    def people_in_shed_tracking(self):
        """Tracking a person in the shed
        """
        people_locations = []
        for x1, _, x2, y2, score in self.cam_1_people_detections:
            xo, yo = (x2-x1)/2+x1, y2
            
            # Homography
            point = np.array([[[xo, yo]]], dtype=np.float64)
            point = cv2.perspectiveTransform(point, self.cam1_homography_matrix)
            xo, yo = point[0, 0, :]
            # Size of point
            xh1, xh2 = xo-20, xo+20
            yh1, yh2 = yo-20, yo+20           
            people_locations.append([xh1, yh1, xh2, yh2, score])
        
        for x1, _, x2, y2, score in self.cam_2_people_detections:
            xo, yo = (x2-x1)/2+x1, y2
            
            # Homography
            point = np.array([[[xo, yo]]], dtype=np.float64)
            point = cv2.perspectiveTransform(point, self.cam2_homography_matrix)
            xo, yo = point[0, 0, :]
            # Size of point
            xh1, xh2 = xo-20, xo+20
            yh1, yh2 = yo-20, yo+20           
            people_locations.append([xh1, yh1, xh2, yh2, score])
            # people_locations.append([xo, yo, score])
            
        
        if people_locations == []:
            people_locations = np.empty((0,5))
        else:
            people_locations = np.array(people_locations)
            

        people_predictions = self.cam2_person_tracker.update(people_locations)
        
        self.people_predictions = people_predictions
        
        people_locations = []
        for x1, y1, x2, y2, id in self.people_predictions:
            cx = x1+(x2-x1)/2
            cy = y1+(y2-y1)/2
            people_locations.append([cx, cy, id])
        
            if id not in self.person_history:
                self.person_history[id] = {"time_start": time.time()}
                self.person_history[id]["coords"] = []
                
            self.person_history[id]["last_update"] = time.time()
            self.person_history[id]["coords"].append([cx, cy])

        print(people_locations)
        self.status["people_locations"] = people_locations
        self.people_locations = people_locations        
        
    
    def cam2_bike_shed_history_update(self, ppl_detections, bike_detections):
        """Update shed state with information from Camera 2

        Args:
            ppl_detections (np.array): People detections [x, y, x, y, score]
            bike_detections (np.array): Bike detections [x, y, x, y, score]
        """
        self.logger.info(f"Number of bikes: {len(bike_detections)}")
        self.cam_2_bike_detections = bike_detections
        self.cam_2_people_detections = ppl_detections
        
        self.people_in_shed_tracking()
        self.bike_to_lot_assignment()
        
        # Status update for MQTT message
        if self.lots is None:
            self.status["lot_status"] = []
        else:
            lot_status = []
            for id in self.lots:
                lot_status.append(self.lots[id]["is_occupied"])
            self.status["lot_status"] = lot_status
        
        # Remove old values
        for id in self.person_history.copy():
            if time.time() - self.person_history[id]["last_update"] > 60:
                self.person_history.pop(id)


    def update_annotated_frame(self, frame):
        _, frame = cv2.imencode('.jpeg', frame)
        self.annotated_frame = frame.tobytes()
   
          
    def publish_shed_state(self):
        self.Node_MQTT_Client.publish("ShedSense/node/status", json.dumps(self.status))
        self.logger.info(f"Shed state: {self.status}")