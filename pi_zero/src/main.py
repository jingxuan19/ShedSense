"""
Purposes of the pi zero camera:
Given a command by the node, start capturing images then send back to the node.
Given a command by the node (or timeout), stop capturing images and go into idle.
"""
from mqtt.mqtt import MQTTPiClient


def main():
   MQTTClient = MQTTPiClient()
   
   try:
       while True:
           print(MQTTClient.subscribed_msg)
   except KeyboardInterrupt:
       
   
    
if __name__ == "__main__":
    main()