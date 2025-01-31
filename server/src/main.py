from mqtt_server import MQTTServerClient
import cv2

def main():
    Server_MQTT_client = MQTTServerClient()
    while True:
        Server_MQTT_client.client.loop()
        if Server_MQTT_client.frame is not None:
            cv2.imshow("Shedsense", Server_MQTT_client.frame)
                
            if cv2.waitKey(1) == ord('q'):
                break        
    # Server_MQTT_client.publish("jashdhks", "ahsihsihdih")

if __name__ == "__main__":
    main()