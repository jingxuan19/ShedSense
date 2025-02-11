from mqtt_server import MQTTServerClient
import cv2
import datetime

def main():
    Server_MQTT_client = MQTTServerClient()
    video = None
    
    while True:
        Server_MQTT_client.client.loop()
        if Server_MQTT_client.frame is not None:
            frame = Server_MQTT_client.frame
            cv2.imshow("Shedsense", frame)
            
            if not video:
                video = cv2.VideoWriter(fr"server\data\recordings\{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 1, (frame.shape[1], frame.shape[0]))
                
            video.write(frame)
            
                
            if cv2.waitKey(1) == ord('q'):
                break
    
    video.release()
    cv2.destroyAllWindows()
            
if __name__ == "__main__":
    main()