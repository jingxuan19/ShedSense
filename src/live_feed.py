from picamera2 import Picamera2
import cv2
import time
import argparse
from loi.detection.loi_detection import loi_detection
from models.YOLOmodel import YOLOmodel
import yaml
from loi.detection.load_lines import load_lines


def main(is_cpu, is_loi, img_path):   
    camera = Picamera2()
    cam_config = camera.create_video_configuration(main={"format": 'RGB888'})
    camera.configure(cam_config)

    camera.start()
    time.sleep(1)
    
    #MQTT setup
    
    
    # LOI IMPLEMENTATION
    with open("") as f:
        config = yaml.load(f)
        LOCATION = config["location"]
        WINDOW_SIZE = config["window_size"]
        
            
    # Everything concerning the region of interest (shed) can be calculated beforehand
    borders = load_lines(LOCATION)
            
    # yolo_roi = masking(WINDOW_SIZE, borders)

    # Yolomodel
    Yolomodel = YOLOmodel(is_cpu)
    
    while True:
        loi_detection(camera, borders, WINDOW_SIZE, Yolomodel)
        if cv2.waitKey(1) == ord('q'):
            break
    
    
    # if img_path:
    #     draw_line(img_path)
    #     input()
    # elif is_loi:
    #     loi_detection(is_cpu, camera)
    
    # ROI IMPLEMENTATION DEPRACATED
    # else:
    #     if imgtest:
    #         roi_test(is_cpu, imgtest)
    #     else:
    #         roi_detection(is_cpu, camera)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Starts live feed of Pi camera")
    parser.add_argument("--cpu", help="Use CPU model (default is tflite)", action="store_true")
    # parser.add_argument("--roi", help="Region-of-Interst implementation", action="store_true")
    parser.add_argument("--loi", help="Line-of-Interst implementation", action="store_true")
    parser.add_argument("--imgtest", help="Testing of model on provided file path")
    
    args = parser.parse_args()   
    
    assert (args.roi or args.loi), "One of the implementations (roi or loi) must be selected"   
    assert not (args.roi and args.loi), "Only one of the implementations (roi or loi) can be selected"   
    
    main(args.cpu, args.loi, args.imgtest)