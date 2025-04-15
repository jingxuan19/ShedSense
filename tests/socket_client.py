import socket
import cv2
import numpy as np
import struct

client_socket = socket.socket()
# client_socket.connect(("10.247.11.189", 8000))
client_socket.connect(("192.168.0.164", 8000))
conn = client_socket.makefile('rb')

count = 0

try:
    while True:
        packed_size = conn.read(4)
        if not packed_size:
            break
        size = struct.unpack('<L', packed_size)[0]
        data = conn.read(size)
        frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        cv2.imshow('Stream', frame)
        key = cv2.waitKey(1)
        if key == 27:  # ESC key to exit
            break
        elif key == ord("s"):
            print(f"SAVING{count}")
            cv2.imwrite(rf"C:\Users\tanji\OneDrive\Cambridge\2\Project\ShedSense\calbration\{count}.png", frame)
            count += 1
finally:
    conn.close()
    client_socket.close()
    cv2.destroyAllWindows()