import numpy as np
import cv2
import yaml

TOLERANCE = 100

def get_bounds(Line, frame_bounds):
    # line coords are in (x,y)
    bounds_x = []
    bounds_y = []
    
    bounds_y.append(Line.pt1[1]-TOLERANCE)
    bounds_y.append(Line.pt1[1]+TOLERANCE)      
    bounds_y.append(Line.pt2[1]-TOLERANCE)
    bounds_y.append(Line.pt2[1]+TOLERANCE)      
    bounds_x.append(Line.pt1[0]-TOLERANCE)
    bounds_x.append(Line.pt1[0]+TOLERANCE)           
    bounds_x.append(Line.pt2[0]-TOLERANCE)
    bounds_x.append(Line.pt2[0]+TOLERANCE)      
    
    min_x = min(bounds_x)
    if min_x < 0:
        min_x = 0    
    max_x = max(bounds_x)
    if max_x > frame_bounds[1]:
        max_x = frame_bounds[1]    
    
    min_y = min(bounds_y)
    if min_y < 0:
        min_y = 0    
    max_y = max(bounds_y)
    if max_y > frame_bounds[0]:
        max_y = frame_bounds[0]
    
    return (min_x, min_y), (max_x, max_y)
    

def masking(window_size, borders):   
    # mask is (y,x)
    mask = np.zeros(window_size, dtype=np.int8)
    
    for Line in borders:
        rect_1, rect_2 = get_bounds(Line, window_size)
        cv2.rectangle(mask, rect_1, rect_2, 255, -1)
        
    return mask
            
            
