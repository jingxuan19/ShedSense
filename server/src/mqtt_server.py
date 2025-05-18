from paho.mqtt import client as mqtt_client
import yaml
import logging
import datetime
import cv2
import numpy as np
import threading
import json
import time

class MQTTServerClient:
    frame = None
    annotated_frame = None
    filtered_frame = None
    history_people_locations = None
    current_people_locations = None
    
    status = None
    
    client = None
    
    reset_flag = False    
    
    def __init__(self):
        logging.basicConfig(filename=f"C:/Users/tanji/OneDrive/Cambridge/2/Project/ShedSense/server/logs/{datetime.date.today()}.log", level=logging.INFO)        
        
        self.logger = logging.getLogger(__name__)

        with open(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\ShedSense\server\config\mqtt.yaml", "r") as f:
            config = yaml.safe_load(f)
            self.broker = config["broker"]
            self.port = config["port"]
            self.config = config
        
        self.frame = None
        self.status = {}
        
        self.history_people_locations = {}
        self.current_people_locations = []
        self.lot_status = {}
        
        self.client = mqtt_client.Client()
        # self.client.tls_set(ca_certs=config["ca_cert"], certfile=config["certfile"], keyfile=config["keyfile"])
        
        # self.client.tls_set()
        # self.client.username_pw_set(username=config["username"], password=config["password"])
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message     
        self.client.on_disconnect = self.on_disconnect   
                
        self.client.connect(self.broker, self.port)        
        
    def on_connect(self, client, user_data, flags, reason_code):
        if reason_code == 0:
            self.logger.info(f"Connected to {self.broker} at port {self.port} at {datetime.datetime.now().time()}")
            print("CONNECTED!")
            for topic in self.config["to_subscribe"]:
                # print(f"subscribed to {topic}")
                self.client.subscribe(topic)   
        else:
            self.logger.warning(f"Failed to connect to {self.broker} at port {self.port} with return code {reason_code}")
            print(f"Failed to connect: return code {reason_code}")
            
    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            self.logger.warning("Disconnected. Trying to reconnect")
            try:
                self.client.reconnect()
                for topic in self.config["to_subscribe"]:
                    self.client.subscribe(topic)  
            except Exception as e:
                self.logger.info("Reconnect failed:", e)        
    
    def on_message(self, client, user_data, msg):
        # print(msg.topic)
        # print(type(msg.payload))
        if msg.topic == "ShedSense/node/frame":
            self.frame = cv2.imdecode(np.frombuffer(msg.payload, dtype=np.uint8), cv2.IMREAD_COLOR)
            self.logger.info(f"Received frame from {msg.topic} at {datetime.datetime.now().time()}")  
                     
        elif msg.topic == "ShedSense/node/status":
            self.logger.info(f"Received status: {msg.payload}")
            self.status = json.loads(msg.payload)
            self.logger.info(f"Current status at {datetime.datetime.now().time()}: {self.status}")   
            self.current_people_locations = self.status["people_locations"]
            self.lot_status = self.status["lot_status"]
                        
            for x, y, id in self.status["people_locations"]:
                if id not in self.history_people_locations:
                    self.history_people_locations[id] = {"coords": [], "timestamps": []}
                self.history_people_locations[id]["coords"].append([x, y])
                self.history_people_locations[id]["timestamps"].append(time.time())
        
        elif msg.topic == "ShedSense/node/annotated_frame":
            if len(np.frombuffer(msg.payload, dtype=np.uint8)) != 0:
                self.annotated_frame = cv2.imdecode(np.frombuffer(msg.payload, dtype=np.uint8), cv2.IMREAD_COLOR)
            self.logger.info("Received annotated frame")     
        
        elif msg.topic == "ShedSense/node/filtered_frame":
            self.filtered_frame = cv2.imdecode(np.frombuffer(msg.payload, dtype=np.uint8), cv2.IMREAD_COLOR)
            self.logger.info("Received filtered frame")     
        
        elif msg.topic == "ShedSense/node/shutdown":
            self.reset()
            self.logger.info("Reset state")
        
        # Pi_zero for debugging
        elif msg.topic == "ShedSense/pi_zero/frame":
            self.filtered_frame = cv2.imdecode(np.frombuffer(msg.payload, dtype=np.uint8), cv2.IMREAD_COLOR)
            self.logger.info(f"Received frame from {msg.topic} at {datetime.datetime.now().time()}")  
            
        elif msg.topic == "ShedSense/node/alert_upgrade":
            self.logger.info(f"Received frame from {msg.topic} at {datetime.datetime.now().time()}")  
            self.logger.warning(f"Alert level increased due to {msg.payload}")  

            
    def reset(self):
        self.frame = None
        self.annotated_frame = None
        self.filtered_frame = None
        self.status = {}
        
        self.reset_flag = True
                    
                    
    def publish(self, topic, payload):
        return_code = self.client.publish(topic, payload)
        if return_code[0] == 0:
            self.logger.info(f"Successfully sent payload to {topic} at {datetime.datetime.now().time()}")
            return 0
        
        # Problem
        self.logger.warning(f"Failed to send payload to {topic} at {datetime.datetime.now().time()}")
        return 1    
    
    def disconnect(self):
        self.client.disconnect()


    