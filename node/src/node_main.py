import threading
import queue
import argparse
import schedule
import cv2
import time
import datetime
import logging
import yaml
# import time

from Shed_state import Shed_state
from loi.detection.load_lines import load_lines
from sensors.live_feed import live_feed
from models.YOLO_model import YOLOmodel
# from utils.sort import Sort
from loi.detection.loi_detection import loi_detection
from roi.detection.roi_detection import roi_detection

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
    # shutdown_event_cam_1 = threading.Event()
    
    # camera1_thread = threading.Thread(target=live_feed, args=(shutdown_event_cam_1, recorded_path, shed_state.Node_MQTT_Client.cam_1_frame_buffer))
    # camera1_thread.start()
    camera1_borders = load_lines("test_1")
    
    # shed_state.Node_MQTT_Client.client.loop_start()
    # Camera 2 setup
    with open("/home/shedsense1/ShedSense/node/config/calibration.yaml", "r") as f:
        calibration_config = yaml.safe_load(f)
    camera_intrinsic_matrix = calibration_config["K"]
    distortion_coeff = calibration_config["D"]
    
    shutdown_event_cam_2 = threading.Event()
    
    camera2_frame_buffer = queue.Queue(maxsize=500)
    camera2_thread = threading.Thread(target=live_feed, args=(shutdown_event_cam_2, recorded_path, camera2_frame_buffer, camera_intrinsic_matrix, distortion_coeff))
    camera2_thread_start_time = None
    camera2_keep_alive_time = 0
    
    
    try:
        while True:
            schedule.run_pending()
            shed_state.Node_MQTT_Client.client.loop()
            
            # check if lots is sent from server to node
            if (shed_state.lots is None) and (shed_state.Node_MQTT_Client.lots is not None):
                shed_state.lots = {}
                for i, lot in enumerate(shed_state.Node_MQTT_Client.lots):
                    shed_state.lots[i] = {"coords": lot[:-1]}
                    if lot[-1] == (0, 0, 255):
                        shed_state.lots[i]["is_occupied": True]
                    elif lot[-1] == (0, 255, 0):
                        shed_state.lots[i]["is_occupied": False]
                    
                print(shed_state.lots)

            # Camera 1 handler
            if not shed_state.Node_MQTT_Client.cam_1_frame_buffer.empty():
                logger.info("Detection triggered")
                start = time.time()
                
                print(f"Frames left in queue: {shed_state.Node_MQTT_Client.cam_1_frame_buffer.qsize()}")
                frame = shed_state.Node_MQTT_Client.cam_1_frame_buffer.get()
                annotated_frame = loi_detection(frame=frame, model=Yolo_model, Shed_state=shed_state, borders=camera1_borders)
                
                # This would be unnecessary if not debugging (not sending annotated frames), don't have to save
                # shed_state.update_annotated_frame(annotated_frame)
                # cv2.imshow("annotate", annotated_frame)
                
                # NOTE: Responsibility of this information would primarily be shifted to camera 2
                shed_state.anomaly_detection(30) # how many frames
                
                end = time.time()
            
                logger.info(f"Time taken per frame: {end-start}")
            else:
                shed_state.history_update({}, False)
                shed_state.history_update({}, True)
                
            # Camera 2 handler
            if shed_state.status["people"] > 0 and not camera2_thread.is_alive():
                camera2_thread.start()
                logger.info("Camera 2 active")
                camera2_keep_alive_time = 0
                camera2_active_time = time.time()
            
            if not camera2_frame_buffer.empty():
                frame = camera2_frame_buffer.get()
                roi_detection(frame)
                
            if shed_state.status["people"] == 0 and camera2_thread.is_alive():
                if camera2_keep_alive_time != 0:
                    if time.time() - camera2_keep_alive_time  >= 30:
                        shutdown_event_cam_2.set()
                        logger.info(f"Camera 2 shutting down, time active: {time.time()-camera2_active_time}")
                        
                        shed_state.cam2_lot_history = {}
                else:
                    camera2_keep_alive_time = time.time()
            

    except KeyboardInterrupt:
        logger.warning("Node thread: Keyboard interrupt, releasing resources")
        # shutdown_event_cam_1.set()
        # camera1_thread.join()
        shed_state.Node_MQTT_Client.cam_1_frame_buffer.queue.clear()
        shed_state.Node_MQTT_Client.publish("ShedSense/node/shutdown", str(datetime.datetime.now().time()))
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Starts node of Pi camera")
    parser.add_argument("--cpu", help="Use CPU model (default is tflite)", action="store_true")
    parser.add_argument("--recorded", help="Use recorded video for detection", default=None)
    
    args = parser.parse_args()   
    
    # assert (args.roi or args.loi), "One of the implementations (roi or loi) must be selected"
    
    main(args.cpu, args.recorded)