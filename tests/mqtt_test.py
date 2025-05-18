from mqtt_server import MQTTServerClient

client = MQTTServerClient()

while True:
    client.client.loop()