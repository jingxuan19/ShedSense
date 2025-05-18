import cv2
import numpy as np
import logging
import datetime
# from loi.detection.temporal_tracking.tracking_history import Tracking_history
from loi.detection.Border import Flow_status
# import yaml
# from loi.detection.masking import masking
# from loi.detection.load_lines import load_lines
# import math
         
logger = logging.getLogger(__name__)
handler = logging.FileHandler(f"/home/shedsense1/ShedSense/node/logs/{datetime.date.today()}")
       
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def loi_detection(frame, model, Shed_state, borders):
    # Detection via model
    result = model.detect(frame)
    detected_objects = model.separate_objects(result) # box, score, class_id, class_name
    
    # Split detections into classes
    person_detections = []
    bike_detections = []
    for det_obj in detected_objects:       
        if det_obj['class_id'] == 0:
            person_detections.append(det_obj['box'].numpy().tolist()+[det_obj['score'].numpy().item()])
        elif det_obj['class_id'] == 1:
            bike_detections.append(det_obj['box'].numpy().tolist()+[det_obj['score'].numpy().item()])
    
    # Update shed state
    Shed_state.cam1_update_bike_detections(bike_detections)
    
    # Prepare data for tracking
    if not person_detections:
        person_detections = np.empty((0,5))
    else:
        person_detections = np.array(person_detections)
    
    if not bike_detections:
        bike_detections = np.empty((0,5))
    else:
        bike_detections = np.array(bike_detections)

    # Object tracking
    person_predictions = Shed_state.cam1_person_tracker.update(person_detections)
    bike_predictions = Shed_state.cam1_bike_tracker.update(bike_detections)

    # Find centers of predicted bounding boxes
    person_measured = {}
    bike_measured = {}
    
    for p in person_predictions:
        c_x = p[0]+(p[2] - p[0])/2
        c_y = p[1]+(p[3] - p[1])/2
        person_measured[p[-1]*2] = np.array([c_x, c_y]) # person_id will be even wrt the Tracking history
        
        # Draw and label object
        int_p = p.astype(np.int64)
        frame = cv2.rectangle(frame, (int_p[0], int_p[1]), (int_p[2], int_p[3]), (36, 255, 12), 1)
        cv2.putText(frame, f"person id:{str(int_p[-1])}", (int_p[0], int_p[1]+10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
        
    for p in bike_predictions:
        c_x = p[0]+(p[2] - p[0])/2
        c_y = p[1]+(p[3] - p[1])/2
        bike_measured[p[-1]*2+1] = np.array([c_x, c_y]) # bike_id will be odd wrt the Tracking history
                        
        # Draw and label object
        int_p = p.astype(np.int64)
        frame = cv2.rectangle(frame, (int_p[0], int_p[1]), (int_p[2], int_p[3]), (36, 255, 12), 1)
        cv2.putText(frame, f"bike id:{str(int_p[-1])}", (int_p[0], int_p[1]+10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)  

    # Check for line-of-interest crossing
    for id in Shed_state.history:
        if id in person_measured:
            cv2.line(frame, Shed_state.history[id]["center"].astype(np.int64), person_measured[id].astype(np.int64), (255, 0, 0), 2)            
            for b in borders:
                flow_status = b.intersect(np.concatenate((Shed_state.history[id]["center"], person_measured[id])))
                if flow_status is Flow_status.IN:
                    logger.info("Detected person entering bike shed")
                    Shed_state.status["people"] += 1
                elif flow_status is Flow_status.OUT:
                    logger.info("Detected person leaving bike shed")
                    if Shed_state.status["people"] > 0:
                        Shed_state.status["people"] -= 1
                    else:
                        logger.warning("Detected negative person occupancy")
        
        elif id in bike_measured:            
            cv2.line(frame, Shed_state.history[id]["center"].astype(np.int64), bike_measured[id].astype(np.int64), (255, 0, 0), 2)            
            for b in borders:
                flow_status = b.intersect(np.concatenate((Shed_state.history[id]["center"], bike_measured[id])))
                if flow_status is Flow_status.IN:
                    logger.info("Detected bike entering bike shed")
                    Shed_state.status["bikes"] += 1
                    Shed_state.bike_in_flag = True
                elif flow_status is Flow_status.OUT:
                    logger.info("Detected bike leaving bike shed")
                    if Shed_state.status["bikes"] > 0:
                        Shed_state.status["bikes"] -= 1
                    else:
                        Shed_state.logger.warning("Detected negative bike occupancy")          

    # Update shed state
    Shed_state.history_update(person_measured, False)
    Shed_state.history_update(bike_measured, True)

    return frame
