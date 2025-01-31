from paho.mqtt import client as mqtt_client
import yaml
import logging
import datetime

class MQTTPiClient:
    def __init__(self, client_id):
        logging.basicConfig(filename=f"/home/shedsense1/ShedSense/rpi/logs/mqtt/{datetime.date.today()}_mqttlogging", level=logging.INFO)        
        
        self.logger = logging.getLogger(__name__)

        
        with open("/home/shedsense1/ShedSense/rpi/config/mqtt.yaml", "r") as f:
            config = yaml.safe_load(f)
            self.broker = config["broker"]
            self.port = config["port"]
                
        self.client = mqtt_client.Client()
        self.client.on_connect = self.on_connect
        
        self.client.connect(self.broker, self.port)
        
    def on_connect(self, client, user_data, flags, reason_code):
        if reason_code == 0:
            self.logger.info(f"Connected to {self.broker} at port {self.port} at {datetime.datetime.now().time()}")
            print("CONNECTED!")
        else:
            self.logger.warning(f"Failed to connect to {self.broker} at port {self.port} with return code {reason_code}")
            print(f"Failed to connect: return code {reason_code}")
                        
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


