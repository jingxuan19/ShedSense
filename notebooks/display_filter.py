import cv2
import numpy as np
# from ultralytics import YOLO

cap = cv2.VideoCapture(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\recordings\2025-02-26_14-38-06.mp4")
timestamps = [cap.get(cv2.CAP_PROP_POS_MSEC)]

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

filter_out = cv2.VideoWriter(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\recordings\Detections\02-26_f.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (width, height))
raw_out = cv2.VideoWriter(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\recordings\Detections\02-26_r.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (width, height))


prev_frame_grey = None
wakeup_time_left = 0

while cap.isOpened():
    ret, frame =  cap.read()
    if not ret:
        break
    
    frame_grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
    if prev_frame_grey is None:
        prev_frame_grey = frame_grey   
    
    frame_difference = cv2.absdiff(prev_frame_grey, frame_grey)
    
    _, filter_frame = cv2.threshold(frame_difference, 30, 255, cv2.THRESH_BINARY)
    
    cv2.imshow("Filtered", filter_frame)
        
    pixels_changed = np.sum(filter_frame)/255

    # print(timestamps)
    
    if pixels_changed > 5000:
        raw_out.write(frame)
        filter_out.write(filter_frame)
        timestamps.append(cap.get(cv2.CAP_PROP_POS_MSEC))
    
    prev_frame_grey = frame_grey
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

with open("timestamps.txt", "w") as f:
    print(len(timestamps))
    f.write(str(timestamps))
    
cap.release()
raw_out.release()
filter_out.release()