import paho.mqtt.client as mqtt

# MQTT Configuration
BROKER = "test.mosquitto.org"  # Replace with your broker's address
PORT = 1883
TOPIC = "bike_shed/frame"

def on_connect(client, userdata, flags, rc):
    print("Connected with result code:", rc)
    # Subscribe to the topic
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    print("Image received from topic:", msg.topic)
    # Save the received image
    with open("received_image.jpg", "wb") as img_file:
        img_file.write(msg.payload)
    print("Image saved as 'received_image.jpg'")

# Create an MQTT client instance
client = mqtt.Client()

# Assign callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
client.connect(BROKER, PORT)

# Keep listening for messages
client.loop_forever()
