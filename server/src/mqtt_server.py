from paho.mqtt import client as mqtt_client
import yaml
import logging
import datetime
import cv2
import numpy as np

class MQTTServerClient:
    frame = None
    status = None
    
    client = None
    
    def __init__(self):
        logging.basicConfig(filename=f"C:/Users/tanji/OneDrive/Cambridge/2/Project/ShedSense/server/logs/{datetime.date.today()}_mqttlogging", level=logging.INFO)        
        
        self.logger = logging.getLogger(__name__)

        with open(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\ShedSense\server\config\mqtt.yaml", "r") as f:
            config = yaml.safe_load(f)
            self.broker = config["broker"]
            self.port = config["port"]
        
        self.frame = None
        self.status = None
                
        self.client = mqtt_client.Client()
        self.client.tls_set(ca_certs=config["ca_cert"], certfile=config["certfile"], keyfile=config["keyfile"])
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message        
                
        self.client.connect(self.broker, self.port)
        self.client.subscribe("shedsense/node/frame")    
        self.client.subscribe("shedsense/node/status") 
        
        
    def on_connect(self, client, user_data, flags, reason_code):
        if reason_code == 0:
            self.logger.info(f"Connected to {self.broker} at port {self.port} at {datetime.datetime.now().time()}")
            print("CONNECTED!")
        else:
            self.logger.warning(f"Failed to connect to {self.broker} at port {self.port} with return code {reason_code}")
            print(f"Failed to connect: return code {reason_code}")
            
    def on_message(self, client, user_data, msg):
        print("RECEIVED")
        # print(type(msg.payload))
        if msg.topic == "shedsense/node/frame":
            self.frame = cv2.imdecode(np.frombuffer(msg.payload, dtype=np.uint8), cv2.IMREAD_COLOR)
        elif msg.topic == "shedsense/node/status":
            self.status = msg.payload        
                    
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


    