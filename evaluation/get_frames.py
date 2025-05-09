import cv2
cap = cv2.VideoCapture(r"C:\Users\tanji\Desktop\recordings\ok recordings\2025-05-01_12-37-19.mp4")
video = cv2.VideoWriter("getframes.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 15, (640, 640))
prev_frame_grey = None
number = 0
try:
    while True:
        ret, frame = cap.read()
            
        if not ret:        
            print("End of stream")      
            break

        """
        Grayscale to calculate frame difference
        2 thresholds here, 1 is how much change per pixel to determine if the pixel changed.
        The other is how many pixels much change to determine that we need to start recording
        """
        frame_grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.resize(frame, (640, 640))
        frame_grey = cv2.GaussianBlur(frame_grey, (21, 21), 0)
        writable = frame_grey.copy()

        if prev_frame_grey is None:
            prev_frame_grey = frame_grey         

        diff = cv2.absdiff(prev_frame_grey, frame_grey)
        _, thresh = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)

        thresh = cv2.dilate(thresh, None, iterations=2)
        
        prev_frame_grey = frame_grey

  
        # thresh = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            if cv2.contourArea(c) > 291:
                print("draw")
                cv2.drawContours(writable, contours, -1, (0, 255, 0), 3)
                break 
        
        if number == 1539:
            cv2.imwrite(f"{number}.png", frame_grey)
            number += 1
            cv2.imwrite(f"{number}.png", thresh)
            number += 1
            cv2.imwrite(f"{number}.png", writable)
            number += 1
            break
        else:
            number += 3
            
except KeyboardInterrupt:
    cv2.destroyAllWindows()

video.release()


