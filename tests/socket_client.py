import socket
import cv2
import numpy as np
import struct
import yaml
from YOLO_model import YOLOmodel

client_socket = socket.socket()
client_socket.connect(("10.247.36.134", 8000))
# client_socket.connect(("192.168.0.164", 8000))
conn = client_socket.makefile('rb')

# camera calibration
# count = 0
# try:
#     while True:
#         packed_size = conn.read(4)
#         if not packed_size:
#             break
#         size = struct.unpack('<L', packed_size)[0]
#         data = conn.read(size)
#         frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
#         cv2.imshow('Stream', frame)
#         key = cv2.waitKey(1)
#         if key == 27:  # ESC key to exit
#             break
#         elif key == ord("s"):
#             print(f"SAVING{count}")
#             cv2.imwrite(rf"C:\Users\tanji\OneDrive\Cambridge\2\Project\ShedSense\calbration\{count}.png", frame)
#             count += 1
# finally:
#     conn.close()
#     client_socket.close()
#     cv2.destroyAllWindows()

def on_click(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDBLCLK:
        print(x, y)

def undistort_fisheye(frame, K, D):    
    scaled_K = K
    scaled_K[2][2] = 1.0
    
    K2 = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(scaled_K, D, (1280, 720), np.eye(3), balance=1)
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(scaled_K, D, np.eye(3), K2, (1280, 720), cv2.CV_16SC2)
    
    # undistort
    dst = cv2.remap(frame, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        # dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
    return dst

with open("calibration.yaml", "r") as f:
        config = yaml.safe_load(f)
K = np.array(config["K"])
D = np.array(config["D"])

source_points = np.array([[600, 295], [720, 295], [1270, 550], [5, 550]], dtype=np.float64)
destination_points = np.array([[0, 0], [740, 0], [740, 1800], [0, 1800]], dtype=np.float64)

H, status = cv2.findHomography(source_points, destination_points)
# with open("H.yaml", "w") as f:
#     yaml.dump({"H": H.tolist()}, f)

# print(H)
model = YOLOmodel(True)

try:
    while True:
        packed_size = conn.read(4)
        if not packed_size:
            break
        size = struct.unpack('<L', packed_size)[0]
        data = conn.read(size)
        frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        # cv2.imshow("Raw", frame)
        frame = undistort_fisheye(frame, K, D)

        # Detect
        result = model.detect(frame)
        detected = model.separate_objects(result)
        
        # print(detected)       
        
        top_down_img = np.ones((2000, 1000, 3), np.uint8)*255

        # Homography        
        # top_down = cv2.warpPerspective(frame, H, (1280, 720))

        
        for obj in detected:
            if obj["class_id"] != 0:
                continue
            x1, _, x2, y2  = obj["box"]
            person_floor_coords = [(x2-x1)/2+x1, y2]
            point = np.array([[person_floor_coords]], dtype=np.float64)
            point = cv2.perspectiveTransform(point, H)
            print(np.array(point[0, 0, :], dtype=int))
            
            cv2.circle(top_down_img, np.array(point[0, 0, :], dtype=int), 10, (255, 65, 137), -1)
        
        top_down_img = cv2.resize(top_down_img, (720, 1280))
        top_down_img = cv2.rotate(top_down_img, cv2.ROTATE_90_COUNTERCLOCKWISE)    
        
        cv2.imshow("Top Down", top_down_img)

        cv2.imshow('Stream', result[0].plot())
        # cv2.setMouseCallback("Stream", on_click)

        key = cv2.waitKey(1)
        if key == ord("q"):
            break
        
        
finally:
    conn.close()
    client_socket.close()
    cv2.destroyAllWindows()