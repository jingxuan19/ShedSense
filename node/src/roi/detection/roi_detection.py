import cv2
import numpy as np

def roi_detection(frame, model, Shed_state):
    """Perform ROI detection of a static frame. The function should be able to determine which lot is taken.
        Functionality for occupancy and anomaly detection should also be used.

    Args:
        frame (_type_): _description_
        model (_type_): _description_
        Shed_state (_type_): _description_
        borders (_type_): _description_
    """
    # print(model)    
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

    person_predictions = Shed_state.person_tracker.update(person_detections)
    bike_predictions = Shed_state.bike_tracker.update(bike_detections)

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
    

# def roi_detection(is_cpu: bool, camera):
#     Yolomodel = YOLOmodel(is_cpu)

#     while True:
#         # frame = camera.capture_array("main")       
#         frame = cv2.imload(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\ShedSense\data\photo_2025-01-23_09-21-25.jpg")
#         result = Yolomodel.detect(frame)   
        
#         cv2.imshow("ROI implementation", result[0].plot())

#         detected_objects = Yolomodel.separate_objects(result) # boxes, score, class_id, class_name
#         bikes = 0
#         people = 0
#         for detected in detected_objects:
#             if detected["class_id"] == 0:
#                 people += 1
#             elif detected["class_id"] == 1:
#                 bikes += 1

#         print(f"number of bikes: {bikes}")
#         print(f"number of people: {people}")
        
#         if cv2.waitKey(1) == ord('q'):
#             break
        
# roi_detection(False, None)