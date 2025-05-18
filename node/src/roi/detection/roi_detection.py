import cv2
import numpy as np

def roi_detection(frame, model, Shed_state):
    """Perform ROI detection of a static frame. The function should be able to determine which lot is taken.
        Functionality for occupancy and anomaly detection should also be used.

    Args:
        frame (np.array): Frame captured by camera
        model (YOLOModel): Model for object detection
        Shed_state (ShedState): Shed object 
    """
    
    result = model.detect(frame)
    detected_objects = model.separate_objects(result) # box, score, class_id, class_name
    
    # Clean detections    
    person_detections = []
    bike_detections = []
    for det_obj in detected_objects:
        x1, y1, x2, y2 = det_obj['box'].numpy().tolist()
        if det_obj["class_id"] == 0:
            person_detections.append([x1, y1, x2, y2, det_obj['score'].numpy().item()])
        elif det_obj["class_id"] == 1:
            bike_detections.append([x1, y1, x2, y2, det_obj['score'].numpy().item()])
    
    Shed_state.cam2_bike_shed_history_update(person_detections, bike_detections)

    return result[0].plot()