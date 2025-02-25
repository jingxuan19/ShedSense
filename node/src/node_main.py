import threading
import queue
import argparse
import schedule
import cv2
import time
import datetime
import logging
# import time

from Shed_state import Shed_state
from loi.detection.load_lines import load_lines
from sensors.live_feed import live_feed
from models.YOLO_model import YOLOmodel
# from utils.sort import Sort
from loi.detection.loi_detection import loi_detection

def main(is_cpu, recorded_path):
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=f"/home/shedsense1/ShedSense/node/logs/{datetime.date.today()}",
                    filemode='w')
    # logging
    logger = logging.getLogger(__name__)
    handler = logging.FileHandler(f"/home/shedsense1/ShedSense/node/logs/{datetime.date.today()}")
                    
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    # Shed Status
    shed_state = Shed_state()
    schedule.every(5).seconds.do(shed_state.publish_shed_state)
    # MQTT_Client = shed_state.Node_MQTT_Client
    
    Yolo_model = YOLOmodel(is_cpu)
    
    # Camera 1 setup    
    shutdown_event = threading.Event()
    
    camera1_frame_buffer = queue.Queue(maxsize=500)
    camera1_thread = threading.Thread(target=live_feed, args=(shutdown_event, recorded_path, camera1_frame_buffer))
    camera1_thread.start()
    camera1_borders = load_lines("test_1")
    

    try:
        while True:
            schedule.run_pending()
            # Camera 1 handler
            if not camera1_frame_buffer.empty():
                logger.info("Detection triggered")
                start = time.time()
                
                print(f"Frames left in queue: {camera1_frame_buffer.qsize()}")
                frame = camera1_frame_buffer.get()
                annotated_frame = loi_detection(frame=frame, model=Yolo_model, Shed_state=shed_state, borders=camera1_borders)
                shed_state.update_annotated_frame(annotated_frame)
                
                # cv2.imshow("annotate", annotated_frame)
                
                shed_state.anomaly_detection(30) # how many frames
                
                end = time.time()
            
                logger.info(f"Time taken per frame: {end-start}")
            else:
                shed_state.history_update({}, False)
                shed_state.history_update({}, True)

    except KeyboardInterrupt:
        logger.warning("Node thread: Keyboard interrupt, releasing resources")
        shutdown_event.set()
        camera1_thread.join()
        camera1_frame_buffer.queue.clear()
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Starts node of Pi camera")
    parser.add_argument("--cpu", help="Use CPU model (default is tflite)", action="store_true")
    parser.add_argument("--recorded", help="Use recorded video for detection", default=None)
    
    args = parser.parse_args()   
    
    # assert (args.roi or args.loi), "One of the implementations (roi or loi) must be selected"
    
    main(args.cpu, args.recorded)