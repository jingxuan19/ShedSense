import threading
import queue
import argparse
import schedule
# import time

from Shed_state import Shed_state
from src.loi.detection.load_lines import load_lines
from src.sensors.live_feed import live_feed
from src.models.YOLO_model import YOLOmodel
# from utils.sort import Sort
from src.loi.detection.loi_detection import loi_detection

def main(is_cpu):
    shed_state = Shed_state()
    schedule.every().minute.do(shed_state.publish_state())
    # MQTT_Client = shed_state.Node_MQTT_Client
    
    Yolo_model = YOLOmodel(is_cpu)
    
    # Camera 1 setup    
    camera1_frame_buffer = queue.Queue()
    camera1_thread = threading.Thread(live_feed, args=(None, camera1_frame_buffer))
    camera1_thread.start()
    camera1_borders = load_lines("test_1")
    

    while True:
        # Camera 1 handler
        if not camera1_frame_buffer.empty():
            frame = camera1_frame_buffer.get()
            frame = loi_detection(frame, camera1_borders, Yolo_model, camera1_borders)
            shed_state.anomaly_detection(300) # how many frames          
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Starts node of Pi camera")
    parser.add_argument("--cpu", help="Use CPU model (default is tflite)", action="store_true")
    
    args = parser.parse_args()   
    
    # assert (args.roi or args.loi), "One of the implementations (roi or loi) must be selected"
    
    main(args.cpu)