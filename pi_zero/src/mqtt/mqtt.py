from paho.mqtt import client as mqtt_client
import yaml
import logging
import datetime

# TODO: Autoreconnect, polish up code for server and pi for multiple topics subscription, message handler

DEVICE = "pi_zero"

class MQTTPiClient:    
    broker = None
    port = None
    
    client = None
        
    def __init__(self):       
        self.logger = logging.getLogger(__name__)
        self.handler = logging.FileHandler(f"/home/shedsense2/ShedSense/{DEVICE}/logs/{datetime.date.today()}")
        
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)
        
        with open(f"/home/shedsense2/ShedSense/{DEVICE}/config/mqtt.yaml", "r") as f:
            config = yaml.safe_load(f)
            self.broker = config["broker"]
            self.port = config["port"]
                
        self.client = mqtt_client.Client()
        # self.client.tls_set(ca_certs=config["ca_cert"], certfile=config["cert_file"], keyfile=config["key"])
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        self.client.connect(self.broker, self.port)
        
        # for topic in config["to_subscribe"]:
        #     self.client.subscribe(topic)   
        
    def on_connect(self, client, user_data, flags, reason_code):
        if reason_code == 0:
            self.logger.info(f"Connected to {self.broker} at port {self.port} at {datetime.datetime.now().time()}")
            print("CONNECTED!")
        else:
            self.logger.warning(f"Failed to connect to {self.broker} at port {self.port} with return code {reason_code}")
            print(f"Failed to connect: return code {reason_code}")
        
    def on_message(self, client, user_data, msg):
        print("RECEIVED")
        
    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            self.logger.warning("Disconnected. Trying to reconnect")
            try:
                self.client.reconnect()
            except Exception as e:
                self.logger.info("Reconnect failed:", e)

    def publish(self, topic, payload):
        return_code = self.client.publish(topic, payload)
        if return_code[0] == 0:
            self.logger.info(f"Successfully sent payload to {topic}")
            print("PUBLISH")
            return 0
        
        # Problem
        self.logger.warning(f"Failed to send payload to {topic}")
        return 1    
    
    def disconnect(self):
        self.client.disconnect()


