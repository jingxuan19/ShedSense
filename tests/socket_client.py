import socket
import cv2
import numpy as np
import struct

client_socket = socket.socket()
client_socket.connect(("10.247.11.189", 8000))
conn = client_socket.makefile('rb')

try:
    while True:
        packed_size = conn.read(4)
        if not packed_size:
            break
        size = struct.unpack('<L', packed_size)[0]
        data = conn.read(size)
        frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        cv2.imshow('Stream', frame)
        if cv2.waitKey(1) == 27:  # ESC key to exit
            break
finally:
    conn.close()
    client_socket.close()
    cv2.destroyAllWindows()