from mqtt_server import MQTTServerClient

Client = MQTTServerClient()

while True:
    ret = Client.publish("shedsense/recording_control", "STOP")
    if ret == 0:
        print("Done!")
        break
