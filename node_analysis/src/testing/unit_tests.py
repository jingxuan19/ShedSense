import yaml
import sys
sys.path.insert(1, "/home/shedsense1/ShedSense/node/src")

from mqtt.mqtt_pi import MQTTPiClient

def test_mqtt(payload="HELLO"):
    client = MQTTPiClient()
    
    with open("/home/shedsense1/ShedSense/node/config/mqtt.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    for topic in config["topics"]:
        client.publish(topic, payload)
        print(f"published {payload} to {topic}")
        
test_mqtt()