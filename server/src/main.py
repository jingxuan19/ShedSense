from mqtt_server import MQTTServerClient
import cv2
import datetime
import numpy as np
import json
import yaml
from lots_initialisation import start_lot_drawing
import time

def on_click(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDBLCLK:
        print(x, y)

def main():
    Server_MQTT_client = MQTTServerClient()
    video = None
    is_to_initialise = True
    is_initialising = False
    video = None    
    with open(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\ShedSense\server\config\bike_lots.yaml", "r") as f:
        config = yaml.safe_load(f)
    bike_lots = config["lots"]
        
    # lot_drawing_thread = threading.Thread(target=start_lot_drawing, args=(Server_MQTT_client, np.copy(Server_MQTT_client.frame)))
    
    while True:
        Server_MQTT_client.client.loop()
        
        if Server_MQTT_client.reset_flag:
            is_to_initialise = True
            is_initialising = False
            Server_MQTT_client.reset_flag = False
                
        if Server_MQTT_client.frame is not None:
            frame = Server_MQTT_client.frame
            # cv2.imshow("Shedsense", frame)
            # cv2.setMouseCallback("Shedsense", on_click)
        
            if is_to_initialise and not is_initialising:
                is_initialising = True
                bike_lot_pts = start_lot_drawing(frame)
                if bike_lot_pts != []:
                    with open(r"C:\Users\tanji\OneDrive\Cambridge\2\Project\ShedSense\server\config\calibration.yaml", "r") as f:
                        config = yaml.safe_load(f)
                    H = np.array(config["H"])
                    
                    lot_pts_top_down = []
                    for x1, x2, y1, y2, color in bike_lot_pts:
                        point1 = np.array([[[x1, y1]]], dtype=np.float64)
                        point2 = np.array([[[x2, y2]]], dtype=np.float64)
                        
                        point1 = cv2.perspectiveTransform(point1, H)
                        point2 = cv2.perspectiveTransform(point2, H)
                        
                        # To send: xyxy
                        if color == (0, 0, 255):
                            lot_pts_top_down.append(point1[0,0,:].tolist()+point2[0,0,:].tolist() + [True])
                        elif color == (0, 255, 0):
                            lot_pts_top_down.append(point1[0,0,:].tolist()+point2[0,0,:].tolist() + [False])

                with open(f"bike_lots.yaml", "w") as f:
                    yaml.dump({"lots": lot_pts_top_down}, f)                        
                Server_MQTT_client.publish("ShedSense/server/initialise_lots", json.dumps(lot_pts_top_down))

                
            # if not video:
            #     video = cv2.VideoWriter(fr"server\data\recordings\{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 1, (frame.shape[1], frame.shape[0]))
                
            # video.write(frame)
        # if Server_MQTT_client.annotated_frame is not None:
        #     cv2.imshow("Annotated", Server_MQTT_client.annotated_frame)
        
        # if Server_MQTT_client.filtered_frame is not None:
        #     cv2.line(Server_MQTT_client.filtered_frame, [320, 0], [320, 640], (255, 0, 0), 3) 
        #     cv2.imshow("Filtered", Server_MQTT_client.filtered_frame)
        
        top_down_img = np.ones((2000, 1000, 3), np.uint8)*255
        mask = top_down_img.copy()
        
        if Server_MQTT_client.lot_status != {}:
            for id, is_occupied in enumerate(Server_MQTT_client.lot_status):
                if is_occupied:
                    color = (0, 0, 255)
                else:
                    color = (0, 255, 0)
                
                x1, y1, x2, y2, _ = bike_lots[id]
                cv2.rectangle(mask, (int(x1), int(y1)), (int(x2), int(y2)), color, -1)
                cv2.rectangle(top_down_img, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
            top_down_img = cv2.addWeighted(top_down_img, 0.5, mask, 0.5, 1.0)
                    
        if Server_MQTT_client.history_people_locations != {}:           
            # print(np.array(Server_MQTT_client.people_locations))
            
            for id in Server_MQTT_client.history_people_locations:
                if Server_MQTT_client.history_people_locations[id]["coords"] == []:
                    continue
                x, y = Server_MQTT_client.history_people_locations[id]["coords"][-1]
                prev_coords = None
                
                pop_until_index = 0
                for index, timestamp in enumerate(Server_MQTT_client.history_people_locations[id]["timestamps"]):
                    if time.time() - timestamp < 30:
                        break
                    pop_until_index += 1
                        
                Server_MQTT_client.history_people_locations[id]["timestamps"] = Server_MQTT_client.history_people_locations[id]["timestamps"][pop_until_index:]
                Server_MQTT_client.history_people_locations[id]["coords"] = Server_MQTT_client.history_people_locations[id]["coords"][pop_until_index:]
                
                for x, y in Server_MQTT_client.history_people_locations[id]["coords"]:
                    if prev_coords is None:
                        prev_coords = [int(x), int(y)]
                        continue
                    cv2.line(top_down_img, prev_coords, [int(x), int(y)], (255, 0, 0), 3) 
                    prev_coords = [int(x), int(y)]
        
        top_down_img = cv2.resize(top_down_img, (720, 1280))
        top_down_img = cv2.rotate(top_down_img, cv2.ROTATE_90_COUNTERCLOCKWISE)   
        
        alert_status = Server_MQTT_client.status.get("alert")
        
        for x, y, id in Server_MQTT_client.current_people_locations:
            # Transform coordinates after rotation
            x, y = int(x*720/1000), int(y*1280/2000)
            x, y = y, 720-1-x
            
            cv2.circle(top_down_img, (x, y), 20, (255, 65, 137), -1)
            cv2.putText(top_down_img, str(int(id)), (int(x)-7, int(y)+8), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (65, 255, 183), 2)     

        # translate_matrix = np.float32([[1,0,100],[0,1,100]])
        # top_down_img = cv2.warpAffine(top_down_img, translate_matrix, (1280,720), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
                 
        if alert_status == "0":
            color = (0, 100, 0)
            cv2.putText(top_down_img, f"Alert {alert_status}: Normal", (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        elif alert_status == "1":
            color = (0, 191, 255)
            cv2.putText(top_down_img, f"Alert {alert_status}: Moderate", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        elif alert_status == "2":
            color = (0, 0, 255)
            cv2.putText(top_down_img, f"Alert {alert_status}: High", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)      
        cv2.imshow("Shed abstract view", top_down_img)

            
        if video is None:
            video = cv2.VideoWriter(f"shed_tracker_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (top_down_img.shape[1], top_down_img.shape[0]))
        video.write(top_down_img)
            
        if cv2.waitKey(1) == ord('q'):
            break
    
    video.release()
    cv2.destroyAllWindows()
            
if __name__ == "__main__":
    main()