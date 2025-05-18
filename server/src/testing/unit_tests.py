import sys
sys.path.insert(1, r"C:\Users\tanji\OneDrive\Cambridge\2\Project\ShedSense\server\src")

from mqtt_server import MQTTServerClient

def test_mqtt():
    client = MQTTServerClient()
    
    while True:
        client.client.loop()
        
        print(client.status)        

test_mqtt()