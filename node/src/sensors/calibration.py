import numpy as np
import cv2
import glob
import time
from picamera2 import Picamera2
import datetime
import yaml

def focus():
    try:
        camera = Picamera2()
        camera.stop()
        cam_config = camera.create_video_configuration(main={"format": 'RGB888'})
        cam_config["controls"]["FrameRate"] = 15
        camera.configure(cam_config)

        camera.start()
        time.sleep(1)
        
        # Client = MQTTPiClient()
        video = cv2.VideoWriter("/home/shedsense1/Desktop/recordings/calibration_test.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (1280, 720))
        while True:
            frame = camera.capture_array("main")
            video.write(frame)
            
            cv2.imshow("Focus test", frame)
        #     _, frame = cv2.imencode('.jpeg', frame)
        #     frame = frame.tobytes()   

        #     Client.publish("ShedSense/node/frame", frame)
    except KeyboardInterrupt:
        camera.stop()
        video.release()
        cv2.destroyAllWindows

def distortion_calibration():
    CHECKERBOARD = (7,7)
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1],3), np.float32)
    objp[:,:2] = np.mgrid[0:CHECKERBOARD[0],0:CHECKERBOARD[1]].T.reshape(-1,2)
    
    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.
    
    cap = cv2.VideoCapture() # TODO: the file path
    success, img = cap.read()
    
    while success:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)
    
        # If found, add object points, image points (after refining them)
        if ret:
            objpoints.append(objp)
    
            corners2 = cv2.cornerSubPix(gray,corners, (11,11), (-1,-1), criteria)
            imgpoints.append(corners2)
    
            # Draw and display the corners
            cv2.drawChessboardCorners(img, (7,6), corners2, ret)
            cv2.imshow('img', img)
            cv2.waitKey(500)
    
    cv2.destroyAllWindows()
    cap.release()
    
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
    with open("calibration.yaml", "w") as f:
        yaml.dump({
            "camera_matrix": mtx.tolist(),
            "dist_coeffs": dist.tolist()
        }, f)

def undistort_test():
    with open("calibration.yaml", "r") as f:
        config = yaml.safe_load(f)
    mtx = config["camera_matrix"]
    dist = config["dist_coeff"]
    
    cap = cv2.VideoCapture() # TODO: the file path
    success, img = cap.read()
    h,  w = img.shape[:2]
    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))
    video = cv2.VideoWriter("/home/shedsense1/Desktop/recordings/undistortion_test.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (w, h))
    
    while success:
        # undistort
        dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
        cv2.imshow("undistort without cropping", dst)
                
        # crop the image
        x, y, w, h = roi
        dst = dst[y:y+h, x:x+w]
        video.write(dst)
    
    cv2.destroyAllWindows()
    cap.release()
    video.release()
    