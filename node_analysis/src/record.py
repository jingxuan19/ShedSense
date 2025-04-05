import datetime
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder

from mqtt.mqtt_pi import MQTTPiClient

def main():
    picam2 = Picamera2()
    video_config = picam2.create_video_configuration()
    picam2.configure(video_config)

    encoder = H264Encoder(10000000)
    
    Client = MQTTPiClient()
    Client.client.subscribe("recording_control")
    
    
    picam2.start_recording(encoder, f"/home/shedsense1/Desktop/recordings/full_recording_{datetime.date.today()}.h264")
    while True:
        if Client.subscribed_msg == "STOP":
            picam2.stop_recording()
            break
    
if __name__ == "__main__":
    main()