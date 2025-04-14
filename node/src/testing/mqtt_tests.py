import yaml
import sys
sys.path.insert(1, "/home/shedsense1/ShedSense/node/src")

from mqtt.mqtt_pi import MQTTPiClient

def test_mqtt(payload="HELLO"):
    client = MQTTPiClient()
    
    with open("/home/shedsense1/ShedSense/node/config/mqtt.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    for topic in config["topics"]:
        result = client.publish(topic, payload)
        if result == 0:
            print(f"published {payload} to {topic}")
        else:
            print("failed to send payload")
        
test_mqtt()