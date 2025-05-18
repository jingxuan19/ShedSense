import cv2
import numpy as np
# from ultralytics import YOLO

cap = cv2.VideoCapture(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\recordings\2025-02-26_14-38-06.mp4")
timestamps = [cap.get(cv2.CAP_PROP_POS_MSEC)]

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

filter_out = cv2.VideoWriter(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\recordings\Detections\02-26_filter.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (width, height))
filter_raw = cv2.VideoWriter(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\recordings\Detections\02-26_filter_raw.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (width, height))
raw_out = cv2.VideoWriter(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\recordings\Detections\02-26_raw.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (width, height))


prev_frame_grey = None
wakeup_time_left = 0

frame_num = 1
while cap.isOpened():
    ret, frame =  cap.read()
    if not ret:
        break
    
    frame_grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
    if prev_frame_grey is None:
        prev_frame_grey = frame_grey   
    
    frame_difference = cv2.absdiff(prev_frame_grey, frame_grey)
    
    _, filter_frame = cv2.threshold(frame_difference, 30, 255, cv2.THRESH_BINARY)
    
    pixels_changed = np.sum(filter_frame)/255



    # print(timestamps)
    
    if pixels_changed > 5000:
        filter_frame = cv2.cvtColor(filter_frame, cv2.COLOR_GRAY2BGR)
        filter_raw.write(filter_frame)
        
        cv2.putText(filter_frame, f"pixels: {int(pixels_changed)}", (0,25), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 3)  
        cv2.putText(filter_frame, f"{frame_num}", (width-100,25), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 3)
        cv2.imshow("Filtered", filter_frame)
    
        cv2.putText(frame, f"{frame_num}", (width-100,25), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 3)
        frame_num += 1
        
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
filter_raw.release()