from mqtt_server import MQTTServerClient
import cv2
import datetime
import numpy as np
import threading
from draw_rectangle import start_lot_drawing

def main():
    Server_MQTT_client = MQTTServerClient()
    video = None
    is_to_initialise = True
    is_initialising = False
    
    # lot_drawing_thread = threading.Thread(target=start_lot_drawing, args=(Server_MQTT_client, np.copy(Server_MQTT_client.frame)))
    
    while True:
        Server_MQTT_client.client.loop()
        
        if Server_MQTT_client.reset_flag:
            is_to_initialise = True
            is_initialising = False
            Server_MQTT_client.reset_flag = False
                
        if Server_MQTT_client.frame is not None:
            frame = Server_MQTT_client.frame
            cv2.imshow("Shedsense", frame)
            
            if is_to_initialise and not is_initialising:
                is_initialising = True
                start_lot_drawing(Server_MQTT_client, frame)
                # lot_drawing_thread.start()

            # if not video:
            #     video = cv2.VideoWriter(fr"server\data\recordings\{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 1, (frame.shape[1], frame.shape[0]))
                
            # video.write(frame)
        # if Server_MQTT_client.annotated_frame is not None:
        #     cv2.imshow("Annotated", Server_MQTT_client.annotated_frame)
        
        # if Server_MQTT_client.filtered_frame is not None:
        #     cv2.imshow("Filtered", Server_MQTT_client.filtered_frame)
            
        if Server_MQTT_client.status is not None:
            # print(Server_MQTT_client.status)
            pass
              
        if cv2.waitKey(1) == ord('q'):
            break
    
    video.release()
    cv2.destroyAllWindows()
            
if __name__ == "__main__":
    main()