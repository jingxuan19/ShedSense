import threading
import queue
import argparse
import schedule
import cv2
import time
import datetime
import logging
import yaml
import numpy as np

from Shed_state import Shed_state, Alert_status
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
                    filename=f"/home/shedsense1/ShedSense/node/logs/{datetime.date.today()}.log",
                    filemode='w')
    # logging
    logger = logging.getLogger(__name__)
    handler = logging.FileHandler(f"/home/shedsense1/ShedSense/node/logs/{datetime.date.today()}.log")
                    
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    # Shed Status
    shed_state = Shed_state()
    schedule.every(1).seconds.do(shed_state.publish_shed_state)
    # MQTT_Client = shed_state.Node_MQTT_Client
    
    Yolo_model = YOLOmodel(is_cpu)
    
    # Camera 1 setup    
    camera1_borders = load_lines("test_1")

    # Camera 2 setup
    with open("/home/shedsense1/ShedSense/node/config/calibration.yaml", "r") as f:
        calibration_config = yaml.safe_load(f)
    camera_intrinsic_matrix = np.array(calibration_config["K"])
    distortion_coeff = np.array(calibration_config["D"])
    
    with open("/home/shedsense1/ShedSense/node/config/bike_lots.yaml", "r") as f:
        bike_lots_config = yaml.safe_load(f)

    if (bike_lots_config is not None) and (bike_lots_config["lots"] is not None):
        shed_state.lots = {}
        for i, lot in enumerate(bike_lots_config["lots"]):
            # print(shed_state.Node_MQTT_Client.lots)
            shed_state.lots[i] = {"coords": lot[:-1]}
            if lot[-1]:
                shed_state.lots[i]["is_occupied"] = True
            elif lot[-1]:
                shed_state.lots[i]["is_occupied"] = False
    
    shutdown_event_cam_2 = threading.Event()
    
    camera2_frame_buffer = queue.Queue(maxsize=200)
    camera2_thread = threading.Thread(target=live_feed, args=(shutdown_event_cam_2, recorded_path, camera2_frame_buffer, camera_intrinsic_matrix, distortion_coeff))
    camera2_thread_start_time = None
    camera2_keep_alive_time = 0
    
    if recorded_path is not None:
        camera2_thread.start()
    
    try:
        while True:
            schedule.run_pending()
            shed_state.Node_MQTT_Client.client.loop()
            
            # if lots are not initialised, check for updates from server
            if (shed_state.lots is None) and (shed_state.Node_MQTT_Client.lots is not None):
                shed_state.lots = {}
                for i, lot in enumerate(shed_state.Node_MQTT_Client.lots):
                    shed_state.lots[i] = {"coords": lot[:-1]}
                    if lot[-1]:
                        shed_state.lots[i]["is_occupied"] = True
                    elif lot[-1]:
                        shed_state.lots[i]["is_occupied"] = False

            # Camera 1 handler
            if not shed_state.Node_MQTT_Client.cam_1_frame_buffer.empty():
                logger.info("Detection triggered")
                start = time.time()
                
                logger.info(f"Frames left in queue: {shed_state.Node_MQTT_Client.cam_1_frame_buffer.qsize()}")
                frame = shed_state.Node_MQTT_Client.cam_1_frame_buffer.get()
                
                annotated_frame = loi_detection(frame=frame, model=Yolo_model, Shed_state=shed_state, borders=camera1_borders)
                
                end = time.time()
            
                logger.info(f"Time taken per frame: {end-start}")
                
                # Anomaly detection: Frames in buffer
                if shed_state.Node_MQTT_Client.cam_1_frame_buffer.qsize()>20:
                    shed_state.status["alert"] = Alert_status.High
                    shed_state.Node_MQTT_Client.publish("ShedSense/node/alert_upgrade", f"Upgraded alert level to {shed_state.status['alert']} due to full buffer")
                elif shed_state.Node_MQTT_Client.cam_1_frame_buffer.qsize()>10:
                    if shed_state.status["alert"] != Alert_status.High:
                        shed_state.status["alert"] = Alert_status.Moderate
                        shed_state.Node_MQTT_Client.publish("ShedSense/node/alert_upgrade", f"Upgraded alert level to {shed_state.status['alert']} due to almost full buffer")       
            else:
                # reset and update with empty detections
                shed_state.cam1_person_tracker.update(np.empty((0,5)))
                shed_state.cam1_person_tracker.update(np.empty((0,5)))
                shed_state.cam_1_people_detections = []
                
            # Camera 2 handler
            # If people in the shed and the thread did not start, start thread
            if shed_state.status["people"] > 0 and not camera2_thread.is_alive():
                camera2_thread.start()
                logger.info("Camera 2 active")
                camera2_keep_alive_time = 0
                camera2_thread_start_time = time.time()
            
            if not camera2_frame_buffer.empty():
                frame = camera2_frame_buffer.get()
                annotated_frame = roi_detection(frame, Yolo_model, shed_state)
                
                # if lots not initialised, send frame to server
                if shed_state.lots is None:
                    _, payload = cv2.imencode('.jpeg', frame)
                    shed_state.Node_MQTT_Client.publish("ShedSense/node/frame", payload.tobytes())
            else:
                # reset and update with empty detections
                shed_state.cam_2_people_detections = []
                shed_state.cam1_person_tracker.update(np.empty((0,5)))

            # If nobody in the shed, stop thread                
            if shed_state.status["people"] == 0 and camera2_thread.is_alive():
                if camera2_keep_alive_time != 0:
                    if time.time() - camera2_keep_alive_time  >= 30:
                        shutdown_event_cam_2.set()
                        logger.info(f"Camera 2 shutting down, time active: {time.time()-camera2_thread_start_time}")
                        
                        shed_state.cam2_lot_history = {}
                        camera2_thread = threading.Thread(target=live_feed, args=(shutdown_event_cam_2, recorded_path, camera2_frame_buffer, camera_intrinsic_matrix, distortion_coeff))
                        
                else:
                    camera2_keep_alive_time = time.time()
            
            # Anomaly detection on current state
            shed_state.anomaly_detection()
    except KeyboardInterrupt:
        logger.warning("Node thread: Keyboard interrupt, releasing resources")
        shutdown_event_cam_2.set()
        shed_state.Node_MQTT_Client.cam_1_frame_buffer.queue.clear()
        shed_state.Node_MQTT_Client.publish("ShedSense/node/shutdown", str(datetime.datetime.now().time()))
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Starts node of Pi camera")
    parser.add_argument("--cpu", help="Use CPU model (default is tflite)", action="store_true")
    parser.add_argument("--recorded", help="Use recorded video for detection", default=None)
    
    args = parser.parse_args()   
    
    # assert (args.roi or args.loi), "One of the implementations (roi or loi) must be selected"
    
    main(args.cpu, args.recorded)