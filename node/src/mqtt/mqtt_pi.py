from paho.mqtt import client as mqtt_client
import yaml
import logging
import datetime
import cv2
import threading
import numpy as np
import queue
import json

# TODO: Autoreconnect, polish up code for server and pi for multiple topics subscription, message handler

class MQTTPiClient:    
    cam_1_frame_buffer = queue.Queue(maxsize=200)
    
    lots = None
    
    def __init__(self):       
        self.logger = logging.getLogger(__name__)
        self.handler = logging.FileHandler(f"/home/shedsense1/ShedSense/node/logs/{datetime.date.today()}.log")
        
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)
        
        with open("/home/shedsense1/ShedSense/node/config/mqtt.yaml", "r") as f:
            config = yaml.safe_load(f)
            self.config = config
            self.broker = config["broker"]
            self.port = config["port"]
                
        self.client = mqtt_client.Client()
        self.client.tls_set(ca_certs=config["ca_cert"], certfile=config["cert_file"], keyfile=config["key"])
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        self.client.connect(self.broker, self.port)
        
        for topic in config["to_subscribe"]:
            self.client.subscribe(topic)   
        
        
    def process_messages(self, msg):
        if msg.topic == "ShedSense/server/initialise_lots":
            self.lots = json.loads(msg.payload)
            self.logger.info(f"Recevied lots: {self.lots} at {datetime.datetime.now().time()}")  

        elif msg.topic == "ShedSense/pi_zero/frame":
            if self.cam_1_frame_buffer.full():
                self.cam_1_frame_buffer.get()
            frame = cv2.imdecode(np.frombuffer(msg.payload, dtype=np.uint8), cv2.IMREAD_COLOR)
            self.cam_1_frame_buffer.put(frame)
            self.logger.info(f"Received frame from pi zero at {datetime.datetime.now().time()}")
        
    # Handlers    
    def on_connect(self, client, user_data, flags, reason_code):
        if reason_code == 0:
            self.logger.info(f"Connected to {self.broker} at port {self.port} at {datetime.datetime.now().time()}")
            print("CONNECTED!")
        else:
            self.logger.warning(f"Failed to connect to {self.broker} at port {self.port} with return code {reason_code}")
            print(f"Failed to connect: return code {reason_code}")
        
        
    def on_message(self, client, user_data, msg):
        threading.Thread(target=self.process_messages, args=(msg,)).start()


    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            self.logger.warning("Disconnected. Trying to reconnect")
            try:
                self.client.reconnect()
                for topic in self.config["to_subscribe"]:
                    self.client.subscribe(topic)  
            except Exception as e:
                self.logger.info("Reconnect failed:", e)
     
    # Public methods 
    def publish(self, topic, payload):
        return_code = self.client.publish(topic, payload)
        if return_code[0] == 0:
            self.logger.info(f"Successfully sent payload to {topic} at {datetime.datetime.now().time()}")
            return 0
        
        # Problem
        self.logger.warning(f"Failed to send payload to {topic}")
        return 1    
    
    
    def disconnect(self):
        self.client.disconnect()
        self.logger.warning("MQTT Disconnected")


