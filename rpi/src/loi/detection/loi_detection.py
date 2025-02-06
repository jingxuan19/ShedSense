import cv2
import numpy as np
import logging
import datetime
from loi.detection.temporal_tracking.tracking_history import Tracking_history
from loi.detection.Border import Flow_status
# import yaml
# from loi.detection.masking import masking
# from loi.detection.load_lines import load_lines
# import math
         
logger = logging.getLogger("LOI detection")
handler = logging.FileHandler(f"/home/shedsense1/ShedSense/rpi/logs/detection/{datetime.date.today()}_loidetection")
       
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def loi_detection(camera, borders, model, person_tracker, bike_tracker):   
    frame = camera.capture_array("main")   
    # print(frame.shape)
            
    result = model.detect(frame)
    detected_objects = model.separate_objects(result) # box, score, class_id, class_name
    
    person_detections = []
    bike_detections = []
    for det_obj in detected_objects:       
        if det_obj['class_id'] == 0:
            person_detections.append(det_obj['box'].numpy().tolist()+[det_obj['score'].numpy().item()])
        elif det_obj['class_id'] == 1:
            bike_detections.append(det_obj['box'].numpy().tolist()+[det_obj['score'].numpy().item()])
    
    if not person_detections:
        person_detections = np.empty((0,5))
    else:
        person_detections = np.array(person_detections)
    
    if not bike_detections:
        bike_detections = np.empty((0,5))
    else:
        bike_detections = np.array(bike_detections)

    person_predictions = person_tracker.update(person_detections)
    bike_predictions = bike_tracker.update(bike_detections)

    # frame = result[0].plot()
    person_measured = {}
    bike_measured = {}
    
    for p in person_predictions:
        c_x = p[0]+(p[2] - p[0])/2
        c_y = p[1]+(p[3] - p[1])/2
        person_measured[p[-1]*2] = np.array([c_x, c_y]) # person_id will be even wrt the Tracking history
        
        int_p = p.astype(np.int64)
        frame = cv2.rectangle(frame, (int_p[0], int_p[1]), (int_p[2], int_p[3]), (36, 255, 12), 1)
        cv2.putText(frame, f"person id:{str(int_p[-1])}", (int_p[0], int_p[1]+10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
        
    for p in bike_predictions:
        c_x = p[0]+(p[2] - p[0])/2
        c_y = p[1]+(p[3] - p[1])/2
        bike_measured[p[-1]*2+1] = np.array([c_x, c_y]) # bike_id will be odd wrt the Tracking history
                        
        int_p = p.astype(np.int64)
        frame = cv2.rectangle(frame, (int_p[0], int_p[1]), (int_p[2], int_p[3]), (36, 255, 12), 1)
        cv2.putText(frame, f"bike id:{str(int_p[-1])}", (int_p[0], int_p[1]+10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)  
               
    for id in Tracking_history.history:
        if id in person_measured:            
            for b in borders:
                flow_status = b.intersect(np.concatenate((Tracking_history.history[id]["center"], person_measured[id])))
                if flow_status is Flow_status.IN:
                    logger.info("Detected person entering bike shed")
                    Tracking_history.person_in += 1
                elif flow_status is Flow_status.OUT:
                    logger.info("Detected person leaving bike shed")
                    if Tracking_history.person_in > 0:
                        Tracking_history.person_in -= 1
                    else:
                        logger.warning("Detected negative person occupancy")
                else:
                    cv2.line(frame, Tracking_history.history[id]["center"].astype(np.int64), person_measured[id].astype(np.int64), (255, 0, 0), 2)
                    logger.info("Detected person, but did not enter or leave")
        
        elif id in bike_measured:            
            for b in borders:
                flow_status = b.intersect(np.concatenate((Tracking_history.history[id]["center"], bike_measured[id])))
                if flow_status is Flow_status.IN:
                    logger.info(f"Detected bike entering bike shed")
                    Tracking_history.bike_in += 1
                elif flow_status is Flow_status.OUT:
                    logger.info(f"Detected bike leaving bike shed")
                    if Tracking_history.bike_in > 0:
                        Tracking_history.bike_in -= 1
                    else:
                        logger.warning(f"Detected negative bike occupancy")     
                else:
                    cv2.line(frame, Tracking_history.history[id]["center"].astype(np.int64), bike_measured[id].astype(np.int64), (255, 0, 0), 2)
                    logger.info("Detected bike, but did not enter or leave")         

    Tracking_history.update(person_measured)
    Tracking_history.update(bike_measured)
    
    cv2.putText(frame, f"person: {Tracking_history.person_in}", (0,50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 3)  
        
    return frame
    
    
