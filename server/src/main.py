from mqtt_server import MQTTServerClient
import cv2
import datetime
import numpy as np
import json
import yaml
from lots_initialisation import start_lot_drawing

def on_click(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDBLCLK:
        print(x, y)

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
            # cv2.setMouseCallback("Shedsense", on_click)
            
            
            if is_to_initialise and not is_initialising:
                is_initialising = True
                bike_lot_pts = start_lot_drawing(Server_MQTT_client, frame)
                
                with open(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\ShedSense\server\config\calibration.yaml", "r") as f:
                    config = yaml.safe_load(f)
                H = config["H"]
                
                lot_pts_top_down = []
                for x1, x2, y1, y2, color in bike_lot_pts:
                    point1 = np.array([[[x1, y1]]], dtype=np.float64)
                    point2 = np.array([[[x2, y2]]], dtype=np.float64)
                    
                    point1 = cv2.perspectiveTransform(point1, H)
                    point2 = cv2.perspectiveTransform(point2, H)
                    
                    if color == (0, 0, 255):
                        lot_pts_top_down.append(point1[0,0,:]+point2[0,0,:] + [True])
                    elif color == (0, 255, 0):
                        lot_pts_top_down.append(point1[0,0,:]+point2[0,0,:] + [False])
                        
                Server_MQTT_client.publish("ShedSense/server/initialise_lots", json.dumps(bike_lot_pts))
                
                # lot_drawing_thread.start()

            # if not video:
            #     video = cv2.VideoWriter(fr"server\data\recordings\{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 1, (frame.shape[1], frame.shape[0]))
                
            # video.write(frame)
        # if Server_MQTT_client.annotated_frame is not None:
        #     cv2.imshow("Annotated", Server_MQTT_client.annotated_frame)
        
        # if Server_MQTT_client.filtered_frame is not None:
        #     cv2.imshow("Filtered", Server_MQTT_client.filtered_frame)
            
        if Server_MQTT_client.history_people_locations is not None:
            # print(np.array(Server_MQTT_client.people_locations))
            top_down_img = np.ones((2000, 1000, 3), np.uint8)*255
            for x, y, _ in Server_MQTT_client.current_people_locations:
                cv2.circle(top_down_img, (int(x), int(y)), 20, (255, 65, 137), -1)
            
            for id in Server_MQTT_client.history_people_locations:
                x, y = Server_MQTT_client.history_people_locations[id][-1]
                prev_coords = None
                for x, y in Server_MQTT_client.history_people_locations[id]:
                    if prev_coords is None:
                        prev_coords = [int(x), int(y)]
                        continue
                    cv2.line(top_down_img, prev_coords, [int(x), int(y)], (255, 0, 0), 3) 
                    prev_coords = [int(x), int(y)]
                    
            top_down_img = cv2.resize(top_down_img, (720, 1280))
            top_down_img = cv2.rotate(top_down_img, cv2.ROTATE_90_COUNTERCLOCKWISE)   
            cv2.imshow("Shed abstract view", top_down_img)
            
              
        if cv2.waitKey(1) == ord('q'):
            break
    
    video.release()
    cv2.destroyAllWindows()
            
if __name__ == "__main__":
    main()