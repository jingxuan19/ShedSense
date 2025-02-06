from mqtt_server import MQTTServerClient

Client = MQTTServerClient()

Client.publish("recording_control", "STOP")
