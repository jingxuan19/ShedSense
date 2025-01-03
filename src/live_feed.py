from picamera2 import Picamera2
import cv2
import time
import argparse
from roi.detection.roi_detection import roi_detection

def main(is_cpu):
    camera = Picamera2()
    cam_config = camera.create_video_configuration(main={"format": 'RGB888'})
    camera.configure(cam_config)

    camera.start()
    time.sleep(1)

    roi_detection(is_cpu, camera)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Starts live feed of Pi camera")
    parser.add_argument("--cpu", help="Use CPU model (default is tflite)", action="store_true")
    args = parser.parse_args()
    
    main(args.cpu)