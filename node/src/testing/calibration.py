import numpy as np
import cv2
import glob
import time
# from picamera2 import Picamera20-
import datetime
import yaml
from mqtt_pi import MQTTPiClient
import socket
import struct
import glob

def focus():
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 8000))
    server_socket.listen(0)
    print("Waiting for connection...")
    conn, addr = server_socket.accept()
    print("Connected by", addr)
    conn = conn.makefile('wb')
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    
    try:
        camera = Picamera2()
        camera.stop()
        cam_config = camera.create_video_configuration(main={"format": 'RGB888'})
        cam_config["controls"]["FrameRate"] = 15
        camera.configure(cam_config)

        camera.start()
        time.sleep(1)
                
        Client = MQTTPiClient()
        video = cv2.VideoWriter("calibration_test.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (1280, 720))
        while True:
            frame = camera.capture_array("main")
            
            # cv2.imshow("Focus test", frame)
            # _, frame = cv2.imencode('.jpeg', frame)
            # frame = frame.tobytes()   
            # Client.publish("ShedSense/node/frame", frame)
            
            _, img_encoded = cv2.imencode('.jpg', frame, encode_param)
            data = img_encoded.tobytes()
            size = len(data)
            conn.write(struct.pack('<L', size))
            conn.write(data)
            
            # video.write(frame)
                
            
    except KeyboardInterrupt:
        camera.stop()
        video.release()
        cv2.destroyAllWindows
    
    finally:
        conn.close()
        server_socket.close()    

def distortion_calibration():
    CHECKERBOARD = (7,7)
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1],3), np.float32)
    objp[:,:2] = np.mgrid[0:CHECKERBOARD[0],0:CHECKERBOARD[1]].T.reshape(-1,2) * 2.5
    
    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.
    
    images = glob.glob(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\ShedSense\calbration\*.png")
    print(images)
    
    count = 0 
    for i in images:
        print(count)
        count += 1
        
        img = cv2.imread(i)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)
    
        # If found, add object points, image points (after refining them)
        if ret:
            # print("FOUND!")
            objpoints.append(objp)
    
            corners2 = cv2.cornerSubPix(gray,corners, (11,11), (-1,-1), criteria)
            imgpoints.append(corners2)
    
            # Draw and display the corners
            cv2.drawChessboardCorners(img, CHECKERBOARD, corners2, ret)
            cv2.imshow('img', img)
            cv2.waitKey(500)
            # input()
    
    cv2.destroyAllWindows()
    
    print("Computing matrices...")
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
    
    print("saving...")
    with open("calibration.yaml", "w") as f:
        yaml.dump({
            "camera_matrix": mtx.tolist(),
            "dist_coeffs": dist.tolist()
        }, f)

def undistort_test():
    with open("calibration.yaml", "r") as f:
        config = yaml.safe_load(f)
    mtx = np.array(config["camera_matrix"])
    dist = np.array(config["dist_coeffs"])
    
    cap = cv2.VideoCapture(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\recordings\calibration_test.mp4") # TODO: the file path
    w,  h = 1280, 720
    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))
    video = cv2.VideoWriter("undistorted.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (1280, 720))
    
    while cap.isOpened():
        print("FRAME!")
        ret, img = cap.read()
        
        if not ret:
            break
       
        # undistort
        dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
        cv2.imshow("undistort without cropping", dst)
        print(dst.shape)
        video.write(dst)
        
        
                
        # crop the image
        x, y, w, h = roi
        dst = dst[y:y+h, x:x+w]
        # cv2.imshow("undistort without cropping", dst)
        
        
        if cv2.waitKey(1) == ord('q'):
            break
    
    video.release()    
    
    cv2.destroyAllWindows()
    cap.release()

def homography_test():
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 8000))
    server_socket.listen(0)
    print("Waiting for connection...")
    conn, addr = server_socket.accept()
    print("Connected by", addr)
    conn = conn.makefile('wb')
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    
    try:
        camera = Picamera2()
        camera.stop()
        cam_config = camera.create_video_configuration(main={"format": 'RGB888'})
        cam_config["controls"]["FrameRate"] = 15
        camera.configure(cam_config)

        camera.start()
        time.sleep(1)
                
        # Client = MQTTPiClient()
        video = cv2.VideoWriter("/home/shedsense1/Desktop/recordings/homography_test.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (1280, 720))
        while True:
            frame = camera.capture_array("main")
            video.write(frame)
            
            # cv2.imshow("Focus test", frame)
            # _, frame = cv2.imencode('.jpeg', frame)
            # frame = frame.tobytes()   
            # Client.publish("ShedSense/node/frame", frame)
            
            _, img_encoded = cv2.imencode('.jpg', frame, encode_param)
            data = img_encoded.tobytes()
            size = len(data)
            conn.write(struct.pack('<L', size))
            conn.write(data)
            
    except KeyboardInterrupt:
        camera.stop()
        video.release()
        cv2.destroyAllWindows
    
    finally:
        conn.close()
        server_socket.close()    

def fisheye_calibration():
    flags = cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC + cv2.fisheye.CALIB_CHECK_COND + cv2.fisheye.CALIB_FIX_SKEW

    # Termination criteria for cornerSubPix
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.1)

    # Board dimensions
    checkerboard = (7, 7)  # e.g., (9, 6)
    objp = np.zeros((1, checkerboard[0]*checkerboard[1], 3), np.float32)
    objp[0,:,:2] = np.mgrid[0:checkerboard[0], 0:checkerboard[1]].T.reshape(-1,2)

    objpoints = []  # 3D points
    imgpoints = []  # 2D points

    images = glob.glob(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\ShedSense\calbration\*.png")

    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, checkerboard, cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK + cv2.CALIB_CB_NORMALIZE_IMAGE)
        if ret:
            corners_refined = cv2.cornerSubPix(gray, corners, (3,3), (-1,-1), criteria)
            imgpoints.append(corners_refined)
            objpoints.append(objp)
        _img_shape = img.shape[:2]

    print("Computing matrices...")
    N_OK = len(objpoints)
    K = np.zeros((3, 3))
    D = np.zeros((4, 1))
    rvecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(N_OK)]
    tvecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(N_OK)]

    img_shape = gray.shape[::-1]
    rms, _, _, _, _ = cv2.fisheye.calibrate(
        objpoints,
        imgpoints,
        img_shape,
        K,
        D,
        rvecs,
        tvecs,
        flags,
        criteria
    )
    
    print("Found " + str(N_OK) + " valid images for calibration")
    print("DIM=" + str(_img_shape[::-1]))
    print("K=np.array(" + str(K.tolist()) + ")")
    print("D=np.array(" + str(D.tolist()) + ")")
        
    print("saving...")
    with open("calibration.yaml", "w") as f:
        yaml.dump({
            "K": K.tolist(),
            "D": D.tolist()
        }, f)

def undistort_fisheye():
    with open("calibration.yaml", "r") as f:
        config = yaml.safe_load(f)
    K = np.array(config["K"])
    D = np.array(config["D"])
    
    cap = cv2.VideoCapture(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\recordings\calibration_test.mp4") # TODO: the file path
    # w,  h = 1280, 720
    # newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))
    video = cv2.VideoWriter("undistorted.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (1280, 720))
    
    while cap.isOpened():
        print("FRAME!")
        ret, img = cap.read()
        
        if not ret:
            break
       
        # undistort
        map1, map2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), K, (1280, 720), cv2.CV_16SC2)
        dst = cv2.remap(img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        # dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
        cv2.imshow("undistort without cropping", dst)
        print(dst.shape)
        video.write(dst)
                        
        # crop the image
        # x, y, w, h = roi
        # dst = dst[y:y+h, x:x+w]
        # cv2.imshow("undistort without cropping", dst)
        
        
        if cv2.waitKey(1) == ord('q'):
            break
    
    video.release()    
    
    cv2.destroyAllWindows()
    cap.release()

# distortion_calibration()
# undistort_test()
# fisheye_calibration()
undistort_fisheye()