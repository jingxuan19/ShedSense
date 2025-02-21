from paho.mqtt import client as mqtt_client
import yaml
import logging
import datetime

# TODO: Autoreconnect, polish up code for server and pi for multiple topics subscription, message handler

class MQTTPiClient:    
    subscribed_msg = None
    
    def __init__(self):       
        self.logger = logging.getLogger("MQTT")
        self.handler = logging.FileHandler(f"/home/shedsense1/ShedSense/node/logs/mqtt/{datetime.date.today()}_mqttlogging")
        
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)
        
        with open("/home/shedsense1/ShedSense/node/config/mqtt.yaml", "r") as f:
            config = yaml.safe_load(f)
            self.broker = config["broker"]
            self.port = config["port"]
                
        self.client = mqtt_client.Client()
        self.client.tls_set(ca_certs=config["ca_cert"], certfile=config["cert_file"], keyfile=config["key"])
        self.client.on_connect = self.on_connect
        
        self.client.connect(self.broker, self.port)
        
    def on_connect(self, client, user_data, flags, reason_code):
        if reason_code == 0:
            self.logger.info(f"Connected to {self.broker} at port {self.port} at {datetime.datetime.now().time()}")
            print("CONNECTED!")
        else:
            self.logger.warning(f"Failed to connect to {self.broker} at port {self.port} with return code {reason_code}")
            print(f"Failed to connect: return code {reason_code}")
        
    def on_message(self, client, user_data, msg):
        print("RECEIVED")
        self.subscribed_msg = msg.payload
     
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


