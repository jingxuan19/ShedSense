from picamera2 import Picamera2
import time
import argparse
from loi.detection.loi_detection import loi_detection
from roi.detection.roi_detection import roi_detection

def main(is_cpu):
    camera = Picamera2()
    cam_config = camera.create_video_configuration(main={"format": 'RGB888'})
    camera.configure(cam_config)

    camera.start()
    time.sleep(1)

    if args.roi:
        roi_detection(is_cpu, camera)
    
    if args.loi:
        roi_detection(is_cpu, camera)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Starts live feed of Pi camera")
    parser.add_argument("--cpu", help="Use CPU model (default is tflite)", action="store_true")
    parser.add_argument("--roi", help="Region-of-Interst implementation", action="store_true")
    parser.add_argument("--loi", help="Line-of-Interst implementation", action="store_true")
        
    args = parser.parse_args()
    
    assert (args.roi or args.loi), "One of the implementations (roi or loi) must be selected"   
    assert not (args.roi and args.loi), "Only one of the implementations (roi or loi) can be selected"   
    
    
    main(args.cpu, args.roi, args.loi)