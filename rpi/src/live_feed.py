from picamera2 import Picamera2
import cv2
import time
import argparse
from loi.detection.loi_detection import loi_detection
from models.YOLOmodel import YOLOmodel
from loi.detection.load_lines import load_lines
from mqtt.mqtt_pi import MQTTPiClient

CAMERA_ID = "test_1"

def main(is_cpu):
    # Default to LOI implementation  
    camera = Picamera2()
    cam_config = camera.create_video_configuration(main={"format": 'RGB888'})
    camera.configure(cam_config)

    camera.start()
    time.sleep(1)
    
    #MQTT setup
    Pi_MQTT_client = MQTTPiClient("shedsense_node")
    
    # Everything concerning the region of interest (shed) can be calculated beforehand
    borders = load_lines(CAMERA_ID)
            
    # yolo_roi = masking(WINDOW_SIZE, borders)

    # Yolomodel
    Yolomodel = YOLOmodel(is_cpu)
    
    while True:
        annotated_frame = loi_detection(camera, borders, Yolomodel)
        
        payload = bytearray(annotated_frame)                
        Pi_MQTT_client.publish("shedsense/frame", payload)
        
        if cv2.waitKey(1) == ord('q'):
            break
    
    Pi_MQTT_client.disconnect()
    
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
    # parser.add_argument("--loi", help="Line-of-Interst implementation", action="store_true")
    # parser.add_argument("--imgtest", help="Testing of model on provided file path")
    
    args = parser.parse_args()   
    
    # assert (args.roi or args.loi), "One of the implementations (roi or loi) must be selected"   
    # assert not (args.roi and args.loi), "Only one of the implementations (roi or loi) can be selected"   
    
    main(args.cpu)