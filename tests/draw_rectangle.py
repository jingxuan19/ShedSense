import numpy as np
import cv2 as cv
import json

def inside_rect_index(x, y, pts):
    for i, [x1,x2,y1,y2, _] in enumerate(pts):
        if (x1 < x) and (x < x2):
            if (y1 < y) and (y < y2):
                return i
    return None

def mouse_callback(event,x,y,flags,param):
    global ix,iy,drawing, mask, mask_uncomitted, color, initial_img, bike_lot_pts, is_occupied

    if event == cv.EVENT_LBUTTONDOWN:
        drawing = True
        ix,iy = x,y
        mask_uncomitted = np.copy(mask)
        
        if is_occupied:
            color = (0, 0, 255)
        else:
            color = (0, 255, 0)

    elif event == cv.EVENT_MOUSEMOVE:
        if drawing:
            cv.rectangle(mask_uncomitted,(ix,iy),(x,y),color,-1)

    elif event == cv.EVENT_LBUTTONUP:
        drawing = False
        cv.rectangle(mask,(ix,iy),(x,y),color,-1)
        bike_lot_pts.append([ix,x,iy,y, color])
        # cv.rectangle(img_copy,(ix,iy),(x,y),(0,255,0),-1)
        
    elif event == cv.EVENT_RBUTTONDOWN:
        drawing = False
    
    elif event == cv.EVENT_LBUTTONDBLCLK:
        index = inside_rect_index(x, y, bike_lot_pts)
        if index:
            bike_lot_pts.pop(index)
            mask = np.zeros_like(initial_img)
            for x1,x2,y1,y2, c in bike_lot_pts:
                cv.rectangle(mask, (x1, y1), (x2, y2), c, -1)
                
def start_lot_drawing(MQTTClient, initial_img):
    print("Starting lot drawing")
    global ix,iy,drawing, mask, mask_uncomitted, color, bike_lot_pts, is_occupied
    
    drawing = False # true if mouse is pressed
    is_occupied = False
    ix,iy = -1,-1
                            
    initial_img = np.zeros((512,512,3), np.uint8)
    mask = np.zeros_like(initial_img)
    bike_lot_pts = []

    cv.namedWindow('Initialise bike lots')
    cv.setMouseCallback('Initialise bike lots', mouse_callback)

    while True:
        out = np.copy(initial_img)
        if drawing:
            out_mask = mask_uncomitted.astype(bool)
            out[out_mask] = cv.addWeighted(initial_img, 0.5, mask_uncomitted, 0.5, 0)[out_mask]
        else:
            out_mask = mask.astype(bool)
            out[out_mask] = cv.addWeighted(initial_img, 0.5, mask, 0.5, 0)[out_mask]
        
        cv.imshow('Initialise bike lots',out)
        
        key = cv.waitKey(1)
        if key == ord("m"):
            is_occupied = not is_occupied
        elif key == ord('q'):
            break
        elif key == ord("s"):
            MQTTClient.publish("ShedSense/server/initialise_lots", json.dumps(bike_lot_pts))
            break
                    
    cv.destroyAllWindows()