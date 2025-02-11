import numpy as np
from cv2 import KalmanFilter

class Object_tracker:
    # Object tracker for a 7,4 kalman filter
    kalman_filter = None
    measurement = None
    time_since_last_update = None
    
    def __init__(self, id, bbox):
        self.kalman_filter = KalmanFilter(7, 4)
        
        # State-to-measurement matrix: how the measurements correspond to state
        self.kalman_filter.measurementMatrix = np.array([
            [1,0,0,0,0,0,0],
            [0,1,0,0,0,0,0],
            [0,0,1,0,0,0,0],
            [0,0,0,1,0,0,0]
        ])
        
        
        # State transiton matrix: constant velocity model (x_2 = x_1 + x.v)
        # NOTE: aspect ratio is assumed unchanging in the original paper, is that a right assumption?
        self.kalman_filter.transitionMatrix = np.array([   
            [1,0,0,0,1,0,0],
            [0,1,0,0,0,1,0],
            [0,0,1,0,0,0,1],
            [0,0,0,1,0,0,0],
            [0,0,0,0,1,0,0],
            [0,0,0,0,0,1,0],
            [0,0,0,0,0,0,1]])
        
        # Process noise covariance matrix: uncertainty that state equations are correct
        self.kalman_filter.processNoiseCov = np.identity(7)
        # The original paper changes this value to 0.01, with all others 1. 
        self.kalman_filter.processNoiseCov[-1,-1] *= 0.01 
        # The original paper then made the process noise for inferred values much smaller (xysize velocities)
        self.kalman_filter.processNoiseCov[4:, 4:] *= 0.01
        # The paper hence implies that the modelled state equations are pretty much perfect? Especially the one about size?
        
        # Measurement covariance matrix: noise in the measurement        
        self.kalman_filter.measurementNoiseCov = np.identity(4)
        # Original paper set size and ratio noise higher, why though?
        self.kalman_filter.measurementNoiseCov[2:, 2:] *= 10
        
        # Sate covariance matrix: uncertainty that predicted values is correct
        self.kalman_filter.errorCovPre = np.identity(7) * 10
        self.kalman_filter.errorCovPre[4:, 4:] *= 1000
        
        self.measurement = self.bbox_to_measurement(bbox)
        
        
        self.time_since_last_update = 0
        self.id = id
     
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0
        
    def bbox_to_measurement(self, bbox):
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        c_x = bbox[0] + width/2.
        c_y = bbox[1] + height/2.
        size = width*height
        ratio = width/height
        return np.array([c_x, c_y, size, ratio])
        
    
class identified_object:
    features = None
    predicted_state = None
    object_type = None
    object_id = None
    
    kalman_filter = None
    
    def __init__(self, tracker: object_tracker, bounding_box: tuple, object_type: int):
        width = bounding_box[2]-bounding_box[0]
        height = bounding_box[3]-bounding_box[1]
        
        center_x = width/2        
        center_y = height/2
        size = width * height
        aspect_ratio = width/height
        
        self.features = np.array([center_x, center_y, size, aspect_ratio])
        self.object_type = object_type
        
        self.object_id = tracker.track_object(self)
        
        self.state = self.features
        
        self.kalman_filter = KalmanFilter(self.features)    
    
        return

    def predict(self):
        self.kalman_filter.predict()
        self.kalman_filter.compute_kalman()
        
        self.predicted_state = self.kalman_filter.state
        
        return
    
    def get_predicted_box(self):
        cx, cy, size, ratio = self.predicted_state[:4]
        
        width = np.sqrt(size*ratio)
        height = size/width
        x1 = cx-width/2
        x2 = cx+width/2
        y1 = cy-height/2
        y2 = cy+height/2
        
        return (x1,x2,y1,y2)
    
    
        
    