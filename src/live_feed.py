from picamera2 import Picamera2
import time
import argparse
from loi.detection.loi_detection import loi_detection
from roi.detection.roi_detection import roi_detection
from loi.test.draw_line import draw_line

def main(is_cpu, is_loi, img_path):   
    camera = Picamera2()
    cam_config = camera.create_video_configuration(main={"format": 'RGB888'})
    camera.configure(cam_config)

    camera.start()
    time.sleep(1)
    
    if img_path:
        draw_line(img_path)
        input()
    elif is_loi:
        loi_detection(is_cpu, camera)
    
    # else:
    #     if imgtest:
    #         roi_test(is_cpu, imgtest)
    #     else:
    #         roi_detection(is_cpu, camera)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Starts live feed of Pi camera")
    parser.add_argument("--cpu", help="Use CPU model (default is tflite)", action="store_true")
    parser.add_argument("--roi", help="Region-of-Interst implementation", action="store_true")
    parser.add_argument("--loi", help="Line-of-Interst implementation", action="store_true")
    parser.add_argument("--imgtest", help="Testing of model on provided file path")
    
    args = parser.parse_args()   
    
    assert (args.roi or args.loi), "One of the implementations (roi or loi) must be selected"   
    assert not (args.roi and args.loi), "Only one of the implementations (roi or loi) can be selected"   
    
    main(args.cpu, args.loi, args.imgtest)