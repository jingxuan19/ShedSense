import cv2
from loi.detection.load_lines import load_lines

def draw_line(img_path):
    while True:
        frame = cv2.imread(img_path)
        frame = cv2.resize(frame, (640, 640), 
                interpolation = cv2.INTER_LINEAR)
        
        borders = load_lines("test_1")

        for line in borders:
            # line coords must be in (x,y)
            cv2.line(frame, line.pt1, line.pt2, color=(0, 255, 0), thickness=5)
            
        cv2.imshow("frame", frame)
        
        if cv2.waitKey(1) == ord('q'):
            break